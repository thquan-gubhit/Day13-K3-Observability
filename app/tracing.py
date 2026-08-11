from __future__ import annotations

import os
from contextlib import contextmanager
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any

try:
    from langfuse import Langfuse, observe as _sdk_observe, propagate_attributes
    from langfuse.types import MaskOtelSpansParams, MaskOtelSpansResult, OtelSpanPatch

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False
    Langfuse = None  # type: ignore[assignment]

    _sdk_observe = None

    @contextmanager
    def propagate_attributes(**kwargs: Any):
        yield

_client: Any | None = None


class _DummyClient:
    def update_current_span(self, **kwargs: Any) -> None:
        return None

    def update_current_generation(self, **kwargs: Any) -> None:
        return None

    def flush(self) -> None:
        return None


def observe(func: Any = None, **observe_kwargs: Any):
    """Use Langfuse only when configured; otherwise run without SDK warnings."""
    def decorator(target: Any):
        if not LANGFUSE_SDK_AVAILABLE or _sdk_observe is None:
            return target
        observed = _sdk_observe(**observe_kwargs)(target)
        if iscoroutinefunction(target):
            @wraps(target)
            async def async_wrapper(*args: Any, **kwargs: Any):
                if not tracing_enabled():
                    return await target(*args, **kwargs)
                return await observed(*args, **kwargs)

            return async_wrapper

        @wraps(target)
        def sync_wrapper(*args: Any, **kwargs: Any):
            if not tracing_enabled():
                return target(*args, **kwargs)
            return observed(*args, **kwargs)

        return sync_wrapper

    return decorator(func) if func is not None else decorator


def mask_trace_value(value: str) -> str:
    """Redact PII in serialized OTEL attributes before they leave the process."""
    from .pii import scrub_text

    return scrub_text(value)


def _mask_otel_spans(
    *, params: MaskOtelSpansParams
) -> MaskOtelSpansResult | None:
    if not LANGFUSE_SDK_AVAILABLE:
        return None
    patches = {}
    for identifier, span in params.spans.items():
        replacements = {
            key: masked
            for key, value in span.attributes.items()
            if isinstance(value, str) and (masked := mask_trace_value(value)) != value
        }
        if replacements:
            patches[identifier] = OtelSpanPatch(set_attributes=replacements)
    return MaskOtelSpansResult(span_patches=patches) if patches else None


def initialize_langfuse() -> Any:
    """Initialize the singleton after environment variables have been loaded."""
    global _client
    if _client is not None:
        return _client
    if not tracing_enabled() or Langfuse is None:
        _client = _DummyClient()
        return _client
    _client = Langfuse(
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        environment=os.getenv("APP_ENV", "development"),
        mask_otel_spans=_mask_otel_spans,
    )
    return _client


def get_langfuse_client():
    return initialize_langfuse()


def flush_langfuse() -> None:
    if _client is not None:
        _client.flush()


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )
