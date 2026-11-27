
"""Orchestrate testing, debugging and approved autonomous corrections."""

from pathlib import Path

from agents.debugging_agent import DebuggingAgent
from agents.testing_agent import TestingAgent
from core.approval_manager import ApprovalManager
from schemas.agent_response import AgentStatus
from services.report_generator import ReportGenerator
from services.workspace_manager import WorkspaceManager


class DebuggingWorkflow:
    """Run a stateful test-and-fix loop with human approval."""

    def __init__(
        self,
        llm_client,
        coding_agent,
        workspace_manager=None,
        approval_manager=None,
        testing_agent=None,
        debugging_agent=None,
        max_retries=2,
    ):
        self.workspace_manager = workspace_manager or WorkspaceManager()
        self.approval_manager = approval_manager or ApprovalManager()
        self.coding_agent = coding_agent
        self.coding_agent.approval_manager = self.approval_manager

        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer.")

        self.max_retries = min(max_retries, 2)

        self.testing_agent = testing_agent or TestingAgent(
            llm_client=llm_client,
            workspace_manager=self.workspace_manager,
        )

        self.testing_agent.test_runner.approval_manager = (
            self.approval_manager
        )

        self.debugging_agent = debugging_agent or DebuggingAgent(
            llm_client=llm_client
        )

        self.report_generator = ReportGenerator(
            self.workspace_manager
        )

        # In-memory workflow state, keyed by approval request ID.
        self._runs = {}

    def _request_test_approval(self, workspace, test_paths=None):
        return self.testing_agent.request_test_approval(
            workspace,
            test_paths,
        )

    def _store_state(self, approval_id, state):
        self._runs[approval_id] = state

    def _get_state(self, approval_id):
        state = self._runs.get(approval_id)

        if state is None:
            raise KeyError(
                "Workflow state was not found. "
                "Start a new debugging workflow."
            )

        return state

    def _request_next_test(self, state):
        request = self._request_test_approval(
            state["workspace"],
            state["test_paths"],
        )

        state["status"] = "approval_pending"
        state["pending_action"] = "run_tests"
        state["pending_test_approval_id"] = request.approval_id

        self._store_state(request.approval_id, state)

        return {
            "status": state["status"],
            "approval_id": request.approval_id,
            "message": "Approve the test execution to continue.",
        }

    def start(self, workspace, test_paths=None):
        """Start the workflow and request approval for initial tests."""

        project_dir = self.workspace_manager._resolve_project_dir(
            workspace
        )

        state = {
            "workspace": str(project_dir),
            "test_paths": test_paths,
            "attempts": 0,
            "max_retries": self.max_retries,
            "test_history": [],
            "fix_history": [],
            "status": "running",
            "pending_action": None,
        }

        return self._request_next_test(state)

    def continue_after_test_approval(self, approval_id):
        """Execute an approved test run and process its result."""

        state = self._get_state(approval_id)

        if state.get("pending_test_approval_id") != approval_id:
            raise PermissionError("This test approval is not current.")

        request = self.approval_manager.get_request(approval_id)

        if request.action != "run_tests":
            raise PermissionError("Invalid test approval action.")

        if request.resource != state["workspace"]:
            raise PermissionError("Test approval belongs to another project.")

        if not self.approval_manager.is_approved(approval_id):
            return {
                "status": "approval_pending",
                "approval_id": approval_id,
            }

        response = self.testing_agent.run_project_tests(
            workspace=state["workspace"],
            approval_id=approval_id,
            test_paths=state["test_paths"],
        )

        if response.status != AgentStatus.SUCCESS:
            state["status"] = "execution_error"
            state["error"] = response.error
            state["pending_action"] = None
            return state

        metadata = response.metadata
        state["test_history"].append(metadata)

        execution_status = metadata.get("execution_status")

        if execution_status == "passed":
            state["status"] = "passed"
            state["pending_action"] = None
            state["final_test_result"] = metadata
            return state

        if execution_status != "failed":
            state["status"] = execution_status or "execution_error"
            state["pending_action"] = None
            state["final_test_result"] = metadata
            return state

        if state["attempts"] >= self.max_retries:
            state["status"] = "failed"
            state["pending_action"] = None
            state["error"] = "Maximum correction attempts reached."
            return state

        return self._prepare_correction(state, response)

    def _prepare_correction(self, state, test_response):
        """Diagnose a failure and request approval for its correction."""

        workspace = state["workspace"]
        metadata = test_response.metadata
        report_path = metadata.get("report_path")

        report = self.workspace_manager.read_file(
            workspace,
            report_path,
        )

        files = self.workspace_manager.list_files(workspace)

        source_files = [
            filename for filename in files
            if filename.endswith(".py")
            and not Path(filename).name.startswith("test_")
            and not Path(filename).name.endswith("_test.py")
        ]

        if not source_files:
            state["status"] = "debugging_failed"
            state["error"] = "No Python source files available."
            return state

        # Initial implementation: analyse the first available source file.
        filename = source_files[0]

        source_code = self.workspace_manager.read_file(
            workspace,
            filename,
        )

        error_details = (
            f"TEST ANALYSIS:\n{test_response.output}\n\n"
            f"TEST METADATA:\n{metadata}"
        )

        response = self.debugging_agent.create_fix_task(
            filename=filename,
            source_code=source_code,
            test_report=report,
            error_details=error_details,
        )

        if response.status != AgentStatus.SUCCESS:
            state["status"] = "debugging_failed"
            state["error"] = response.error
            return state

        fix_task = response.metadata["fix_task"]

        next_attempt = state["attempts"] + 1

        bug_report = self.report_generator.generate_bug_report(
            workspace=workspace,
            fix_tasks=[fix_task],
            attempt=next_attempt,
            status="approval_pending",
            details=test_response.output,
        )

        approval = self.coding_agent.request_fix_approval(
            workspace,
            fix_task,
        )

        state["status"] = "approval_pending"
        state["pending_action"] = "apply_fix"
        state["attempts"] = next_attempt
        state["pending_fix"] = fix_task
        state["pending_fix_approval_id"] = approval.approval_id
        state["bug_report"] = bug_report

        self._store_state(approval.approval_id, state)

        return {
            "status": "approval_pending",
            "pending_action": "apply_fix",
            "approval_id": approval.approval_id,
            "fix_task": fix_task,
            "attempt": next_attempt,
            "bug_report": bug_report,
        }

    def continue_after_fix_approval(self, approval_id):
        """Apply an approved correction and request another test run."""

        state = self._get_state(approval_id)

        if state.get("pending_fix_approval_id") != approval_id:
            raise PermissionError("This correction approval is not current.")

        if state.get("pending_action") != "apply_fix":
            raise PermissionError("No correction is awaiting approval.")

        request = self.approval_manager.get_request(approval_id)

        if request.action != "apply_code_fix":
            raise PermissionError("Invalid correction approval action.")

        if not self.approval_manager.is_approved(approval_id):
            return {
                "status": "approval_pending",
                "approval_id": approval_id,
            }

        result = self.coding_agent.apply_fix_task(
            workspace=state["workspace"],
            fix_task=state["pending_fix"],
            approval_id=approval_id,
        )

        state["fix_history"].append({
            "attempt": state["attempts"],
            "approval_id": approval_id,
            "result": result.metadata,
            "status": result.status.value,
        })

        if result.status != AgentStatus.SUCCESS:
            state["status"] = "correction_failed"
            state["error"] = result.error
            state["pending_action"] = None
            return state

        state["pending_fix"] = None
        state["pending_fix_approval_id"] = None

        # Request approval for the next test execution.
        return self._request_next_test(state)

    def run(self, workspace, test_paths=None):
        """Compatibility alias for starting the workflow."""

        return self.start(workspace, test_paths)
