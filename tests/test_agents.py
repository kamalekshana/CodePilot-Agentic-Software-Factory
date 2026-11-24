
import pytest

from core.base_agent import BaseAgent
from schemas.agent_response import AgentResponse, AgentStatus


class MockLLMClient:
    """Simulates the shared LLM client for testing."""

    def generate_response(
        self,
        system_prompt,
        user_prompt,
        **kwargs
    ):
        return f"Mock response for: {user_prompt}"


class FailingMockLLMClient:
    """Simulates an LLM service failure."""

    def generate_response(
        self,
        system_prompt,
        user_prompt,
        **kwargs
    ):
        raise RuntimeError("Simulated LLM failure")


class SampleAgent(BaseAgent):
    """A sample agent used to test BaseAgent."""

    @property
    def system_prompt(self):
        return "You are a sample testing agent."


def test_agent_initialization():
    agent = SampleAgent(
        name="Sample Agent",
        role="Testing",
        llm_client=MockLLMClient(),
    )

    assert agent.name == "Sample Agent"
    assert agent.role == "Testing"


def test_agent_run():
    agent = SampleAgent(
        name="Sample Agent",
        role="Testing",
        llm_client=MockLLMClient(),
    )

    result = agent.run("Test CodePilot")

    assert result == "Mock response for: Test CodePilot"


def test_agent_get_info():
    agent = SampleAgent(
        name="Sample Agent",
        role="Testing",
        llm_client=MockLLMClient(),
    )

    info = agent.get_info()

    assert info["name"] == "Sample Agent"
    assert info["role"] == "Testing"
    assert info["description"] == ""


def test_agent_rejects_empty_input():
    agent = SampleAgent(
        name="Sample Agent",
        role="Testing",
        llm_client=MockLLMClient(),
    )

    with pytest.raises(ValueError):
        agent.run("")


def test_agent_execute_returns_standard_response():
    agent = SampleAgent(
        name="Sample Agent",
        role="Testing",
        llm_client=MockLLMClient(),
    )

    response = agent.execute("Build a calculator")

    assert isinstance(response, AgentResponse)
    assert response.agent_name == "Sample Agent"
    assert response.status == AgentStatus.SUCCESS
    assert response.output == "Mock response for: Build a calculator"
    assert response.error is None


def test_agent_execute_rejects_empty_input():
    agent = SampleAgent(
        name="Sample Agent",
        role="Testing",
        llm_client=MockLLMClient(),
    )

    with pytest.raises(ValueError):
        agent.execute("")


def test_agent_execute_handles_llm_failure():
    agent = SampleAgent(
        name="Sample Agent",
        role="Testing",
        llm_client=FailingMockLLMClient(),
    )

    response = agent.execute("Generate some code")

    assert isinstance(response, AgentResponse)
    assert response.agent_name == "Sample Agent"
    assert response.status == AgentStatus.FAILED
    assert response.output == ""
    assert "Simulated LLM failure" in response.error


def test_agent_run_raises_on_llm_failure():
    agent = SampleAgent(
        name="Sample Agent",
        role="Testing",
        llm_client=FailingMockLLMClient(),
    )

    with pytest.raises(RuntimeError, match="Simulated LLM failure"):
        agent.run("Generate some code")
