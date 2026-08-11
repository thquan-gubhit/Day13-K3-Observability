from __future__ import annotations

import argparse
import html
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(0, math.ceil((p / 100) * len(ordered)) - 1)
    return ordered[rank]


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_events(path: Path, minutes: int) -> list[dict]:
    if not path.exists():
        return []
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            events.append(item)
    timestamps = [ts for event in events if (ts := parse_timestamp(event.get("ts")))]
    reference = max(timestamps, default=datetime.now(timezone.utc))
    cutoff = reference - timedelta(minutes=minutes)
    return [
        event
        for event in events
        if (ts := parse_timestamp(event.get("ts"))) is None or ts >= cutoff
    ]


def summarize(events: list[dict], minutes: int) -> dict:
    received = [event for event in events if event.get("event") == "request_received"]
    responses = [event for event in events if event.get("event") == "response_sent"]
    failures = [event for event in events if event.get("event") == "request_failed"]
    latencies = [float(event["latency_ms"]) for event in responses if isinstance(event.get("latency_ms"), (int, float))]
    costs = [float(event["cost_usd"]) for event in responses if isinstance(event.get("cost_usd"), (int, float))]
    qualities = [float(event["quality_score"]) for event in responses if isinstance(event.get("quality_score"), (int, float))]
    errors = Counter(str(event.get("error_type", "unknown")) for event in failures)
    traffic = len(received)
    received_timestamps = [
        ts for event in received if (ts := parse_timestamp(event.get("ts")))
    ]
    if len(received_timestamps) > 1:
        active_minutes = max(
            1.0,
            (max(received_timestamps) - min(received_timestamps)).total_seconds() / 60,
        )
    else:
        active_minutes = 1.0
    return {
        "p50": percentile(latencies, 50),
        "p95": percentile(latencies, 95),
        "p99": percentile(latencies, 99),
        "traffic": traffic,
        "rate": traffic / min(max(minutes, 1), active_minutes),
        "error_rate": (len(failures) / traffic * 100) if traffic else 0.0,
        "errors": errors,
        "cost": sum(costs),
        "tokens_in": sum(int(event.get("tokens_in", 0)) for event in responses),
        "tokens_out": sum(int(event.get("tokens_out", 0)) for event in responses),
        "quality": mean(qualities) if qualities else 0.0,
        "responses": len(responses),
    }


def status(value: float, operator: str, threshold: float) -> str:
    return "good" if (value <= threshold if operator == "lte" else value >= threshold) else "bad"


def card(title: str, value: str, detail: str, state: str) -> str:
    return f"""<section class="card {state}"><h2>{html.escape(title)}</h2><div class="value">{html.escape(value)}</div><p>{html.escape(detail)}</p></section>"""


def render_dashboard(summary: dict, config: dict, generated_at: datetime) -> str:
    dashboard = config["dashboard"]
    thresholds = {panel["id"]: panel["threshold"] for panel in dashboard["panels"]}
    latency_t = thresholds["latency"]
    traffic_t = thresholds["traffic"]
    errors_t = thresholds["errors"]
    cost_t = thresholds["cost"]
    tokens_t = thresholds["tokens"]
    quality_t = thresholds["quality"]
    error_breakdown = ", ".join(f"{key}: {value}" for key, value in summary["errors"].items()) or "Không có lỗi"
    cards = [
        card("Latency percentiles", f"P95 {summary['p95']:.0f} ms", f"P50 {summary['p50']:.0f} · P99 {summary['p99']:.0f} · SLO P95 ≤ {latency_t['value']} ms", status(summary["p95"], latency_t["operator"], latency_t["value"])),
        card("Request traffic", f"{summary['traffic']} requests", f"{summary['rate']:.2f} requests/min · threshold ≥ {traffic_t['value']}", status(summary["rate"], traffic_t["operator"], traffic_t["value"])),
        card("Error rate and breakdown", f"{summary['error_rate']:.2f}%", f"{error_breakdown} · SLO ≤ {errors_t['value']}%", status(summary["error_rate"], errors_t["operator"], errors_t["value"])),
        card("Cost over time", f"${summary['cost']:.4f}", f"Tổng cửa sổ · ngân sách ≤ ${cost_t['value']}", status(summary["cost"], cost_t["operator"], cost_t["value"])),
        card("Input and output tokens", f"{summary['tokens_in']:,} / {summary['tokens_out']:,}", f"Input / output tokens · threshold mỗi tổng ≤ {tokens_t['value']:,}", status(max(summary["tokens_in"], summary["tokens_out"]), tokens_t["operator"], tokens_t["value"])),
        card("Quality proxy", f"{summary['quality']:.2f}", f"Mean score 0–1 · SLO ≥ {quality_t['value']}", status(summary["quality"], quality_t["operator"], quality_t["value"])),
    ]
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta http-equiv="refresh" content="{dashboard['refresh_seconds']}">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(dashboard['title'])}</title>
<style>
:root{{--bg:#09111f;--panel:#111d31;--text:#eef5ff;--muted:#9fb0ca;--good:#43d19e;--bad:#ff6b7a;--line:#243652}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top,#183153 0,#09111f 48%);color:var(--text);font-family:Inter,Segoe UI,sans-serif;min-height:100vh}}main{{max-width:1180px;margin:auto;padding:38px 28px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:end;border-bottom:1px solid var(--line);padding-bottom:20px}}h1{{font-size:30px;margin:0 0 8px}}.sub,p{{color:var(--muted)}}.meta{{text-align:right;font-size:14px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:24px}}.card{{background:linear-gradient(145deg,rgba(23,39,65,.96),rgba(12,23,40,.96));padding:22px;border:1px solid var(--line);border-radius:16px;min-height:180px;box-shadow:0 16px 35px rgba(0,0,0,.22)}}.card.good{{border-top:4px solid var(--good)}}.card.bad{{border-top:4px solid var(--bad)}}h2{{font-size:16px;letter-spacing:.02em;margin:0;color:#cbd8eb}}.value{{font-size:34px;font-weight:750;margin:28px 0 12px}}.card p{{font-size:14px;line-height:1.5;margin:0}}footer{{margin-top:22px;color:var(--muted);font-size:13px}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}header{{display:block}}.meta{{text-align:left;margin-top:12px}}}}
</style></head><body><main><header><div><h1>{html.escape(dashboard['title'])}</h1><div class="sub">Nguồn chuẩn: data/logs.jsonl</div></div><div class="meta">Time range: {dashboard['time_range_minutes']} phút<br>Refresh: {dashboard['refresh_seconds']} giây<br>Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</div></header><div class="grid">{''.join(cards)}</div><footer>{summary['responses']} response_sent events trong cửa sổ · Đường viền xanh: đạt threshold · đỏ: vi phạm threshold</footer></main></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Tạo dashboard CP2 từ structured logs")
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "config" / "dashboard.yaml")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "submission" / "evidence" / "cp2-dashboard.html")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    minutes = int(config["dashboard"]["time_range_minutes"])
    summary = summarize(load_events(args.logs, minutes), minutes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_dashboard(summary, config, datetime.now(timezone.utc)), encoding="utf-8")
    print(f"Dashboard: {args.output}")
    print(json.dumps({**summary, "errors": dict(summary["errors"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
