from __future__ import annotations

from contextlib import contextmanager

from app import agent as agent_module
from app import mock_llm, mock_rag


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.span_updates: list[dict] = []
        self.generation_updates: list[dict] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def update_current_span(self, **kwargs) -> None:
        self.span_updates.append(kwargs)

    def update_current_generation(self, **kwargs) -> None:
        self.generation_updates.append(kwargs)


def test_agent_links_prompt_version_to_trace_and_generation(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(mock_llm, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(mock_rag, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    propagated: dict = {}

    @contextmanager
    def fake_propagate_attributes(**kwargs):
        propagated.update(kwargs)
        yield

    monkeypatch.setattr(agent_module, "propagate_attributes", fake_propagate_attributes)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces",
        correlation_id="req-1234abcd",
    )

    trace_metadata = client.span_updates[-1]["metadata"]
    generation_update = client.generation_updates[-1]
    assert trace_metadata == {
        "correlation_id": "req-1234abcd",
        "feature": "qa",
        "model": "claude-sonnet-4-5",
        "prompt_name": "day13-chat",
        "prompt_label": "production",
        "prompt_version": "3",
        "prompt_source": "langfuse",
        "document_count": 1,
    }
    assert generation_update["prompt"] is client.prompt
    assert generation_update["metadata"]["prompt_version"] == "3"
    assert generation_update["model"] == "claude-sonnet-4-5"
    assert generation_update["usage_details"]["input_tokens"] > 0
    assert propagated["trace_name"] == "chat-response"
    assert propagated["user_id"] != "student-01"
    assert propagated["session_id"] == "session-01"
    assert propagated["tags"] == ["lab", "qa", "api"]
