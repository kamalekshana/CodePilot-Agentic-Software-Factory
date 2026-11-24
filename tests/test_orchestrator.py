
import pytest

from core.base_agent import BaseAgent
from core.orchestrator import Orchestrator
from schemas.task import TaskStatus
from schemas.workflow import WorkflowStatus


class MockLLMClient:
    """Simulates successful LLM responses."""

    def generate_response(
        self,
        system_prompt,
        user_prompt,
        **kwargs,
    ):
        return f"Processed: {user_prompt}"


class FailingLLMClient:
    """Simulates an LLM failure."""

    def generate_response(
        self,
        system_prompt,
        user_prompt,
        **kwargs,
    ):
        raise RuntimeError("Simulated agent failure")


class MockAgent(BaseAgent):
    """Reusable mock agent for Orchestrator testing."""

    @property
    def system_prompt(self):
        return "You are a mock agent."


def create_orchestrator():
    """Create an Orchestrator with two mock agents."""

    agents = {
        "requirements_agent": MockAgent(
            name="Requirements Agent",
            role="Requirements Analysis",
            llm_client=MockLLMClient(),
        ),
        "architect_agent": MockAgent(
            name="Architect Agent",
            role="System Architecture",
            llm_client=MockLLMClient(),
        ),
    }

    return Orchestrator(agents=agents)


def test_orchestrator_initialization():
    orchestrator = create_orchestrator()

    assert len(orchestrator.agents) == 2


def test_orchestrator_rejects_empty_agents():
    with pytest.raises(ValueError):
        Orchestrator(agents={})


def test_orchestrator_completes_workflow():
    orchestrator = create_orchestrator()

    workflow = orchestrator.run_workflow(
        project_name="Calculator",
        user_request="Build a calculator application",
        agent_names=[
            "requirements_agent",
            "architect_agent",
        ],
    )

    assert workflow.status == WorkflowStatus.COMPLETED
    assert len(workflow.tasks) == 2
    assert workflow.current_task_id is None
    assert workflow.final_output.startswith("Processed:")

    for task in workflow.tasks:
        assert task.status == TaskStatus.COMPLETED


def test_orchestrator_passes_output_between_agents():
    orchestrator = create_orchestrator()

    workflow = orchestrator.run_workflow(
        project_name="Calculator",
        user_request="Build a calculator",
        agent_names=[
            "requirements_agent",
            "architect_agent",
        ],
    )

    first_output = workflow.tasks[0].output_data
    second_input = workflow.tasks[1].input_data

    assert second_input == first_output
    assert "Build a calculator" in first_output


def test_orchestrator_tracks_task_dependencies():
    orchestrator = create_orchestrator()

    workflow = orchestrator.run_workflow(
        project_name="Calculator",
        user_request="Build a calculator",
        agent_names=[
            "requirements_agent",
            "architect_agent",
        ],
    )

    assert workflow.tasks[0].depends_on == []
    assert workflow.tasks[1].depends_on == [
        workflow.tasks[0].task_id
    ]


def test_orchestrator_handles_agent_failure():
    failing_agent = MockAgent(
        name="Failing Agent",
        role="Testing",
        llm_client=FailingLLMClient(),
    )

    agents = {
        "failing_agent": failing_agent,
        "architect_agent": MockAgent(
            name="Architect Agent",
            role="Architecture",
            llm_client=MockLLMClient(),
        ),
    }

    orchestrator = Orchestrator(agents=agents)

    workflow = orchestrator.run_workflow(
        project_name="Failure Test",
        user_request="Test failure handling",
        agent_names=[
            "failing_agent",
            "architect_agent",
        ],
    )

    assert workflow.status == WorkflowStatus.FAILED
    assert workflow.tasks[0].status == TaskStatus.FAILED
    assert workflow.tasks[1].status == TaskStatus.BLOCKED
    assert workflow.current_task_id is None
    assert workflow.error is not None
