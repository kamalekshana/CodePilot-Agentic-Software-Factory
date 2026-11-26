
import re
from pathlib import Path
from typing import Any

from core.base_agent import BaseAgent
from core.llm_client import LLMClient
from schemas.agent_response import AgentResponse, AgentStatus
from schemas.implementation_plan import ImplementationPlan
from services.project1_adapter import Project1Adapter
from services.workspace_manager import WorkspaceManager


class CodingAgent(BaseAgent):
    """Generates project files using Project 1 through Project 2."""

    def __init__(
        self,
        llm_client: LLMClient,
        project1_adapter: Project1Adapter | None = None,
        workspace_manager: WorkspaceManager | None = None,
    ):
        super().__init__(
            name="Coding Agent",
            role="Software Code Generation",
            llm_client=llm_client,
            description=(
                "Generates application source files from validated "
                "implementation plans using Project 1's coding engine."
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
        """Convert task information into a safe filename component."""
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
        return slug.strip("_").lower() or "task"

    def _get_plan(
        self,
        implementation_plan: dict | ImplementationPlan,
    ) -> ImplementationPlan:
        """Convert and validate incoming implementation plan."""
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
