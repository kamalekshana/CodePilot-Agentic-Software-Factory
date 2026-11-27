
import pytest

from services.workspace_manager import WorkspaceManager
from tools.test_runner import TestRunner
from agents.testing_agent import TestingAgent


class FakeLLMClient:
    def generate_response(self, system_prompt, user_prompt):
        return "Testing analysis completed."


@pytest.fixture
def setup_agent(tmp_path):
    manager = WorkspaceManager(tmp_path / "workspace")
    workspace = manager.create_workspace("Testing Agent Project")

    manager.write_file(
        workspace,
        "app.py",
        "def add(a, b):\n    return a + b\n",
    )

    manager.write_file(
        workspace,
        "tests/test_app.py",
        "def test_add():\n    assert 2 + 2 == 4\n",
    )

    runner = TestRunner(workspace_manager=manager)

    agent = TestingAgent(
        llm_client=FakeLLMClient(),
        workspace_manager=manager,
        test_runner=runner,
    )

    return agent, workspace


def test_testing_agent_inspects_project(setup_agent):
    agent, workspace = setup_agent

    inventory = agent.inspect_project(workspace)

    assert inventory["has_tests"] is True
    assert "app.py" in inventory["python_files"]
    assert "tests/test_app.py" in inventory["test_files"]


def test_testing_agent_detects_missing_tests(tmp_path):
    manager = WorkspaceManager(tmp_path / "workspace")
    workspace = manager.create_workspace("No Tests")

    manager.write_file(workspace, "app.py", "print('Hello')\n")

    agent = TestingAgent(
        llm_client=FakeLLMClient(),
        workspace_manager=manager,
    )

    inventory = agent.inspect_project(workspace)

    assert inventory["has_tests"] is False
    assert inventory["test_files"] == []


def test_testing_agent_requires_approval(setup_agent):
    agent, workspace = setup_agent

    request = agent.request_test_approval(workspace)

    response = agent.run_project_tests(
        workspace,
        request.approval_id,
    )

    assert response.status.value == "failed"
    assert "approved" in response.error.lower()


def test_testing_agent_generates_report(setup_agent):
    agent, workspace = setup_agent

    request = agent.request_test_approval(
        workspace,
        ["tests/test_app.py"],
    )

    agent.test_runner.approval_manager.approve(
        request.approval_id
    )

    response = agent.run_project_tests(
        workspace,
        request.approval_id,
        ["tests/test_app.py"],
    )

    assert response.status.value == "success"
    assert response.metadata["execution_status"] == "passed"
    assert response.metadata["passed"] == 1
    assert response.metadata["report_path"] == "reports/test_report_001.md"

    report = agent.workspace_manager.read_file(
        workspace,
        "reports/test_report.md",
    )

    assert "PASSED" in report
    assert "Total tests" in report
