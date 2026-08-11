# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: High user-facing latency
- Severity: warning
- SLI/SLO liên quan: `latency_p95_ms <= 3000`
- Điều kiện và thời gian duy trì: `latency_p95_ms > 3000` trong 5 phút liên tục.
- Ảnh hưởng tới người dùng: Phản hồi chat chậm, người dùng có thể bỏ phiên.
- Ba bước kiểm tra đầu tiên:
  1. So sánh P50/P95/P99 với traffic trong cùng cửa sổ.
  2. Mở trace chậm và xác định span chiếm nhiều thời gian nhất.
  3. Dùng correlation ID của trace để tìm log liên quan.
- Mitigation tạm thời: Tắt incident practice nếu đang bật và giảm concurrency trong khi điều tra.
- Owner: `observability-oncall`

## Alert 2

- Tên: Elevated request error rate
- Severity: critical
- SLI/SLO liên quan: `error_rate_pct <= 2`
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` trong 5 phút liên tục.
- Ảnh hưởng tới người dùng: Một phần request không trả về câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra error breakdown theo `error_type`.
  2. Mở trace lỗi để xác định observation cuối cùng thành công.
  3. Tìm `request_failed` trong log bằng correlation ID.
- Mitigation tạm thời: Rollback prompt `production` nếu lỗi xuất hiện sau khi đổi label; nếu không, tắt incident và cô lập feature lỗi.
- Owner: `api-oncall`

## Alert 3

- Tên: Quality score degradation
- Severity: warning
- SLI/SLO liên quan: `quality_score_avg >= 0.75`
- Điều kiện và thời gian duy trì: `quality_score_avg < 0.75` trong 15 phút liên tục.
- Ảnh hưởng tới người dùng: Câu trả lời có thể thiếu ngữ cảnh hoặc ít hữu ích dù API vẫn thành công.
- Ba bước kiểm tra đầu tiên:
  1. Phân nhóm trace theo prompt version, feature và model.
  2. So sánh prompt metadata và số document retrieval của các trace điểm thấp.
  3. Kiểm tra `quality_score`, token và correlation ID trong log.
- Mitigation tạm thời: Rollback `production` về prompt baseline và chạy lại cùng bộ input.
- Owner: `ai-quality-oncall`
