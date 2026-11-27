
from pathlib import Path

from agents.coding_agent import CodingAgent
from core.approval_manager import ApprovalManager
from schemas.agent_response import AgentStatus
from schemas.fix_task import FixTask
from services.workspace_manager import WorkspaceManager


class FakeLLMClient:
    def generate_response(self, system_prompt, user_prompt):
        return "Analysis"


class FakeProject1Adapter:
    def analyse_error(self, code, error_message):
        return "The function does not return the expected result."

    def fix_code(self, code, error_analysis):
        return "def calculate():\n    return 10\n"


def create_agent(tmp_path):
    workspace_manager = WorkspaceManager(
        workspace_root=tmp_path / "workspace"
    )
    approval_manager = ApprovalManager()

    agent = CodingAgent(
        llm_client=FakeLLMClient(),
        project1_adapter=FakeProject1Adapter(),
        workspace_manager=workspace_manager,
        approval_manager=approval_manager,
    )

    workspace = workspace_manager.create_workspace("Fix_Test_Project")

    workspace_manager.write_file(
        workspace,
        "inventory.py",
        "def calculate():\n    return 5\n",
    )

    fix_task = FixTask(
        filename="inventory.py",
        error_summary="Incorrect calculation result.",
        root_cause="The function returns 5 instead of 10.",
        correction_instructions="Return 10 from calculate().",
        related_test="test_calculate",
        priority="high",
    )

    return agent, workspace_manager, approval_manager, workspace, fix_task


def test_fix_requires_approval(tmp_path):
    agent, _, _, workspace, fix_task = create_agent(tmp_path)

    request = agent.request_fix_approval(workspace, fix_task)

    result = agent.apply_fix_task(
        workspace,
        fix_task,
        request.approval_id,
    )

    assert result.status == AgentStatus.FAILED
    assert result.metadata["file_modified"] is False


def test_approved_fix_is_applied(tmp_path):
    agent, _, approval_manager, workspace, fix_task = create_agent(
        tmp_path
    )

    request = agent.request_fix_approval(workspace, fix_task)
    approval_manager.approve(request.approval_id)

    result = agent.apply_fix_task(
        workspace,
        fix_task,
        request.approval_id,
    )

    assert result.status == AgentStatus.SUCCESS
    assert result.metadata["syntax_validated"] is True
    assert result.metadata["file_modified"] is True


def test_rejected_fix_is_not_applied(tmp_path):
    agent, workspace_manager, approval_manager, workspace, fix_task = (
        create_agent(tmp_path)
    )

    request = agent.request_fix_approval(workspace, fix_task)
    approval_manager.reject(request.approval_id)

    result = agent.apply_fix_task(
        workspace,
        fix_task,
        request.approval_id,
    )

    assert result.status == AgentStatus.FAILED

    original = workspace_manager.read_file(
        workspace,
        "inventory.py",
    )

    assert "return 5" in original


def test_fix_rejects_path_traversal(tmp_path):
    agent, _, _, workspace, _ = create_agent(tmp_path)

    fix_task = FixTask(
        filename="../outside.py",
        error_summary="Test error",
        root_cause="Test cause",
        correction_instructions="Test correction",
    )

    try:
        agent.request_fix_approval(workspace, fix_task)
        assert False, "Path traversal should have been rejected."
    except (ValueError, PermissionError):
        pass


def test_fix_rejects_modified_file_after_approval(tmp_path):
    agent, workspace_manager, approval_manager, workspace, fix_task = (
        create_agent(tmp_path)
    )

    request = agent.request_fix_approval(workspace, fix_task)
    approval_manager.approve(request.approval_id)

    workspace_manager.write_file(
        workspace,
        "inventory.py",
        "def calculate():\n    return 20\n",
        overwrite=True,
    )

    result = agent.apply_fix_task(
        workspace,
        fix_task,
        request.approval_id,
    )

    assert result.status == AgentStatus.FAILED
    assert result.metadata["file_modified"] is False
