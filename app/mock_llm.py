from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

from .incidents import STATE
from .pii import scrub_text
from .tracing import get_langfuse_client, observe


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


class FakeLLM:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model

    @observe(name="generate-response", as_type="generation", capture_input=False, capture_output=False)
    def generate(
        self,
        prompt: str,
        *,
        managed_prompt: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FakeResponse:
        time.sleep(0.15)
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(80, 180)
        if STATE["cost_spike"]:
            output_tokens *= 4
        answer = (
            "Starter answer. Teams should improve this output logic and add better quality checks. "
            "Use retrieved context and keep responses concise."
        )
        cost_usd = round((input_tokens / 1_000_000) * 3 + (output_tokens / 1_000_000) * 15, 6)
        get_langfuse_client().update_current_generation(
            input=scrub_text(prompt),
            output=scrub_text(answer),
            model=self.model,
            usage_details={"input_tokens": input_tokens, "output_tokens": output_tokens},
            cost_details={"total": cost_usd},
            metadata=metadata or {},
            prompt=managed_prompt,
        )
        return FakeResponse(text=answer, usage=FakeUsage(input_tokens, output_tokens), model=self.model)
