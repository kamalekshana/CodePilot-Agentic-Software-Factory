
from types import SimpleNamespace

from agents.debugging_agent import DebuggingAgent
from core.approval_manager import ApprovalManager
from schemas.agent_response import AgentResponse, AgentStatus
from schemas.fix_task import FixTask
from services.debugging_workflow import DebuggingWorkflow
from services.workspace_manager import WorkspaceManager


class FakeTestingAgent:
    def __init__(self, results):
        self.results = list(results)
        self.test_runner = SimpleNamespace(approval_manager=None)

    def request_test_approval(self, workspace, test_paths=None):
        return self.test_runner.approval_manager.request_approval(
            action="run_tests",
            details="Integration test approval",
            resource=workspace,
        )

    def run_project_tests(self, workspace, approval_id, test_paths=None):
        execution_status = self.results.pop(0)

        return AgentResponse(
            agent_name="Testing Agent",
            status=AgentStatus.SUCCESS,
            output=f"Test execution: {execution_status}",
            metadata={
                "execution_status": execution_status,
                "total": 2,
                "passed": 2 if execution_status == "passed" else 1,
                "failed": 0 if execution_status == "passed" else 1,
                "errors": 0,
                "skipped": 0,
                "report_path": "reports/test_report.md",
                "test_files": ["test_main.py"],
            },
        )


class FakeDebuggingAgent:
    def create_fix_task(
        self, filename, source_code, test_report, error_details=""
    ):
        fix_task = FixTask(
            filename=filename,
            error_summary="A controlled test failure",
            root_cause="Incorrect application logic",
            correction_instructions="Correct the application logic.",
            related_test="test_main.py",
        )

        return AgentResponse(
            agent_name="Debugging Agent",
            status=AgentStatus.SUCCESS,
            output="Fix task created",
            metadata={"fix_task": fix_task},
        )


class FakeCodingAgent:
    def __init__(self):
        self.approval_manager = None
        self.applied_fixes = 0

    def request_fix_approval(self, workspace, fix_task):
        return self.approval_manager.request_approval(
            action="apply_code_fix",
            details="Approve integration-test correction",
            resource=f"{workspace}/{fix_task.filename}",
        )

    def apply_fix_task(self, workspace, fix_task, approval_id):
        self.applied_fixes += 1

        return AgentResponse(
            agent_name="Coding Agent",
            status=AgentStatus.SUCCESS,
            output="Correction applied",
            metadata={"filename": fix_task.filename},
        )


class FakeLLMClient:
    def generate_response(self, system_prompt, user_prompt):
        return "Test analysis completed."


def create_workflow(tmp_path, test_results, max_retries=2):
    workspace_manager = WorkspaceManager(tmp_path / "workspace")
    workspace = workspace_manager.create_workspace("integration-demo")

    workspace_manager.write_file(
        workspace,
        "main.py",
        "def calculate_total(price, quantity):\n"
        "    return price * quantity\n",
    )

    workspace_manager.write_file(
        workspace,
        "reports/test_report.md",
        "# Test Report\n\nOne controlled test failure.\n",
    )

    approval_manager = ApprovalManager()
    coding_agent = FakeCodingAgent()
    testing_agent = FakeTestingAgent(test_results)

    workflow = DebuggingWorkflow(
        llm_client=FakeLLMClient(),
        coding_agent=coding_agent,
        workspace_manager=workspace_manager,
        approval_manager=approval_manager,
        testing_agent=testing_agent,
        debugging_agent=FakeDebuggingAgent(),
        max_retries=max_retries,
    )

    return workflow, workspace, approval_manager, coding_agent


def test_workflow_completes_when_tests_pass(tmp_path):
    workflow, workspace, approvals, coding = create_workflow(
        tmp_path, ["passed"]
    )

    result = workflow.start(workspace)

    assert result["status"] == "approval_pending"

    approvals.approve(result["approval_id"])
    result = workflow.continue_after_test_approval(result["approval_id"])

    assert result["status"] == "passed"
    assert coding.applied_fixes == 0


def test_workflow_requests_approval_before_applying_fix(tmp_path):
    workflow, workspace, approvals, coding = create_workflow(
        tmp_path, ["failed", "passed"]
    )

    result = workflow.start(workspace)
    approvals.approve(result["approval_id"])

    result = workflow.continue_after_test_approval(result["approval_id"])

    assert result["status"] == "approval_pending"
    assert result["pending_action"] == "apply_fix"
    assert coding.applied_fixes == 0

    fix_approval_id = result["approval_id"]
    approvals.approve(fix_approval_id)

    result = workflow.continue_after_fix_approval(fix_approval_id)

    assert result["status"] == "approval_pending"
    assert approvals.get_request(result["approval_id"]).action == "run_tests"

    approvals.approve(result["approval_id"])
    result = workflow.continue_after_test_approval(result["approval_id"])

    assert result["status"] == "passed"
    assert coding.applied_fixes == 1


def test_workflow_stops_after_maximum_retries(tmp_path):
    workflow, workspace, approvals, coding = create_workflow(
        tmp_path, ["failed", "failed"], max_retries=1
    )

    result = workflow.start(workspace)
    approvals.approve(result["approval_id"])

    result = workflow.continue_after_test_approval(result["approval_id"])

    assert result["pending_action"] == "apply_fix"

    fix_approval_id = result["approval_id"]
    approvals.approve(fix_approval_id)

    result = workflow.continue_after_fix_approval(fix_approval_id)

    approvals.approve(result["approval_id"])
    result = workflow.continue_after_test_approval(result["approval_id"])

    assert result["status"] == "failed"
    assert result["attempts"] == 1
    assert coding.applied_fixes == 1
