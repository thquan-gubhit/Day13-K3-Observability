# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Tứ Tuất Tài Tử
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (baseline CP2, 20 request sau kiểm tra incident)
- Tổng số traces: 12 traces CP2 đã xác minh qua Langfuse API (10 load-test + 2 prompt-versioning)
- Số PII leak còn lại: 0 theo `scripts/validate_logs.py`
- Link/đường dẫn dashboard: `submission/evidence/cp2-dashboard-baseline.html` và `submission/evidence/cp2-dashboard-rag-slow.html`

## 3. Logging và tracing

- Evidence correlation ID: `req-28acc3b9` (baseline v1), `req-002491a4` (candidate v2)
- Evidence PII redaction: trace input đã hiển thị `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`; validator báo 0 leak.
- Evidence trace waterfall: Trace `47e6ffa1f76a65390fec6e1eda7e23f0` có root `chat-response` và hai observation con `retrieve-context`, `generate-response`.
- Giải thích một span đáng chú ý: `retrieve-context` có type `RETRIEVER`, input query đã redact và output là documents; `generate-response` có type `GENERATION`, model, input/output token, cost và prompt link. Với practice incident `rag_slow`, P95 nội bộ tăng từ 151 ms lên 2652 ms.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: Version 1 — `baseline`, `production`
- Version/label candidate: Version 2 — `candidate`
- Trace ID của mỗi version: baseline v1 `47e6ffa1f76a65390fec6e1eda7e23f0`; candidate v2 `6e33d04168f0a87613d3d317ba15dec9`
- Bằng chứng đổi label hoặc rollback: Đã promote `production` sang v2 (`candidate`, `production`, `latest`) và rollback về v1 (`baseline`, `production`). Trạng thái cuối: `production=v1`.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: `submission/evidence/cp2-dashboard-baseline.html`; `submission/evidence/cp2-dashboard-rag-slow.html`; chi tiết tại `submission/evidence/CP2.md`.
- SLO đã chọn và lý do: P95 ≤ 3000 ms, error rate ≤ 2%, daily cost ≤ 2,5 USD và quality trung bình ≥ 0,75. Các ngưỡng bao phủ độ trễ, độ tin cậy, ngân sách và chất lượng cảm nhận.
- Alert rules và runbook: Ba alert symptom-based trong `config/alert_rules.yaml`; quy trình kiểm tra, mitigation và owner trong `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
| ---------- | --------- | --------- | ----------- |
|            |           |           |             |
