from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

CORRELATION_ID_HEADER = "x-request-id"
RESPONSE_TIME_HEADER = "x-response-time-ms"


def new_correlation_id() -> str:
    """Correlation ID theo format req-<8 ký tự hex>."""
    return f"req-{uuid.uuid4().hex[:8]}"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Xóa context của request trước để không rò rỉ metadata sang request mới
        # (worker/task có thể được tái sử dụng giữa các request).
        clear_contextvars()

        # Ưu tiên ID do client gửi lên để truy vết xuyên service; nếu không có thì tự sinh.
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or new_correlation_id()

        # Bind vào structlog contextvars: mọi log sau đây tự động mang correlation_id.
        bind_contextvars(correlation_id=correlation_id)

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            # Lưu lại để exception handler ở app/main.py cũng gắn được header khi lỗi.
            request.state.response_time_ms = elapsed_ms

        # Trả correlation ID về client để họ đính kèm khi báo lỗi/tra cứu log.
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        response.headers[RESPONSE_TIME_HEADER] = f"{elapsed_ms:.1f}"

        return response
