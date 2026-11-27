
"""Testing Agent for CodePilot's generated software projects."""

from pathlib import Path

from core.base_agent import BaseAgent
from core.llm_client import LLMClient
from schemas.agent_response import AgentResponse, AgentStatus
from services.report_generator import ReportGenerator
from services.workspace_manager import WorkspaceManager
from tools.test_runner import TestRunner


class TestingAgent(BaseAgent):
    """Inspects generated projects and coordinates approved pytest runs."""

    def __init__(
        self,
        llm_client: LLMClient,
        workspace_manager: WorkspaceManager | None = None,
        test_runner: TestRunner | None = None,
        report_generator: ReportGenerator | None = None,
    ):
        super().__init__(
            name="Testing Agent",
            role="Software Testing and Quality Assurance",
            llm_client=llm_client,
            description=(
                "Inspects generated software, coordinates pytest execution, "
                "and produces factual test reports."
            ),
        )

        self.workspace_manager = (
            workspace_manager or WorkspaceManager()
        )
        self.test_runner = test_runner or TestRunner(
            workspace_manager=self.workspace_manager
        )
        self.report_generator = report_generator or ReportGenerator(
            workspace_manager=self.workspace_manager
        )

    @property
    def system_prompt(self) -> str:
        return """
You are the Testing Agent in CodePilot, an Agentic Software Factory.

Analyse the supplied generated-project file inventory and actual test
execution results.

RULES:
1. Treat execution results as the source of truth.
2. Never claim a test passed unless the test runner confirms it.
3. Identify failed tests and execution errors separately.
4. Identify missing test coverage and potential quality risks.
5. Recommend practical additional tests.
6. Do not invent test counts, files, or execution results.

Return a concise Markdown analysis.
"""

    def inspect_project(self, workspace: str | Path) -> dict:
        """Inspect project files and identify existing pytest test files."""

        project_dir = self.workspace_manager._resolve_project_dir(
            workspace
        )

        files = self.workspace_manager.list_files(workspace)

        python_files = [
            filename for filename in files
            if filename.endswith(".py")
        ]

        test_files = [
            filename for filename in python_files
            if Path(filename).name.startswith("test_")
            or Path(filename).name.endswith("_test.py")
        ]

        return {
            "project_directory": str(project_dir),
            "files": files,
            "python_files": python_files,
            "test_files": test_files,
            "has_tests": bool(test_files),
        }

    def run_project_tests(
        self,
        workspace: str | Path,
        approval_id: str,
        test_paths: list[str] | None = None,
    ) -> AgentResponse:
        """Inspect, execute approved tests, and generate a report."""

        try:
            inventory = self.inspect_project(workspace)

            result = self.test_runner.run_tests(
                workspace=workspace,
                approval_id=approval_id,
                test_paths=test_paths,
            )

            report_path = self.report_generator.generate_test_report(
                workspace,
                result,
            )

            analysis_prompt = f"""
PROJECT FILE INVENTORY:
{inventory}

ACTUAL PYTEST RESULT:
{result.to_dict()}

TEST REPORT:
{report_path}

Analyse the results. Separate confirmed failures from possible
coverage gaps. Do not invent results.
"""

            analysis = self.run(analysis_prompt)

            output = (
                f"## Test Execution\n\n"
                f"- Status: {result.status}\n"
                f"- Total: {result.total}\n"
                f"- Passed: {result.passed}\n"
                f"- Failed: {result.failed}\n"
                f"- Errors: {result.errors}\n"
                f"- Skipped: {result.skipped}\n"
                f"- Report: {report_path}\n\n"
                f"## Testing Analysis\n\n{analysis}"
            )

            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output=output,
                metadata={
                    "execution_status": result.status,
                    "total": result.total,
                    "passed": result.passed,
                    "failed": result.failed,
                    "errors": result.errors,
                    "skipped": result.skipped,
                    "report_path": report_path,
                    "test_files": inventory["test_files"],
                },
            )

        except Exception as error:
            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=f"{type(error).__name__}: {error}",
                metadata={
                    "execution_status": "agent_error",
                },
            )

    def request_test_approval(
        self,
        workspace: str | Path,
        test_paths: list[str] | None = None,
    ):
        """Create a pending human approval request."""

        return self.test_runner.request_test_approval(
            workspace,
            test_paths,
        )
TestingAgent.__test__ = False