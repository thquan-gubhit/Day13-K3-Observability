from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import langfuse

from app import tracing


class TracingAdapterTests(unittest.TestCase):
    def test_adapter_uses_the_installed_langfuse_v4_api(self) -> None:
        self.assertEqual(tracing._sdk_observe.__module__, langfuse.observe.__module__)
        client = tracing.get_langfuse_client()
        self.assertTrue(callable(client.update_current_span))
        self.assertTrue(callable(client.update_current_generation))

    def test_trace_mask_redacts_pii(self) -> None:
        masked = tracing.mask_trace_value(
            "Email student@vinuni.edu.vn phone 0987654321 card 4111 1111 1111 1111"
        )

        self.assertNotIn("student@vinuni.edu.vn", masked)
        self.assertNotIn("0987654321", masked)
        self.assertNotIn("4111 1111 1111 1111", masked)

    def test_initialization_preserves_original_langfuse_host_format(self) -> None:
        captured: dict = {}

        class FakeLangfuse:
            def __init__(self, **kwargs) -> None:
                captured.update(kwargs)

        environment = {
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "http://langfuse.local:3000",
            "APP_ENV": "test",
        }
        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(tracing, "_client", None),
            patch.object(tracing, "Langfuse", FakeLangfuse),
        ):
            tracing.initialize_langfuse()

        self.assertEqual(captured["host"], "http://langfuse.local:3000")
        self.assertEqual(captured["environment"], "test")
        self.assertTrue(callable(captured["mask_otel_spans"]))

    def test_tracing_is_disabled_without_both_keys(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(tracing.tracing_enabled())

        with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-only"}, clear=True):
            self.assertFalse(tracing.tracing_enabled())


if __name__ == "__main__":
    unittest.main()
