# CP3 investigation evidence

Run date: 2026-08-11 (timestamps in log are UTC). Challenge: `day13-k3-observability-v1` / `rag_slow` / feature `refund`.

## Commands and results

- Tests: `python -m pytest -q` → `22 passed`.
- Dashboard contract: `python scripts/validate_dashboard.py` → `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Log validation after load: 33 records, 17 correlation IDs, 0 missing required/enrichment fields, 0 PII leak, estimated score 100/100.
- Baseline (10 responses): P50 150 ms, P95 152 ms, P99 152 ms.
- Challenge (5 responses): P50 2651 ms, P95 2656 ms, P99 2656 ms; all five responses exceeded the 2000 ms challenge threshold.

## Verifiable log anchors

- Incident enabled: `2026-08-11T10:29:35.985571Z`, correlation `req-5acb61b7`.
- Slow request: `req-23015ce9`, session `k3-challenge-s03`, feature `refund`, `latency_ms=2656`.
- Other affected requests: `req-fcf208c4`, `req-a72a8fc5`, `req-55897ccf`, `req-810cb75b`.
- Incident disabled: `2026-08-11T10:29:50.670252Z`, correlation `req-eacbf196`.

Full records are retained in `data/logs.jsonl`. Runtime health reported `tracing_enabled:false`, so this run produced no defensible CP3 trace ID; rerun with Langfuse configured before final submission.
