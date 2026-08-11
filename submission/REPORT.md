# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
  - Baseline (CP0, trước khi sửa code): **30/100** — xem [evidence](evidence/cp0-baseline-validate_logs.txt).
    - FAILED: required fields (thiếu `correlation_id` trên 20 log `service=api`), correlation ID propagation (0 unique ID), log enrichment (thiếu `user_id_hash`/`session_id`/`feature`/`model`).
    - PASSED: PII scrubbing — chỉ vì `summarize_text()` đã che sẵn `payload.message_preview`; `scrub_event` chưa được bật nên các trường khác vẫn chưa an toàn.
  - Sau CP1: **100/100** — xem [evidence](evidence/cp1-validate_logs.txt) (4/4 mục PASSED, 15 unique correlation ID, 0 PII leak).
- Tổng số traces: _(phần Tracing & Prompt Version)_
- Số PII leak còn lại: **0** — kiểm tra bằng `validate_logs.py` và kiểm tra thủ công ngoài script ([evidence](evidence/cp1-pii-manual-check.txt): `@`, `4111`, `0987654321`, `duong Lang`, `student-01` đều 0 match).
- Link/đường dẫn dashboard: _(phần Dashboard, SLO & Alert)_

## 3. Logging và tracing

- Evidence correlation ID: [cp1-correlation-id-and-pii.txt](evidence/cp1-correlation-id-and-pii.txt) mục 1–5, log thô tại [cp1-log-sample.jsonl](evidence/cp1-log-sample.jsonl).
  - Server sinh ID theo format `req-<8hex>`, trả về cả trong header `x-request-id` lẫn body; thêm `x-response-time-ms`.
  - ID do client gửi lên được tái sử dụng (`req-fromclient`) để truy vết xuyên service.
  - Cả `request_received` và `response_sent`/`request_failed` của cùng một request dùng chung một ID → tra được toàn bộ hành trình bằng một lần lọc.
  - Request lỗi 500 (incident `tool_fail`) vẫn trả `x-request-id`: `chat()` chuyển lỗi thành `HTTPException` nên response vẫn đi ngược qua middleware và được gắn header.
- Evidence PII redaction: [cp1-correlation-id-and-pii.txt](evidence/cp1-correlation-id-and-pii.txt) mục 6 và [cp1-pii-manual-check.txt](evidence/cp1-pii-manual-check.txt).
  - `scrub_event` được đăng ký sau `TimeStamper` và trước `JsonlFileProcessor` + `JSONRenderer` → PII bị che trước khi ghi file và trước khi in console.
  - Thêm PII pattern cho hộ chiếu và địa chỉ VN (che cả cụm sau từ khoá, có cả biến thể không dấu).
  - `user_id` không bao giờ vào log — chỉ ghi `user_id_hash` (SHA-256 rút gọn 12 ký tự).
- Evidence trace waterfall: _(phần Tracing & Prompt Version)_
- Giải thích một span đáng chú ý: _(phần Tracing & Prompt Version)_

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

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
|---|---|---|---|
| Nguyễn Quang Hưng (Thành viên A — Logging & Middleware) | CP0 setup/baseline; CP1: hoàn thiện 7 TODO — 4 TODO `CorrelationIdMiddleware`, 1 TODO enrich log metadata trong `/chat`, 1 TODO đăng ký `scrub_event`, 1 TODO thêm PII pattern (hộ chiếu, địa chỉ VN) | nhánh `hung`: commit CP0 `chore(cp0)`, commit CP1 `feat(cp1)` | `clear_contextvars()` là bắt buộc vì structlog dùng `contextvars` gắn theo task; worker được tái sử dụng nên nếu không xoá, request sau sẽ kế thừa `session_id`/`user_id_hash` của request trước — log trông vẫn hợp lệ nhưng gán sai người dùng, loại lỗi rất khó phát hiện khi đọc log. |
