from __future__ import annotations

from scripts.generate_dashboard import percentile, summarize


def test_percentile_uses_nearest_rank() -> None:
    assert percentile([10, 20, 30, 40], 50) == 20
    assert percentile([10, 20, 30, 40], 95) == 40


def test_dashboard_summary_calculates_six_panel_values() -> None:
    events = [
        {"event": "request_received"},
        {"event": "request_received"},
        {"event": "response_sent", "latency_ms": 100, "cost_usd": 0.1, "tokens_in": 10, "tokens_out": 20, "quality_score": 0.8},
        {"event": "request_failed", "error_type": "TimeoutError"},
    ]

    result = summarize(events, minutes=60)

    assert result["traffic"] == 2
    assert result["p95"] == 100
    assert result["error_rate"] == 50
    assert result["errors"]["TimeoutError"] == 1
    assert result["cost"] == 0.1
    assert result["tokens_in"] == 10
    assert result["tokens_out"] == 20
    assert result["quality"] == 0.8
