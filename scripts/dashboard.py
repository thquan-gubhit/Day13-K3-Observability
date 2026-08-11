from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from statistics import mean
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
CONTRACT_PATH = REPO_ROOT / "config" / "dashboard.yaml"


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_events(window_minutes: int) -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    events: list[dict[str, Any]] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        timestamp = _timestamp(event.get("ts"))
        if timestamp is not None and timestamp >= cutoff:
            events.append(event)
    return events


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def snapshot(events: list[dict[str, Any]], window_minutes: int) -> dict[str, Any]:
    requests = [event for event in events if event.get("event") == "request_received"]
    failures = [event for event in events if event.get("event") == "request_failed"]
    responses = [event for event in events if event.get("event") == "response_sent"]
    latencies = [
        float(event["latency_ms"])
        for event in responses
        if isinstance(event.get("latency_ms"), (int, float))
    ]
    qualities = [
        float(event["quality_score"])
        for event in responses
        if isinstance(event.get("quality_score"), (int, float))
    ]
    breakdown = Counter(str(event.get("error_type") or "unknown") for event in failures)
    return {
        "latency": {
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "p99": percentile(latencies, 99),
        },
        "traffic": {
            "count": len(requests),
            "rate_per_minute": len(requests) / window_minutes,
        },
        "errors": {
            "rate": len(failures) / len(requests) * 100 if requests else 0.0,
            "breakdown": dict(breakdown),
        },
        "cost": sum(float(event.get("cost_usd") or 0) for event in responses),
        "tokens": {
            "in": sum(int(event.get("tokens_in") or 0) for event in responses),
            "out": sum(int(event.get("tokens_out") or 0) for event in responses),
        },
        "quality": mean(qualities) if qualities else 0.0,
    }


def render() -> str:
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))["dashboard"]
    window = int(contract["time_range_minutes"])
    refresh = int(contract["refresh_seconds"])
    values = snapshot(load_events(window), window)
    panels = {panel["id"]: panel for panel in contract["panels"]}

    def threshold(panel_id: str) -> str:
        item = panels[panel_id]["threshold"]
        operator = "≤" if item["operator"] == "lte" else "≥"
        return (
            f'{escape(str(item["aggregation"]))} {operator} {item["value"]} '
            f'{escape(str(panels[panel_id]["unit"]))}'
        )

    error_breakdown = escape(
        json.dumps(values["errors"]["breakdown"], ensure_ascii=False)
    )
    cards = [
        (
            panels["latency"]["title"],
            f'{values["latency"]["p95"]:.0f} ms',
            f'P50 {values["latency"]["p50"]:.0f} · P99 {values["latency"]["p99"]:.0f}',
            threshold("latency"),
        ),
        (
            panels["traffic"]["title"],
            f'{values["traffic"]["rate_per_minute"]:.2f} req/min',
            f'Count: {values["traffic"]["count"]}',
            threshold("traffic"),
        ),
        (
            panels["errors"]["title"],
            f'{values["errors"]["rate"]:.2f}%',
            f"Breakdown: {error_breakdown}",
            threshold("errors"),
        ),
        (
            panels["cost"]["title"],
            f'${values["cost"]:.6f}',
            "Total cost in selected window",
            threshold("cost"),
        ),
        (
            panels["tokens"]["title"],
            f'{values["tokens"]["in"] + values["tokens"]["out"]:,} tokens',
            f'Input {values["tokens"]["in"]:,} · Output {values["tokens"]["out"]:,}',
            threshold("tokens"),
        ),
        (
            panels["quality"]["title"],
            f'{values["quality"]:.3f}',
            "Mean quality score (0–1)",
            threshold("quality"),
        ),
    ]
    card_html = "".join(
        f'<article><h2>{escape(title)}</h2><div class="value">{value}</div>'
        f'<p>{detail}</p><footer>SLO/threshold: {limit}</footer></article>'
        for title, value, detail, limit in cards
    )
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="{refresh}">
<title>{escape(contract["title"])}</title><style>
body{{margin:0;background:#07111f;color:#eef5ff;font:14px Segoe UI,sans-serif}}
main{{max-width:1200px;margin:auto;padding:28px}}header{{display:flex;justify-content:space-between;align-items:end;margin-bottom:18px}}
h1{{margin:0 0 5px}}.meta,p{{color:#9bb0c9}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
article{{background:#102036;border:1px solid #29405b;border-radius:14px;padding:18px;min-height:180px}}
h2{{font-size:16px;margin:0}}.value{{font-size:30px;font-weight:700;margin:24px 0 8px}}
footer{{border-top:1px solid #29405b;padding-top:12px;color:#ffd27a}}
@media(max-width:850px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><main>
<header><div><h1>{escape(contract["title"])}</h1><div class="meta">Source: data/logs.jsonl</div></div>
<div class="meta">Time range: last {window} minutes<br>Refresh: {refresh} seconds</div></header>
<section class="grid">{card_html}</section></main></body></html>'''


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        content = render().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Runtime dashboard for Checkpoint 2")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    print(f"Dashboard: http://{args.host}:{args.port}")
    ThreadingHTTPServer((args.host, args.port), DashboardHandler).serve_forever()


if __name__ == "__main__":
    main()
