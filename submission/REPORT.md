# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Tứ Tuất Tài Tử
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces: 14; evidence `submission/evidence/cp2-traces-list.png`
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `http://127.0.0.1:8501`

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall: `submission/evidence/cp2-trace-waterfall.png`
- Giải thích một span đáng chú ý: Span retrieval cho biết số document và thời gian lấy ngữ cảnh; generation ghi model, token, cost và prompt version, nên có thể phân biệt chậm ở retrieval hay sinh câu trả lời.

## 4. Prompt versioning

- Prompt name: `day13-chat`; evidence danh sách version `submission/evidence/cp2-prompt-versions.png`
- Version/label baseline: version 1 — `baseline`, `production` (sau rollback); evidence `submission/evidence/cp2-prompt-v1-trace.png`
- Version/label candidate: version 2 — `candidate`; evidence `submission/evidence/cp2-prompt-v2-trace.png`
- Trace ID của mỗi version: baseline `47e6ffa1f76a65390fec6e1eda7e23f0`; candidate `6e33d04168f0a87613d3d317ba15dec9`
- Bằng chứng đổi label hoặc rollback: `submission/evidence/cp2-prompt-production-v2.png` và `submission/evidence/cp2-prompt-rollback.png`

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`; evidence `submission/evidence/cp2-dashboard-validator.png`
- Evidence dashboard: `submission/evidence/cp2-dashboard.png`
- SLO đã chọn và lý do: P95 latency ≤ 3000 ms để giới hạn thời gian chờ; error rate ≤ 2% để bảo vệ độ tin cậy; quality mean ≥ 0,75 để phát hiện suy giảm chất lượng; cost ≤ 2,5 USD để kiểm soát ngân sách.
- Alert rules và runbook: `config/alert_rules.yaml` và `docs/alerts.md`.

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
