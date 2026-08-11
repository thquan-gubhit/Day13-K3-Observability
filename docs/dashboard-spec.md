# Yêu cầu dashboard

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md).

Dashboard chính cần đủ 6 nhóm thông tin:

1. Latency P50/P95/P99.
2. Traffic: request count hoặc QPS.
3. Error rate và breakdown theo loại lỗi.
4. Cost theo thời gian.
5. Tổng token input/output.
6. Quality proxy.

| Panel | Nguồn và phép tổng hợp | Đơn vị | Threshold/SLO |
|---|---|---|---|
| Latency percentiles | `response_sent.latency_ms` → P50/P95/P99 | ms | P95 ≤ 3000 ms |
| Request traffic | `request_received` → count và rate/phút | requests/min | ≥ 1 request/phút |
| Error rate and breakdown | `request_failed / request_received` và count theo `error_type` | % | Error rate ≤ 2% |
| Cost over time | tổng `response_sent.cost_usd` | USD | Tổng ≤ 2,5 USD |
| Input and output tokens | tổng `tokens_in`, `tokens_out` | tokens | Mỗi tổng ≤ 50.000 |
| Quality proxy | trung bình `quality_score` | score 0–1 | Mean ≥ 0,75 |

Công cụ runtime của nhóm: dashboard HTML tạo bởi `scripts/generate_dashboard.py` từ nguồn chuẩn `data/logs.jsonl`. Khoảng thời gian mặc định là 60 phút; trang tự refresh sau 30 giây.

Tiêu chuẩn trình bày:

- Khoảng thời gian mặc định: 1 giờ.
- Tự refresh mỗi 15–30 giây nếu công cụ hỗ trợ.
- Có threshold hoặc SLO line.
- Ghi rõ đơn vị.
- Chỉ giữ 6–8 panel quan trọng ở lớp chính.
- Screenshot phải nhìn được tên panel và khoảng thời gian.

Kiểm tra contract trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```
