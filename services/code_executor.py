
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from config.settings import CODE_EXECUTION_TIMEOUT
from services.workspace_manager import WorkspaceManager
from core.approval_manager import ApprovalManager


@dataclass
class ExecutionResult:
    """Structured result returned after Python execution."""
    success: bool
    return_code: int | None
    stdout: str
    stderr: str
    error: str | None = None
    timed_out: bool = False


class CodeExecutor:
    """Executes approved Python files in a project workspace.

    This is controlled subprocess execution, NOT a security sandbox.
    """

    def __init__(
        self,
        workspace_manager: WorkspaceManager | None = None,
        approval_manager: ApprovalManager | None = None,
        timeout: int = CODE_EXECUTION_TIMEOUT,
    ):
        if not isinstance(timeout, int) or timeout < 1:
            raise ValueError("Execution timeout must be a positive integer.")

        self.workspace_manager = workspace_manager or WorkspaceManager()
        self.approval_manager = approval_manager or ApprovalManager()
        self.timeout = timeout

    def execute_file(
        self,
        workspace: Path | str,
        filename: str,
        approval_id: str,
    ) -> ExecutionResult:
        """Execute a Python file only with a valid approved request."""

        if not self.approval_manager.is_approved(approval_id):
            raise PermissionError(
                "Execution requires a valid approved request."
            )

        project_dir = self.workspace_manager._resolve_project_dir(workspace)

        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Python filename cannot be empty.")

        if Path(filename).suffix.lower() != ".py":
            raise ValueError("Only Python files can be executed.")

        file_path = self.workspace_manager._resolve_file_path(
            project_dir, filename
        )

        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Python file not found: {filename}")

        if file_path.stat().st_size > self.workspace_manager.MAX_FILE_SIZE:
            raise ValueError("Python file exceeds the permitted size limit.")

        source_code = self.workspace_manager.read_file(
            project_dir, filename
        )
        self.workspace_manager.validate_python_code(source_code)

        try:
            result = subprocess.run(
                [sys.executable, str(file_path)],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=False,
                check=False,
            )

            return ExecutionResult(
                success=result.returncode == 0,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or ""
            stderr = error.stderr or ""

            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")

            return ExecutionResult(
                success=False,
                return_code=None,
                stdout=stdout,
                stderr=stderr,
                error=f"Execution exceeded {self.timeout} seconds.",
                timed_out=True,
            )

        except OSError as error:
            return ExecutionResult(
                success=False,
                return_code=None,
                stdout="",
                stderr="",
                error=f"{type(error).__name__}: {error}",
            )
