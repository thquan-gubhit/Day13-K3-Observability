# Dashboard Spec — Day 13 AI Observability

## Mục tiêu và phạm vi

Dashboard phục vụ ba câu hỏi vận hành: hệ thống có đang vi phạm SLO, phạm vi ảnh hưởng là gì, và cần mở trace/log nào để điều tra. Nguồn chuẩn duy nhất cho số liệu là `data/logs.jsonl`; trace chi tiết được mở ở Langfuse bằng correlation context tương ứng.

- Audience: on-call engineer, QA và incident analyst.
- Time range mặc định: 60 phút.
- Auto refresh: 30 giây.
- Bộ lọc chung nên có: `feature`, `model`, `env`, `session_id`, `correlation_id`.
- Bố cục: 6 panel trên một màn hình, latency/error ở hàng đầu vì đây là tín hiệu phát hiện sự cố.

## Định nghĩa panel

| # | Panel | Event/field | Phép tính và hiển thị | Đơn vị | SLO/threshold | Drill-down |
|---:|---|---|---|---|---|---|
| 1 | Latency percentiles | `response_sent.latency_ms` | P50/P95/P99 trong cửa sổ; ưu tiên time series và ba stat | ms | P95 ≤ 3000 ms | Lọc request trên P95, mở theo `correlation_id` |
| 2 | Request traffic | `request_received` | Count và rate/phút; time series 1 phút | requests/min | ≥ 1 request/phút khi chạy test | Breakdown theo `feature` |
| 3 | Error rate and breakdown | `request_received`, `request_failed.error_type` | failures / requests × 100 và count theo `error_type` | % | ≤ 2% | Mở log `request_failed` |
| 4 | Cost over time | `response_sent.cost_usd` | Sum theo phút và tổng cửa sổ | USD | Tổng ≤ 2.5 USD | Breakdown theo model/feature |
| 5 | Input and output tokens | `response_sent.tokens_in`, `tokens_out` | Hai tổng riêng, không gộp mất tỷ lệ input/output | tokens | Tổng ≤ 50,000 | Breakdown theo model/feature |
| 6 | Quality proxy | `response_sent.quality_score` | Mean; time series và stat | score 0–1 | Mean ≥ 0.75 | Lọc request dưới 0.75 |

## Quy tắc trực quan và trạng thái

- Hiển thị rõ time range, thời điểm refresh gần nhất, source, đơn vị và đường threshold.
- Trạng thái xanh khi đạt, vàng khi còn cách threshold ≤ 10%, đỏ khi vi phạm.
- Không thay số 0 cho dữ liệu thiếu; hiển thị `No data` để tránh kết luận sai.
- P95/P99 dùng nearest-rank như `scripts/dashboard.py`; cùng một cửa sổ phải dùng cùng tập `response_sent`.
- Error rate dùng mẫu số `request_received`, không dùng `response_sent`, để request thất bại vẫn được tính.

## Luồng điều tra Metrics → Traces → Logs

1. Từ panel latency xác nhận P95 vượt threshold và lọc `feature` bất thường.
2. Chọn request chậm, lấy `correlation_id`; mở trace Langfuse và xác định span retrieval/generation chiếm thời gian.
3. Tìm tất cả log cùng `correlation_id`, đối chiếu `request_received`, `response_sent` hoặc `request_failed`.
4. So sánh error, cost, token và quality để phân biệt sự cố latency đơn thuần với lỗi/cost/quality regression.
5. Ghi lại trace ID, correlation ID, timestamp UTC, metric trước/sau và hành động khắc phục trong incident report.

## Acceptance test

1. `python scripts/validate_dashboard.py` trả về `HỢP LỆ: 6/6 panel`.
2. Baseline load test tạo dữ liệu cho đủ sáu panel.
3. Bật `rag_slow`, chạy cùng input/concurrency: P95 latency phải tăng và các panel không liên quan không được báo sai sự cố.
4. Screenshot phải thấy đủ tên panel, time range 60 phút, refresh 30 giây, đơn vị và threshold.
5. Có ít nhất một drill-down nối được metric với trace và log; nếu tracing tắt phải hiển thị/ghi nhận rõ evidence gap.
