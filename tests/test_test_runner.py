
import pytest

from core.approval_manager import ApprovalManager
from services.workspace_manager import WorkspaceManager
from tools.test_runner import TestRunner


@pytest.fixture
def setup_runner(tmp_path):
    workspace_manager = WorkspaceManager(tmp_path / "workspace")
    approval_manager = ApprovalManager()
    runner = TestRunner(
        workspace_manager=workspace_manager,
        approval_manager=approval_manager,
        timeout=10,
    )

    workspace = workspace_manager.create_workspace("Runner Test")
    return runner, workspace, approval_manager


def test_runner_requires_approval(setup_runner):
    runner, workspace, _ = setup_runner

    request = runner.request_test_approval(workspace)

    with pytest.raises(PermissionError):
        runner.run_tests(workspace, request.approval_id)


def test_runner_rejects_wrong_approval_action(setup_runner):
    runner, workspace, approval_manager = setup_runner

    request = approval_manager.request_approval(
        action="delete_project",
        details="Test approval validation",
        resource=str(workspace),
    )
    approval_manager.approve(request.approval_id)

    with pytest.raises(PermissionError):
        runner.run_tests(workspace, request.approval_id)


def test_runner_rejects_approval_for_another_workspace(setup_runner):
    runner, workspace, approval_manager = setup_runner

    request = approval_manager.request_approval(
        action="run_tests",
        details="Test approval validation",
        resource=str(workspace / "another"),
    )
    approval_manager.approve(request.approval_id)

    with pytest.raises(PermissionError):
        runner.run_tests(workspace, request.approval_id)


def test_runner_executes_approved_pytest(setup_runner):
    runner, workspace, approval_manager = setup_runner

    runner.workspace_manager.write_file(
        workspace,
        "tests/test_sample.py",
        "def test_sample():\n    assert 2 + 2 == 4\n",
    )

    request = runner.request_test_approval(
        workspace,
        ["tests/test_sample.py"],
    )
    approval_manager.approve(request.approval_id)

    result = runner.run_tests(
        workspace,
        request.approval_id,
        ["tests/test_sample.py"],
    )

    assert result.status == "passed"
    assert result.exit_code == 0
    assert result.passed == 1


def test_runner_reports_failed_test(setup_runner):
    runner, workspace, approval_manager = setup_runner

    runner.workspace_manager.write_file(
        workspace,
        "tests/test_failure.py",
        "def test_failure():\n    assert 2 + 2 == 5\n",
    )

    request = runner.request_test_approval(
        workspace,
        ["tests/test_failure.py"],
    )
    approval_manager.approve(request.approval_id)

    result = runner.run_tests(
        workspace,
        request.approval_id,
        ["tests/test_failure.py"],
    )

    assert result.status == "failed"
    assert result.exit_code == 1
    assert result.failed == 1


def test_runner_rejects_path_traversal(setup_runner):
    runner, workspace, _ = setup_runner

    with pytest.raises(ValueError):
        runner.request_test_approval(
            workspace,
            ["../outside.py"],
        )
