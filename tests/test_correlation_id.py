from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app

CORRELATION_ID_RE = re.compile(r"^req-[0-9a-f]{8}$")
ENRICHMENT_FIELDS = {"user_id_hash", "session_id", "feature", "model", "env"}


def _payload(**overrides) -> dict:
    body = {
        "user_id": "student-01",
        "session_id": "session-01",
        "feature": "qa",
        "message": "What should be logged?",
    }
    body.update(overrides)
    return body


def _read_events(log_path: Path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def test_generated_correlation_id_matches_contract(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    with TestClient(app) as client:
        response = client.post("/chat", json=_payload())

    assert response.status_code == 200
    correlation_id = response.headers["x-request-id"]
    assert CORRELATION_ID_RE.match(correlation_id)
    assert response.json()["correlation_id"] == correlation_id
    assert float(response.headers["x-response-time-ms"]) >= 0


def test_client_supplied_correlation_id_is_reused(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat", json=_payload(), headers={"x-request-id": "req-fromclient"}
        )

    assert response.headers["x-request-id"] == "req-fromclient"
    api_events = [e for e in _read_events(log_path) if e.get("service") == "api"]
    assert api_events
    assert all(event["correlation_id"] == "req-fromclient" for event in api_events)


def test_every_api_log_carries_enrichment_metadata(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        client.post("/chat", json=_payload())

    api_events = [e for e in _read_events(log_path) if e.get("service") == "api"]
    assert {e["event"] for e in api_events} >= {"request_received", "response_sent"}
    for event in api_events:
        assert ENRICHMENT_FIELDS.issubset(event.keys()), event
        # user_id thô không bao giờ được ghi xuống log.
        assert "student-01" not in json.dumps(event, ensure_ascii=False)


def test_context_is_not_leaked_between_requests(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        first = client.post("/chat", json=_payload(session_id="session-A", feature="qa"))
        second = client.post(
            "/chat", json=_payload(session_id="session-B", feature="summary")
        )

    assert first.headers["x-request-id"] != second.headers["x-request-id"]

    by_correlation_id: dict[str, set[str]] = {}
    for event in _read_events(log_path):
        if event.get("service") != "api":
            continue
        by_correlation_id.setdefault(event["correlation_id"], set()).add(event["session_id"])

    # Nếu quên clear_contextvars(), request thứ hai sẽ kế thừa session của request đầu.
    assert by_correlation_id[first.headers["x-request-id"]] == {"session-A"}
    assert by_correlation_id[second.headers["x-request-id"]] == {"session-B"}


def test_pii_is_scrubbed_outside_payload(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        client.post("/chat", json=_payload(session_id="student@vinuni.edu.vn"))

    raw = log_path.read_text(encoding="utf-8")
    assert "student@vinuni.edu.vn" not in raw
    assert "REDACTED_EMAIL" in raw


def test_failed_request_still_returns_correlation_id(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    from app import incidents

    incidents.enable("tool_fail")
    try:
        with TestClient(app) as client:
            response = client.post("/chat", json=_payload())
    finally:
        incidents.disable("tool_fail")

    assert response.status_code == 500
    correlation_id = response.headers["x-request-id"]
    assert CORRELATION_ID_RE.match(correlation_id)

    failures = [e for e in _read_events(log_path) if e.get("event") == "request_failed"]
    assert failures
    # Log lỗi phải tra cứu được bằng đúng correlation ID client nhận về.
    assert failures[-1]["correlation_id"] == correlation_id
    assert ENRICHMENT_FIELDS.issubset(failures[-1].keys())
