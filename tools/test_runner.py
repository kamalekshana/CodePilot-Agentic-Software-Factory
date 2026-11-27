
"""Approved pytest execution for generated CodePilot workspaces."""

import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.approval_manager import ApprovalManager
from services.workspace_manager import WorkspaceManager


@dataclass
class TestRunResult:
    """Structured result of a pytest execution."""

    status: str
    exit_code: int | None
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration_seconds: float
    stdout: str
    stderr: str
    command: list[str]
    execution_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Prevent pytest from collecting this dataclass as a test class.
TestRunResult.__test__ = False


class TestRunner:
    """Run only approved pytest commands inside generated workspaces."""

    def __init__(
        self,
        workspace_manager: WorkspaceManager | None = None,
        approval_manager: ApprovalManager | None = None,
        timeout: int = 60,
    ):
        if not isinstance(timeout, int) or timeout < 1:
            raise ValueError("Timeout must be a positive integer.")

        self.workspace_manager = workspace_manager or WorkspaceManager()
        self.approval_manager = approval_manager or ApprovalManager()
        self.timeout = timeout

    def request_test_approval(
        self,
        workspace: str | Path,
        test_paths: list[str] | None = None,
    ):
        """Request human approval for a pytest run."""

        project_dir = self.workspace_manager._resolve_project_dir(
            workspace
        )

        paths = self._validate_test_paths(project_dir, test_paths)

        details = (
            "Execute pytest in the generated project workspace. "
            f"Test targets: {paths if paths else 'pytest discovery'}"
        )

        return self.approval_manager.request_approval(
            action="run_tests",
            details=details,
            resource=str(project_dir),
        )

    def _validate_test_paths(
        self,
        project_dir: Path,
        test_paths: list[str] | None,
    ) -> list[str]:
        """Validate relative test paths and reject paths outside workspace."""

        if test_paths is None:
            return []

        if not isinstance(test_paths, list):
            raise ValueError("Test paths must be a list.")

        validated = []

        for filename in test_paths:
            if not isinstance(filename, str) or not filename.strip():
                raise ValueError("Test path cannot be empty.")

            file_path = self.workspace_manager._resolve_file_path(
                project_dir,
                filename,
            )

            if not file_path.exists():
                raise FileNotFoundError(
                    f"Test target does not exist: {filename}"
                )

            if not file_path.is_file():
                raise ValueError(
                    f"Test target must be a file: {filename}"
                )

            if file_path.suffix.lower() != ".py":
                raise ValueError(
                    "Only Python pytest test files are supported."
                )

            validated.append(
                file_path.relative_to(project_dir).as_posix()
            )

        return validated

    @staticmethod
    def _parse_summary(stdout: str, stderr: str) -> dict[str, int]:
        """Extract pytest result counts from its summary."""

        combined = f"{stdout}\n{stderr}"

        counts = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
        }

        patterns = {
            "passed": r"(\d+)\s+passed",
            "failed": r"(\d+)\s+failed",
            "errors": r"(\d+)\s+errors?",
            "skipped": r"(\d+)\s+skipped",
        }

        for key, pattern in patterns.items():
            matches = re.findall(
                pattern,
                combined,
                re.IGNORECASE,
            )

            if matches:
                counts[key] = int(matches[-1])

        return counts

    @staticmethod
    def _decode_output(value):
        """Convert subprocess output into safe text."""

        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")

        return value or ""

    def run_tests(
        self,
        workspace: str | Path,
        approval_id: str,
        test_paths: list[str] | None = None,
    ) -> TestRunResult:
        """Execute pytest after verifying explicit human approval."""

        project_dir = self.workspace_manager._resolve_project_dir(
            workspace
        )

        request = self.approval_manager.get_request(approval_id)

        if request.action != "run_tests":
            raise PermissionError(
                "Approval is not for pytest execution."
            )

        if request.resource != str(project_dir):
            raise PermissionError(
                "Approval does not match this project workspace."
            )

        if not self.approval_manager.is_approved(approval_id):
            raise PermissionError(
                "Pytest execution requires approved human authorization."
            )

        paths = self._validate_test_paths(project_dir, test_paths)

        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--tb=short",
            *paths,
        ]

        start_time = time.monotonic()

        try:
            completed = subprocess.run(
                command,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=False,
                check=False,
            )

            duration = time.monotonic() - start_time
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""

            counts = self._parse_summary(stdout, stderr)
            total = sum(counts.values())

            if completed.returncode == 0:
                status = "passed"
            elif completed.returncode == 1:
                status = "failed"
            elif completed.returncode == 5:
                status = "no_tests"
            else:
                status = "execution_error"

            return TestRunResult(
                status=status,
                exit_code=completed.returncode,
                total=total,
                passed=counts["passed"],
                failed=counts["failed"],
                errors=counts["errors"],
                skipped=counts["skipped"],
                duration_seconds=round(duration, 3),
                stdout=stdout,
                stderr=stderr,
                command=command,
                execution_error=(
                    "Pytest could not execute successfully."
                    if status == "execution_error"
                    else None
                ),
            )

        except subprocess.TimeoutExpired as error:
            duration = time.monotonic() - start_time

            return TestRunResult(
                status="timeout",
                exit_code=None,
                total=0,
                passed=0,
                failed=0,
                errors=0,
                skipped=0,
                duration_seconds=round(duration, 3),
                stdout=self._decode_output(error.stdout),
                stderr=self._decode_output(error.stderr),
                command=command,
                execution_error=(
                    f"Pytest exceeded the {self.timeout}-second timeout."
                ),
            )

        except OSError as error:
            duration = time.monotonic() - start_time

            return TestRunResult(
                status="execution_error",
                exit_code=None,
                total=0,
                passed=0,
                failed=0,
                errors=0,
                skipped=0,
                duration_seconds=round(duration, 3),
                stdout="",
                stderr="",
                command=command,
                execution_error=f"{type(error).__name__}: {error}",
            )


# Prevent pytest from collecting the runner itself.
TestRunner.__test__ = False
