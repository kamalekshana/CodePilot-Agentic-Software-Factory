
"""Generate and preserve Markdown reports for CodePilot."""

from datetime import datetime, timezone
from pathlib import Path

from services.workspace_manager import WorkspaceManager


class ReportGenerator:
    """Creates timestamped reports inside a generated project workspace."""

    def __init__(
        self,
        workspace_manager: WorkspaceManager | None = None,
    ):
        self.workspace_manager = (
            workspace_manager or WorkspaceManager()
        )

    def _next_report_number(self, report_dir, prefix):
        number = 1

        while (report_dir / f"{prefix}_{number:03d}.md").exists():
            number += 1

        return number

    def generate_test_report(
        self,
        workspace: str | Path,
        result,
    ) -> str:
        """Generate a Markdown report from actual TestRunResult data."""

        timestamp = datetime.now(timezone.utc)
        project_dir = self.workspace_manager._resolve_project_dir(
            workspace
        )

        report_dir = project_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        history_number = self._next_report_number(
            report_dir,
            "test_report",
        )

        report_name = f"test_report_{history_number:03d}.md"

        status_labels = {
            "passed": "PASSED",
            "failed": "FAILED",
            "no_tests": "NO TESTS COLLECTED",
            "timeout": "TIMED OUT",
            "execution_error": "EXECUTION ERROR",
        }

        status = status_labels.get(result.status, result.status.upper())

        report = f"""# CodePilot Test Report

## Execution Summary

- **Status:** {status}
- **Date (UTC):** {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
- **Total tests:** {result.total}
- **Passed:** {result.passed}
- **Failed:** {result.failed}
- **Errors:** {result.errors}
- **Skipped:** {result.skipped}
- **Duration:** {result.duration_seconds:.2f} seconds
- **Exit code:** {result.exit_code}

## Execution Details

**Command:** `{" ".join(result.command)}`

**Execution error:** {result.execution_error or "None"}

## Standard Output

```text
{result.stdout or "No standard output."}
```

## Standard Error

```text
{result.stderr or "No standard error."}
```
"""

        self.workspace_manager.write_file(
            workspace,
            f"reports/{report_name}",
            report,
        )

        self.workspace_manager.write_file(
            workspace,
            "reports/test_report.md",
            report,
            overwrite=True,
        )

        return f"reports/{report_name}"

    def generate_bug_report(
        self,
        workspace: str | Path,
        fix_tasks: list,
        attempt: int,
        status: str,
        details: str = "",
    ) -> str:
        """Generate a timestamped report of diagnosed software failures."""

        project_dir = self.workspace_manager._resolve_project_dir(
            workspace
        )

        report_dir = project_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc)

        history_number = self._next_report_number(
            report_dir,
            "bug_report",
        )

        report_name = f"bug_report_{history_number:03d}.md"

        task_sections = []

        for index, task in enumerate(fix_tasks, start=1):
            task_data = (
                task.model_dump()
                if hasattr(task, "model_dump")
                else task
            )

            task_sections.append(
                f"""### Bug {index}

- **File:** {task_data.get("filename", "Unknown")}
- **Priority:** {task_data.get("priority", "Unknown")}
- **Error:** {task_data.get("error_summary", "Not specified")}
- **Root cause:** {task_data.get("root_cause", "Not specified")}
- **Related test:** {task_data.get("related_test", "Not specified")}

**Correction instructions:**

{task_data.get("correction_instructions", "Not specified")}
"""
            )

        report = f"""# CodePilot Bug Report

## Summary

- **Date (UTC):** {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
- **Correction attempt:** {attempt}
- **Workflow status:** {status}
- **Diagnosed issues:** {len(fix_tasks)}

## Diagnosed Issues

{"".join(task_sections) if task_sections else "No structured bugs were diagnosed."}

## Additional Details

{details or "None"}
"""

        self.workspace_manager.write_file(
            workspace,
            f"reports/{report_name}",
            report,
        )

        self.workspace_manager.write_file(
            workspace,
            "reports/bug_report.md",
            report,
            overwrite=True,
        )

        return f"reports/{report_name}"
