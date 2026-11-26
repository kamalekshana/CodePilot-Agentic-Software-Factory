
from pathlib import Path

from core.llm_client import LLMClient
from agents.coding_agent import CodingAgent
from schemas.agent_response import AgentStatus
from services.workspace_manager import WorkspaceManager


class MockProject1Adapter:
    """Mock Project 1 without making API requests."""

    def __init__(self):
        self.calls = []

    def generate_code(self, task, workspace):
        self.calls.append({
            "task": task,
            "workspace": Path(workspace),
        })

        return 'print("CODING_AGENT_TEST_OK")'


def create_test_plan():
    return {
        "project_name": "Test Application",
        "summary": "Test dependency-aware code generation.",
        "tasks": [
            {
                "task_id": "TASK-001",
                "title": "Create Main Module",
                "description": "Create the main Python module.",
                "priority": "high",
                "dependencies": [],
                "completion_criteria": [
                    "Main module exists."
                ],
            },
            {
                "task_id": "TASK-002",
                "title": "Create Helper Module",
                "description": "Create a helper Python module.",
                "priority": "medium",
                "dependencies": ["TASK-001"],
                "completion_criteria": [
                    "Helper module exists."
                ],
            },
        ],
        "execution_order": ["TASK-001", "TASK-002"],
    }


def test_coding_agent_generates_project_files(tmp_path):
    workspace_manager = WorkspaceManager(tmp_path / "workspace")
    workspace = workspace_manager.create_workspace("test_application")

    mock_adapter = MockProject1Adapter()

    agent = CodingAgent(
        llm_client=LLMClient.__new__(LLMClient),
        project1_adapter=mock_adapter,
        workspace_manager=workspace_manager,
    )

    response = agent.generate_project(
        project_name="Test Application",
        requirements="Create a simple Python application.",
        architecture="Use separate Python modules.",
        implementation_plan=create_test_plan(),
        workspace=workspace,
    )

    assert response.status == AgentStatus.SUCCESS
    assert len(response.metadata["completed_tasks"]) == 2
    assert len(response.metadata["generated_files"]) == 2

    files = workspace_manager.list_files(workspace)
    assert len(files) == 2

    for filename in files:
        assert workspace_manager.read_file(
            workspace,
            filename,
        ) == 'print("CODING_AGENT_TEST_OK")'

    assert len(mock_adapter.calls) == 2


def test_coding_agent_rejects_invalid_python(tmp_path):
    workspace_manager = WorkspaceManager(tmp_path / "workspace")
    workspace = workspace_manager.create_workspace("invalid_application")

    class InvalidAdapter:
        def generate_code(self, task, workspace):
            return "def broken(:"

    agent = CodingAgent(
        llm_client=LLMClient.__new__(LLMClient),
        project1_adapter=InvalidAdapter(),
        workspace_manager=workspace_manager,
    )

    response = agent.generate_project(
        project_name="Test Application",
        requirements="Create a Python application.",
        architecture="Use separate modules.",
        implementation_plan=create_test_plan(),
        workspace=workspace,
    )

    assert response.status == AgentStatus.FAILED
    assert len(response.metadata["generated_files"]) == 0
    assert workspace_manager.list_files(workspace) == []


def test_coding_agent_rejects_missing_dependencies(tmp_path):
    workspace_manager = WorkspaceManager(tmp_path / "workspace")
    workspace = workspace_manager.create_workspace("dependency_application")

    class FailingAdapter:
        def generate_code(self, task, workspace):
            raise RuntimeError("Simulated generation failure")

    agent = CodingAgent(
        llm_client=LLMClient.__new__(LLMClient),
        project1_adapter=FailingAdapter(),
        workspace_manager=workspace_manager,
    )

    response = agent.generate_project(
        project_name="Test Application",
        requirements="Create a Python application.",
        architecture="Use separate modules.",
        implementation_plan=create_test_plan(),
        workspace=workspace,
    )

    assert response.status == AgentStatus.FAILED
    assert response.metadata["completed_tasks"] == []
    assert len(response.metadata["failed_tasks"]) == 1
    assert workspace_manager.list_files(workspace) == []
