
import pytest

import core.llm_client as llm_module
from core.llm_client import LLMClient


class FakeMessage:
    def __init__(self, content):
        self.content = content
        self.reasoning = None


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def create(self, **kwargs):
        return FakeResponse("Mock OpenRouter response")


class FakeChat:
    def __init__(self):
        self.completions = FakeCompletions()


class FakeOpenAIClient:
    def __init__(self, **kwargs):
        self.chat = FakeChat()


def test_llm_client_initialization(monkeypatch):
    monkeypatch.setattr(
        llm_module,
        "OPENROUTER_API_KEY",
        "test-api-key",
    )
    monkeypatch.setattr(
        llm_module,
        "OpenAI",
        FakeOpenAIClient,
    )

    client = LLMClient()

    assert client.model == llm_module.OPENROUTER_MODEL
    assert client.client is not None


def test_llm_client_rejects_missing_api_key(monkeypatch):
    monkeypatch.setattr(
        llm_module,
        "OPENROUTER_API_KEY",
        "",
    )

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        LLMClient()


def test_llm_client_generates_response(monkeypatch):
    monkeypatch.setattr(
        llm_module,
        "OPENROUTER_API_KEY",
        "test-api-key",
    )
    monkeypatch.setattr(
        llm_module,
        "OpenAI",
        FakeOpenAIClient,
    )

    client = LLMClient()

    result = client.generate_response(
        system_prompt="You are a test agent.",
        user_prompt="Test CodePilot.",
    )

    assert result == "Mock OpenRouter response"


def test_llm_client_wraps_api_errors(monkeypatch):
    monkeypatch.setattr(
        llm_module,
        "OPENROUTER_API_KEY",
        "test-api-key",
    )

    class FailingOpenAIClient:
        def __init__(self, **kwargs):
            self.chat = self

            class FailingCompletions:
                def create(self, **kwargs):
                    raise RuntimeError("Simulated API failure")

            self.completions = FailingCompletions()

    monkeypatch.setattr(
        llm_module,
        "OpenAI",
        FailingOpenAIClient,
    )

    client = LLMClient()

    with pytest.raises(RuntimeError, match="Simulated API failure"):
        client.generate_response(
            system_prompt="Test system prompt",
            user_prompt="Test user prompt",
        )
