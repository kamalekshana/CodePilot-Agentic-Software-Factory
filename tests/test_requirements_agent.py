
import pytest

from agents.requirements_agent import RequirementsAgent
from schemas.agent_response import AgentStatus


VALID_REQUIREMENTS = """
# Software Requirements Specification

## 1. Project Objective
Build a pharmacy inventory application.

## 2. Functional Requirements
| ID | Requirement | Description | Status |
|---|---|---|---|
| FR-001 | Stock tracking | Track medicine stock | Confirmed |

## 3. Non-Functional Requirements
Not specified.

## 4. User Roles
Not specified.

## 5. Main Application Features
Stock tracking, billing and expiry alerts.

## 6. Constraints
Not specified.

## 7. Assumptions Requiring Confirmation
Medicine batch tracking requires confirmation.

## 8. Ambiguities and Open Questions
Is barcode scanning required?

## 9. Requirements Summary
The three requested features are confirmed.
"""


class MockLLMClient:
    def __init__(self, response=VALID_REQUIREMENTS):
        self.response = response
        self.last_system_prompt = None
        self.last_user_prompt = None

    def generate_response(self, system_prompt, user_prompt, **kwargs):
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.response


def create_agent(response=VALID_REQUIREMENTS):
    mock_llm = MockLLMClient(response)
    agent = RequirementsAgent(llm_client=mock_llm)
    return agent, mock_llm


def test_requirements_agent_initialization():
    agent, _ = create_agent()
    assert agent.name == "Requirements Analyst Agent"
    assert agent.role == "Software Requirements Analysis"


def test_requirements_agent_system_prompt():
    agent, _ = create_agent()
    prompt = agent.system_prompt

    assert "FUNCTIONAL REQUIREMENTS" in prompt
    assert "NON-FUNCTIONAL REQUIREMENTS" in prompt
    assert "ASSUMPTIONS" in prompt
    assert "AMBIGUITIES AND OPEN QUESTIONS" in prompt


def test_analyze_requirements():
    agent, mock_llm = create_agent()
    request = (
        "Build a pharmacy inventory management application "
        "with billing, stock tracking and expiry alerts."
    )

    result = agent.analyze_requirements(request)

    assert result.startswith("# Software Requirements Specification")
    assert "Stock tracking" in result
    assert request in mock_llm.last_user_prompt


def test_agent_passes_system_prompt_to_llm():
    agent, mock_llm = create_agent()
    agent.analyze_requirements("Build a pharmacy application.")

    assert mock_llm.last_system_prompt == agent.system_prompt


def test_agent_rejects_empty_request():
    agent, _ = create_agent()

    with pytest.raises(ValueError, match="cannot be empty"):
        agent.analyze_requirements("")


def test_agent_rejects_whitespace_request():
    agent, _ = create_agent()

    with pytest.raises(ValueError, match="cannot be empty"):
        agent.analyze_requirements("   ")


def test_agent_execute_returns_standard_response():
    agent, _ = create_agent()
    response = agent.execute("Build a pharmacy application.")

    assert response.status == AgentStatus.SUCCESS
    assert response.agent_name == "Requirements Analyst Agent"


def test_agent_handles_llm_failure():
    class FailingLLMClient:
        def generate_response(self, **kwargs):
            raise RuntimeError("Simulated LLM failure")

    agent = RequirementsAgent(llm_client=FailingLLMClient())
    response = agent.execute("Build a pharmacy application.")

    assert response.status == AgentStatus.FAILED
    assert "Simulated LLM failure" in response.error


def test_agent_rejects_thinking_style_response():
    agent, _ = create_agent("Here's a thinking process: Let me analyze.")

    with pytest.raises(RuntimeError, match="invalid document"):
        agent.analyze_requirements("Build a pharmacy application.")


def test_agent_rejects_incomplete_document():
    agent, _ = create_agent(
        "# Software Requirements Specification\n\n"
        "## 1. Project Objective\n"
        "Build a pharmacy application."
    )

    with pytest.raises(RuntimeError, match="incomplete document"):
        agent.analyze_requirements("Build a pharmacy application.")
