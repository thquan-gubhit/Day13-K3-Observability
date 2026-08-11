# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `high_latency_p95`
- Severity: `warning`
- SLI/SLO liên quan: `latency_p95_ms`; mục tiêu P95 ≤ 3000 ms cho 99,5% request trong 28 ngày.
- Điều kiện và thời gian duy trì: `latency_p95_ms > 3000` liên tục 5 phút.
- Ảnh hưởng tới người dùng: phần lớn người dùng phải chờ hơn 3 giây và có thể gửi lại request hoặc rời phiên.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận P50/P95/P99 và traffic trong cùng cửa sổ để loại trừ một outlier đơn lẻ.
  2. Mở các trace chậm nhất trên Langfuse, so sánh thời gian span `retrieve` và `generate`.
  3. Tra log bằng correlation ID của trace chậm; kiểm tra feature, model, incident và lỗi dependency.
- Mitigation tạm thời: giảm concurrency, tắt feature/dependency đang chậm hoặc chuyển sang fallback; theo dõi P95 trong ít nhất 5 phút sau thay đổi.
- Owner: `on-call-engineer`

## Alert 2

- Tên: `elevated_error_rate`
- Severity: `critical`
- SLI/SLO liên quan: `error_rate_pct`; mục tiêu error rate ≤ 2% cho 99% thời gian trong 28 ngày.
- Điều kiện và thời gian duy trì: `error_rate_pct > 5` liên tục 3 phút.
- Ảnh hưởng tới người dùng: request trả lỗi hoặc không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận mẫu số traffic và breakdown theo `error_type`, feature và thời điểm bắt đầu.
  2. Mở trace lỗi đại diện để xác định span thất bại đầu tiên.
  3. Tra log `request_failed` bằng correlation ID, kiểm tra dependency và thay đổi triển khai gần nhất.
- Mitigation tạm thời: rollback thay đổi gần nhất hoặc chuyển dependency lỗi sang fallback; giới hạn traffic nếu lỗi làm quá tải dây chuyền.
- Owner: `on-call-engineer`

## Alert 3

- Tên: `cost_budget_exceeded`
- Severity: `warning`
- SLI/SLO liên quan: `daily_cost_usd`; ngân sách ≤ 2,5 USD/ngày.
- Điều kiện và thời gian duy trì: `daily_cost_usd > 2.5` trong ngày hiện tại.
- Ảnh hưởng tới người dùng: chưa nhất thiết gây lỗi ngay, nhưng có nguy cơ hết ngân sách hoặc phải giới hạn dịch vụ.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận tổng cost và traffic, sau đó tính cost/request so với baseline.
  2. Phân tách token input/output theo model, feature và prompt version để tìm nhóm tăng bất thường.
  3. Mở trace cost cao, kiểm tra prompt, số token output, retry và request lặp.
- Mitigation tạm thời: giới hạn output token, giảm retry, chuyển model tiết kiệm hơn hoặc rate-limit feature gây tăng chi phí.
- Owner: `team-lead`

## Nguyên tắc thiết kế

Các alert trên đều symptom-based vì chúng phản ánh điều người dùng hoặc doanh nghiệp thực sự chịu ảnh hưởng: chậm, lỗi và vượt ngân sách. Tên hàm hay lỗi implementation có thể thay đổi sau refactor và đôi khi xuất hiện mà chưa ảnh hưởng SLO; vì vậy chúng phù hợp làm tín hiệu chẩn đoán sau khi alert kích hoạt hơn là điều kiện cảnh báo chính.
