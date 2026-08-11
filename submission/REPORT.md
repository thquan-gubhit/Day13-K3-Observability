# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Tứ Tuất Tài Tử
- Repository URL: https://github.com/thquan-gubhit/Day13-K3-Observability
- Commit SHA tại thời điểm QA: `182094cbbe87d5d94ef0c249b80b712d6b8e32fb` (cần thay bằng SHA commit nộp cuối)
- Thành viên D: **Lê Minh Khiêm** — QA & Incident Analyst

## 2. Kết quả kỹ thuật

- Test suite: `22 passed`, 2 cảnh báo deprecation của FastAPI `on_event`.
- `validate_logs.py`: **100/100**, 33 records, 17 correlation IDs, 0 missing field, 0 PII leak.
- Tổng số traces CP2: 14; evidence `submission/evidence/cp2-traces-list.png`.
- Dashboard validator: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Dashboard runtime: `http://127.0.0.1:8501` khi chạy `python scripts/dashboard.py`.
- Dashboard spec: `docs/dashboard-spec.md`.

## 3. Logging và tracing

- Correlation ID được tạo/kiểm tra ở middleware và xuất hiện xuyên suốt cặp event `request_received` → `response_sent`. Ví dụ CP3: `req-23015ce9`.
- PII redaction đã được kiểm tra tự động: email, số điện thoại Việt Nam và thẻ thử nghiệm trong baseline đều được thay bằng marker `[REDACTED_*]`; validator ghi nhận 0 leak.
- Evidence trace waterfall CP2: `submission/evidence/cp2-trace-waterfall.png`.
- Span đáng chú ý: retrieval cho biết số document và thời gian lấy ngữ cảnh; generation ghi model, token, cost và prompt version. Với CP3, tracing trên runtime QA đang tắt nên không có trace ID mới để dẫn — không được suy diễn trace từ correlation ID.

## 4. Prompt versioning

- Prompt name: `day13-chat`; evidence `submission/evidence/cp2-prompt-versions.png`.
- Baseline: version 1 — `baseline`, `production` sau rollback; trace `47e6ffa1f76a65390fec6e1eda7e23f0`.
- Candidate: version 2 — `candidate`; trace `6e33d04168f0a87613d3d317ba15dec9`.
- Evidence đổi label/rollback: `submission/evidence/cp2-prompt-production-v2.png`, `submission/evidence/cp2-prompt-rollback.png`.

## 5. Dashboard, SLO và alerts

Dashboard có đúng sáu panel: latency P50/P95/P99, traffic, error rate/breakdown, cost, input/output tokens và quality proxy. Cửa sổ mặc định 60 phút, refresh 30 giây; định nghĩa phép tính, đơn vị, drill-down và acceptance test nằm trong `docs/dashboard-spec.md`.

| SLI | Mục tiêu | Lý do |
|---|---:|---|
| P95 latency | ≤ 3000 ms | Giới hạn thời gian chờ phía ứng dụng |
| Error rate | ≤ 2% | Bảo vệ độ tin cậy |
| Quality mean | ≥ 0.75 | Phát hiện suy giảm chất lượng |
| Cost/window | ≤ 2.5 USD | Kiểm soát ngân sách |

Alert rules và runbook: `config/alert_rules.yaml`, `docs/alerts.md`. Evidence CP2: `submission/evidence/cp2-dashboard-validator.png`, `submission/evidence/cp2-dashboard.png`.

## 6. Điều tra challenge CP3

- Challenge ID: `day13-k3-observability-v1`; incident `rag_slow`; feature ảnh hưởng `refund`; threshold challenge 2000 ms.
- Cách chạy: baseline `python scripts/load_test.py --concurrency 5`; sau đó `python scripts/inject_incident.py`, `python scripts/load_test.py --challenge --concurrency 5`, và tắt bằng `python scripts/inject_incident.py --disable`.
- Metrics baseline (10 response): P50 150 ms, P95/P99 152 ms, cost 0.022155 USD, 330/1411 input/output tokens, quality mean 0.880.
- Metrics incident (5 response): P50 2651 ms, P95/P99 2656 ms, min–max 2650–2656 ms, cost 0.008661 USD, 162/545 tokens, quality mean 0.860, error rate 0%. P95 tăng 2504 ms (khoảng 17.5×) và cả 5 request vượt threshold 2000 ms; cost, error và quality không cho thấy regression tương ứng.
- Correlation IDs: `req-fcf208c4`, `req-a72a8fc5`, `req-23015ce9`, `req-55897ccf`, `req-810cb75b`.
- Log chứng minh: `incident_enabled` lúc `2026-08-11T10:29:35.985571Z`; `req-23015ce9` có `request_received` lúc `10:29:41.971619Z` và `response_sent.latency_ms=2656` lúc `10:29:44.634147Z`; `incident_disabled` lúc `10:29:50.670252Z`.
- Trace ID CP3: **chưa có**. `/health` trả `tracing_enabled:false`; đây là evidence gap cần đóng trước khi nộp để chứng minh trọn luồng Metrics → Traces → Logs.
- Root cause: scenario `rag_slow` thêm `time.sleep(2.5)` đồng bộ vào retrieval. Vì endpoint `async` gọi luồng đồng bộ này trực tiếp, nó còn chặn event loop; do đó client quan sát 10.6–13.3 giây khi chạy 5 request đồng thời dù mỗi log ứng dụng ghi khoảng 2.65 giây.
- Fix action: bỏ delay injection sau khi điều tra; trong production chuyển retrieval blocking sang async I/O hoặc `run_in_threadpool`/worker, đặt timeout và cancellation budget cho retrieval.
- Preventive measure: thêm span riêng cho retrieval, alert P95 theo `feature`, load test concurrency trong CI, timeout/circuit breaker, và test hồi quy bảo đảm event loop không bị block.

Evidence máy đọc được: `submission/evidence/cp3-investigation.md` và `data/logs.jsonl`.

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Lê Minh Khiêm | Chạy baseline/challenge load test; xác minh test, log và dashboard contract; thiết kế dashboard spec; điều tra CP3; viết report | Commit [`930813e`](https://github.com/thquan-gubhit/Day13-K3-Observability/commit/930813ea1e5c592e68ae54ed54dba6b083593625), nhánh `khiem-cp3` | Percentile phải gắn với cùng cửa sổ dữ liệu; correlation ID nối log, còn trace ID cần backend tracing thực sự; synchronous blocking có thể làm tail latency phía client cao hơn latency nội bộ từng request. |

## 8. Việc còn lại trước khi nộp

1. Bật/cấu hình Langfuse, chạy lại CP3 và điền trace ID retrieval chậm.
2. Chạy dashboard runtime và chụp screenshot CP3 có time range, unit, threshold.
3. Cập nhật SHA merge/nộp cuối sau khi pull request được nhập vào nhánh chính.
