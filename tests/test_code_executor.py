
import pytest

from core.approval_manager import ApprovalManager
from services.code_executor import CodeExecutor
from services.workspace_manager import WorkspaceManager


def create_executor(tmp_path, timeout=3):
    manager = WorkspaceManager(tmp_path / "workspace")
    approvals = ApprovalManager()
    workspace = manager.create_workspace("executor_test")
    executor = CodeExecutor(manager, approvals, timeout)
    return executor, manager, approvals, workspace


def request_approval(approvals):
    request = approvals.request_approval(
        "Execute Python file",
        "Run the generated test application",
        "executor_test/main.py",
    )
    return request.approval_id


def test_execution_requires_approval(tmp_path):
    executor, manager, approvals, workspace = create_executor(tmp_path)

    manager.write_file(workspace, "main.py", 'print("APPROVED")')

    request_id = request_approval(approvals)

    with pytest.raises(PermissionError):
        executor.execute_file(workspace, "main.py", request_id)


def test_approved_python_file_executes(tmp_path):
    executor, manager, approvals, workspace = create_executor(tmp_path)

    manager.write_file(
        workspace, "main.py", 'print("CODE_EXECUTOR_OK")'
    )

    request_id = request_approval(approvals)
    approvals.approve(request_id)

    result = executor.execute_file(workspace, "main.py", request_id)

    assert result.success is True
    assert result.return_code == 0
    assert "CODE_EXECUTOR_OK" in result.stdout
    assert result.timed_out is False


def test_non_python_file_is_rejected(tmp_path):
    executor, manager, approvals, workspace = create_executor(tmp_path)

    manager.write_file(workspace, "notes.txt", "Not executable.")
    request_id = request_approval(approvals)
    approvals.approve(request_id)

    with pytest.raises(ValueError):
        executor.execute_file(workspace, "notes.txt", request_id)


def test_path_traversal_is_rejected(tmp_path):
    executor, manager, approvals, workspace = create_executor(tmp_path)

    request_id = request_approval(approvals)
    approvals.approve(request_id)

    with pytest.raises(ValueError):
        executor.execute_file(workspace, "../outside.py", request_id)


def test_execution_timeout(tmp_path):
    executor, manager, approvals, workspace = create_executor(
        tmp_path, timeout=1
    )

    manager.write_file(
        workspace, "slow.py", "import time\ntime.sleep(5)\n"
    )

    request_id = request_approval(approvals)
    approvals.approve(request_id)

    result = executor.execute_file(workspace, "slow.py", request_id)

    assert result.success is False
    assert result.timed_out is True
    assert "exceeded" in result.error
