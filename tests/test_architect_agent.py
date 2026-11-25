
import pytest

from agents.architect_agent import ArchitectAgent
from schemas.agent_response import AgentStatus


VALID_ARCHITECTURE = """
# System Architecture Document

## 1. Architecture Overview
Proposed application architecture.

## 2. Architecture Style
Layered architecture recommendation.

## 3. Technology Stack
Technology recommendations.

## 4. System Components
Application components.

## 5. Component Interactions
Component communication.

## 6. Data Flow
Application data flow.

## 7. Security Considerations
Security recommendations.

## 8. Scalability and Reliability
Reliability considerations.

## 9. Architecture Decisions and Trade-offs
Architecture trade-offs.

## 10. Assumptions and Open Decisions
Decisions requiring confirmation.
"""

VALID_DATABASE = """
# Database Design Document

## 1. Database Overview
Database overview.

## 2. Database Technology
Database recommendation.

## 3. Entity Overview
Entity descriptions.

## 4. Entity Attributes
Entity attributes.

## 5. Primary and Foreign Keys
Key definitions.

## 6. Entity Relationships
Entity relationships.

## 7. Data Integrity Constraints
Integrity rules.

## 8. Indexing Strategy
Index recommendations.

## 9. Data Security and Backup Considerations
Security considerations.

## 10. Assumptions and Open Decisions
Open database decisions.
"""


class MockLLMClient:
    def __init__(self, responses=None):
        self.responses = list(
            responses or [VALID_ARCHITECTURE, VALID_DATABASE]
        )
        self.prompts = []

    def generate_response(self, system_prompt, user_prompt, **kwargs):
        self.prompts.append((system_prompt, user_prompt))

        if not self.responses:
            raise RuntimeError("No mock response available.")

        return self.responses.pop(0)


def create_agent(responses=None):
    mock = MockLLMClient(responses)
    agent = ArchitectAgent(llm_client=mock)
    return agent, mock


def test_architect_agent_initialization():
    agent, _ = create_agent()

    assert agent.name == "Architect Agent"
    assert agent.role == "Software Architecture and Database Design"


def test_architect_agent_system_prompt():
    agent, _ = create_agent()

    assert "source of truth" in agent.system_prompt
    assert "assumptions" in agent.system_prompt.lower()


def test_generate_architecture():
    agent, mock = create_agent()

    requirements = "# Software Requirements Specification\nStock tracking."

    result = agent.generate_architecture(requirements)

    assert result.startswith("# System Architecture Document")
    assert "## 10. Assumptions and Open Decisions" in result
    assert requirements in mock.prompts[0][1]


def test_generate_database_design():
    agent, mock = create_agent([VALID_DATABASE])

    requirements = "# Software Requirements Specification\nBilling."

    result = agent.generate_database_design(requirements)

    assert result.startswith("# Database Design Document")
    assert "## 6. Entity Relationships" in result
    assert requirements in mock.prompts[0][1]


def test_architecture_rejects_empty_requirements():
    agent, _ = create_agent()

    with pytest.raises(ValueError, match="cannot be empty"):
        agent.generate_architecture("")


def test_database_design_rejects_empty_requirements():
    agent, _ = create_agent()

    with pytest.raises(ValueError, match="cannot be empty"):
        agent.generate_database_design("   ")


def test_architecture_rejects_incomplete_document():
    agent, _ = create_agent(["# System Architecture Document\n\nIncomplete"])

    with pytest.raises(RuntimeError, match="incomplete"):
        agent.generate_architecture("Requirements")


def test_database_design_rejects_incomplete_document():
    agent, _ = create_agent(["# Database Design Document\n\nIncomplete"])

    with pytest.raises(RuntimeError, match="incomplete"):
        agent.generate_database_design("Requirements")


def test_architect_execute_uses_standard_response():
    agent, _ = create_agent()

    response = agent.execute("Design a pharmacy application.")

    assert response.status == AgentStatus.SUCCESS
    assert response.agent_name == "Architect Agent"


def test_architect_handles_llm_failure():
    class FailingLLMClient:
        def generate_response(self, **kwargs):
            raise RuntimeError("Simulated architecture failure")

    agent = ArchitectAgent(llm_client=FailingLLMClient())

    response = agent.execute("Design an application.")

    assert response.status == AgentStatus.FAILED
    assert "Simulated architecture failure" in response.error
