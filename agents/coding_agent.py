
import hashlib
import json
import re
from pathlib import Path

from core.approval_manager import ApprovalManager
from core.base_agent import BaseAgent
from core.llm_client import LLMClient
from schemas.agent_response import AgentResponse, AgentStatus
from schemas.fix_task import FixTask
from schemas.implementation_plan import ImplementationPlan
from services.project1_adapter import Project1Adapter
from services.workspace_manager import WorkspaceManager


class CodingAgent(BaseAgent):
    """Generates project files and applies approved code corrections."""

    def __init__(
        self,
        llm_client: LLMClient,
        project1_adapter: Project1Adapter | None = None,
        workspace_manager: WorkspaceManager | None = None,
        approval_manager: ApprovalManager | None = None,
    ):
        super().__init__(
            name="Coding Agent",
            role="Software Code Generation and Correction",
            llm_client=llm_client,
            description=(
                "Generates application source files using Project 1 "
                "and applies human-approved code corrections."
            ),
        )

        self.workspace_manager = (
            workspace_manager or WorkspaceManager()
        )

        self.project1_adapter = (
            project1_adapter
            or Project1Adapter(
                llm_client=llm_client,
                workspace_manager=self.workspace_manager,
            )
        )

        self.approval_manager = (
            approval_manager or ApprovalManager()
        )

    @property
    def system_prompt(self) -> str:
        return """
You are the Coding Agent in CodePilot, an Agentic Software Factory.

Your responsibility is to implement individual software development tasks.

RULES:
1. Follow the supplied requirements and architecture.
2. Implement only the requested task.
3. Produce complete, executable Python source code.
4. Preserve compatibility with existing project files.
5. Use clear names, modular design and appropriate error handling.
6. Do not create unnecessary files or features.
7. Do not include Markdown code fences.
8. Return Python source code only.
9. Never claim that code was saved or executed.
"""

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
        return slug.strip("_").lower() or "task"

    def _get_plan(
        self,
        implementation_plan: dict | ImplementationPlan,
    ) -> ImplementationPlan:
        if isinstance(implementation_plan, ImplementationPlan):
            return implementation_plan

        if isinstance(implementation_plan, dict):
            return ImplementationPlan.model_validate(
                implementation_plan
            )

        raise ValueError(
            "Implementation plan must be a dictionary or "
            "ImplementationPlan object."
        )

    def _get_fix_task(self, fix_task: FixTask | dict) -> FixTask:
        if isinstance(fix_task, FixTask):
            return fix_task

        if isinstance(fix_task, dict):
            return FixTask.model_validate(fix_task)

        raise ValueError(
            "Fix task must be a FixTask object or dictionary."
        )

    def _validate_fix_file(self, workspace, filename):
        project_dir = self.workspace_manager._resolve_project_dir(
            workspace
        )

        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Filename cannot be empty.")

        if Path(filename).suffix.lower() != ".py":
            raise ValueError("Only Python files can be corrected.")

        file_path = self.workspace_manager._resolve_file_path(
            project_dir,
            filename,
        )

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Correction target does not exist: {filename}"
            )

        return project_dir, file_path

    def request_fix_approval(
        self,
        workspace,
        fix_task: FixTask | dict,
    ):
        """Request human approval before modifying a project file."""

        task = self._get_fix_task(fix_task)

        project_dir, file_path = self._validate_fix_file(
            workspace,
            task.filename,
        )

        original_code = file_path.read_text(encoding="utf-8")

        details = {
            "filename": task.filename,
            "error_summary": task.error_summary,
            "root_cause": task.root_cause,
            "correction_instructions": task.correction_instructions,
            "original_sha256": hashlib.sha256(
                original_code.encode("utf-8")
            ).hexdigest(),
        }

        request = self.approval_manager.request_approval(
            action="apply_code_fix",
            details=json.dumps(details, indent=2),
            resource=str(file_path),
        )

        return request

    def apply_fix_task(
        self,
        workspace,
        fix_task: FixTask | dict,
        approval_id: str,
    ) -> AgentResponse:
        """Apply a correction only after verifying human approval."""

        try:
            task = self._get_fix_task(fix_task)

            project_dir, file_path = self._validate_fix_file(
                workspace,
                task.filename,
            )

            request = self.approval_manager.get_request(approval_id)

            if request.action != "apply_code_fix":
                raise PermissionError(
                    "Approval is not valid for code correction."
                )

            if request.resource != str(file_path):
                raise PermissionError(
                    "Approval does not match the requested file."
                )

            if not self.approval_manager.is_approved(approval_id):
                raise PermissionError(
                    "Human approval is required before modifying code."
                )

            approval_details = json.loads(request.details)

            original_code = file_path.read_text(encoding="utf-8")

            current_hash = hashlib.sha256(
                original_code.encode("utf-8")
            ).hexdigest()

            if current_hash != approval_details["original_sha256"]:
                raise RuntimeError(
                    "The source file changed after approval was requested. "
                    "Request approval again before applying the fix."
                )

            error_context = f"""
ERROR SUMMARY:
{task.error_summary}

ROOT CAUSE:
{task.root_cause}

REQUIRED CORRECTION:
{task.correction_instructions}

RELATED TEST:
{task.related_test or "Not specified"}
"""

            error_analysis = self.project1_adapter.analyse_error(
                original_code,
                error_context,
            )

            corrected_code = self.project1_adapter.fix_code(
                original_code,
                error_analysis,
            )

            self.workspace_manager.validate_python_code(
                corrected_code
            )

            saved_path = self.workspace_manager.write_file(
                project_dir,
                task.filename,
                corrected_code,
                overwrite=True,
            )

            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output=f"Approved correction applied to {task.filename}.",
                metadata={
                    "filename": task.filename,
                    "corrected_file": str(saved_path),
                    "approval_id": approval_id,
                    "approval_verified": True,
                    "syntax_validated": True,
                    "file_modified": True,
                },
            )

        except Exception as error:
            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=f"{type(error).__name__}: {error}",
                metadata={
                    "approval_id": approval_id,
                    "file_modified": False,
                },
            )

    def generate_project(
        self,
        project_name: str,
        requirements: str,
        architecture: str,
        implementation_plan: dict | ImplementationPlan,
        workspace: Path | str,
    ) -> AgentResponse:
        """Generate project files in dependency-aware task order."""

        try:
            if not isinstance(project_name, str) or not project_name.strip():
                raise ValueError("Project name cannot be empty.")

            if not isinstance(requirements, str) or not requirements.strip():
                raise ValueError("Requirements cannot be empty.")

            if not isinstance(architecture, str) or not architecture.strip():
                raise ValueError("Architecture cannot be empty.")

            project_dir = (
                self.workspace_manager._resolve_project_dir(workspace)
            )

            plan = self._get_plan(implementation_plan)

            if plan.project_name.strip() != project_name.strip():
                raise ValueError(
                    "Project name does not match implementation plan."
                )

            tasks_by_id = {
                task.task_id: task
                for task in plan.tasks
            }

            completed_tasks = []
            generated_files = []
            failed_tasks = []

            for task_id in plan.execution_order:
                task = tasks_by_id[task_id]

                missing_dependencies = [
                    dependency
                    for dependency in task.dependencies
                    if dependency not in completed_tasks
                ]

                if missing_dependencies:
                    failed_tasks.append({
                        "task_id": task_id,
                        "error": (
                            "Dependencies not completed: "
                            + ", ".join(missing_dependencies)
                        ),
                    })
                    break

                filename = (
                    f"{self._slug(task.task_id)}_"
                    f"{self._slug(task.title)}.py"
                )

                task_prompt = f"""
PROJECT NAME:
{project_name}

SOFTWARE REQUIREMENTS:
{requirements}

SYSTEM ARCHITECTURE:
{architecture}

CURRENT IMPLEMENTATION TASK:
Task ID: {task.task_id}
Title: {task.title}
Priority: {task.priority.value}

Description:
{task.description}

Completion Criteria:
{chr(10).join('- ' + item for item in task.completion_criteria)}

COMPLETED TASKS:
{', '.join(completed_tasks) if completed_tasks else 'None'}

EXISTING PROJECT FILES:
{self.workspace_manager.get_project_context(project_dir)}

IMPLEMENTATION INSTRUCTIONS:
Generate the complete Python source code for this task.

Target filename: {filename}

If other generated modules are required, import them using their
actual filenames and available interfaces.

Do not regenerate unrelated files.
Return Python source code only.
"""

                try:
                    generated_code = self.project1_adapter.generate_code(
                        task_prompt,
                        project_dir,
                    )

                    self.workspace_manager.validate_python_code(
                        generated_code
                    )

                    saved_path = self.workspace_manager.write_file(
                        project_dir,
                        filename,
                        generated_code,
                        overwrite=True,
                    )

                    generated_files.append(
                        saved_path.relative_to(project_dir).as_posix()
                    )

                    completed_tasks.append(task_id)

                except Exception as error:
                    failed_tasks.append({
                        "task_id": task_id,
                        "error": f"{type(error).__name__}: {error}",
                    })
                    break

            success = (
                len(completed_tasks) == len(plan.tasks)
                and not failed_tasks
            )

            if success:
                summary = (
                    f"Successfully generated {len(generated_files)} "
                    f"files for {project_name}."
                )
                status = AgentStatus.SUCCESS
            else:
                summary = (
                    f"Generated {len(generated_files)} files. "
                    f"{len(failed_tasks)} task(s) failed."
                )
                status = AgentStatus.FAILED

            return AgentResponse(
                agent_name=self.name,
                status=status,
                output=summary,
                error=(
                    str(failed_tasks)
                    if failed_tasks
                    else None
                ),
                metadata={
                    "project_name": project_name,
                    "workspace": str(project_dir),
                    "completed_tasks": completed_tasks,
                    "generated_files": generated_files,
                    "failed_tasks": failed_tasks,
                    "execution_order": plan.execution_order,
                    "execution_performed": False,
                },
            )

        except Exception as error:
            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=f"{type(error).__name__}: {error}",
                metadata={
                    "generated_files": [],
                    "execution_performed": False,
                },
            )
