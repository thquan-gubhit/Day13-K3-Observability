# Evidence CP2 — Metrics, Traces, Dashboard & Alerts

## Kết quả tự kiểm

```text
pytest: 26 passed
validate_dashboard.py: HỢP LỆ: 6/6 panel có trong dashboard contract.
validate_logs.py: 100/100
PII leaks: 0
```

## Dashboard runtime

- Baseline: `cp2-dashboard-baseline.html`
- Practice incident RAG chậm: `cp2-dashboard-rag-slow.html`
- Nguồn dữ liệu: `data/logs.jsonl`
- Time range: 60 phút
- Refresh: 30 giây

Kết quả trước/sau practice incident:

| Chỉ số | Baseline | `rag_slow` |
|---|---:|---:|
| P50 latency | 151 ms | 151 ms |
| P95 latency | 151 ms | 2652 ms |
| P99 latency | 151 ms | 2652 ms |
| Traffic | 10 | 20 |
| Error rate | 0% | 0% |
| Total cost | 0,021930 USD | 0,044385 USD |
| Quality mean | 0,88 | 0,88 |

P95 tăng khoảng 17,6 lần khi bật `rag_slow`, đúng hướng kỳ vọng. Incident đã được tắt sau phép thử.

## Tracing và prompt versioning

Langfuse đã được kết nối và xác minh bằng Observations API. Có 12 traces CP2: 10 traces từ load test và hai traces dùng cùng input để kiểm tra prompt versioning.

Code đã instrument ba tầng waterfall:

```text
chat-response (CHAIN)
├── retrieve-context (RETRIEVER)
└── generate-response (GENERATION)
```

Mỗi trace có user hash, session, tags, environment, correlation ID và input/output đã redact. Generation có model `claude-sonnet-4-5`, usage token, cost và managed prompt link.

### Prompt versioning

Hai trace sử dụng cùng input `Explain the refund window and required evidence.`:

| Label | Prompt version | Trace ID | Correlation ID | Prompt link |
|---|---:|---|---|---|
| `baseline` | 1 | `47e6ffa1f76a65390fec6e1eda7e23f0` | `req-28acc3b9` | `day13-chat` v1 |
| `candidate` | 2 | `6e33d04168f0a87613d3d317ba15dec9` | `req-002491a4` | `day13-chat` v2 |

- Baseline trace: https://cloud.langfuse.com/project/cmso5snz004iuad0iqpqh9zab/traces/47e6ffa1f76a65390fec6e1eda7e23f0
- Candidate trace: https://cloud.langfuse.com/project/cmso5snz004iuad0iqpqh9zab/traces/6e33d04168f0a87613d3d317ba15dec9

### Promote và rollback

1. Trạng thái đầu: `production` trỏ tới v1 (`baseline`, `production`).
2. Promote: `production` trỏ tới v2 (`candidate`, `production`, `latest`).
3. Rollback: `production` trở về v1 (`baseline`, `production`).
4. Trạng thái cuối đã xác minh qua SDK: `production=v1`.

Theo yêu cầu hiện tại, evidence CP2 dùng Trace ID, URL trực tiếp và kết quả xác minh Langfuse API; không thu ảnh UI.
