
from core.base_agent import BaseAgent


class MockLLMClient:
    """Simulates the shared LLM client for testing."""

    def generate_response(
        self,
        system_prompt,
        user_prompt,
        **kwargs
    ):
        return f"Mock response for: {user_prompt}"


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


def test_agent_rejects_empty_input():
    agent = SampleAgent(
        name="Sample Agent",
        role="Testing",
        llm_client=MockLLMClient(),
    )

    try:
        agent.run("")
        assert False, "Expected ValueError for empty input"
    except ValueError:
        pass
