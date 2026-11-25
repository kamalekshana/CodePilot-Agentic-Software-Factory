
import json
import re
import time
from pathlib import Path

from config.settings import WORKSPACE_DIR


class PlanningWorkflow:
    """Runs the sequential CodePilot planning pipeline."""

    def __init__(
        self,
        requirements_agent,
        architect_agent,
        planner_agent,
        workspace_dir: Path | str = WORKSPACE_DIR,
    ):
        self.requirements_agent = requirements_agent
        self.architect_agent = architect_agent
        self.planner_agent = planner_agent
        self.workspace_dir = Path(workspace_dir).resolve()

    @classmethod
    def from_llm_client(cls, llm_client, workspace_dir=WORKSPACE_DIR):
        from agents.requirements_agent import RequirementsAgent
        from agents.architect_agent import ArchitectAgent
        from agents.planner_agent import PlannerAgent

        return cls(
            requirements_agent=RequirementsAgent(llm_client),
            architect_agent=ArchitectAgent(llm_client),
            planner_agent=PlannerAgent(llm_client),
            workspace_dir=workspace_dir,
        )

    def _run_stage(self, stage_name, operation):
        print(f"\n[{stage_name}] Running...", flush=True)
        started = time.perf_counter()

        try:
            result = operation()
        except Exception as error:
            elapsed = time.perf_counter() - started
            print(
                f"[{stage_name}] FAILED after {elapsed:.1f}s: {error}",
                flush=True,
            )
            raise RuntimeError(
                f"Planning workflow failed during {stage_name}: {error}"
            ) from error

        elapsed = time.perf_counter() - started
        print(
            f"[{stage_name}] Completed in {elapsed:.1f}s",
            flush=True,
        )
        return result

    def run(self, project_name: str, user_request: str) -> dict:
        if not project_name or not project_name.strip():
            raise ValueError("Project name cannot be empty.")

        if not user_request or not user_request.strip():
            raise ValueError("User request cannot be empty.")

        project_slug = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            project_name.strip(),
        ).strip("_")

        if not project_slug:
            raise ValueError("Project name must contain valid characters.")

        project_dir = (self.workspace_dir / project_slug).resolve()

        if not project_dir.is_relative_to(self.workspace_dir):
            raise ValueError("Invalid project directory.")

        project_dir.mkdir(parents=True, exist_ok=True)

        print("\nStarting CodePilot planning pipeline...", flush=True)

        # Stage 1
        requirements = self._run_stage(
            "Requirements Agent",
            lambda: self.requirements_agent.analyze_requirements(
                user_request
            ),
        )
        self._validate_text(requirements, "Requirements Agent")
        self._save_text(project_dir / "requirements.md", requirements)

        # Stage 2
        architecture = self._run_stage(
            "Architect Agent",
            lambda: self.architect_agent.generate_architecture(
                requirements
            ),
        )
        self._validate_text(architecture, "Architect Agent")
        self._save_text(project_dir / "architecture.md", architecture)

        # Stage 3
        database_design = self._run_stage(
            "Database Design",
            lambda: self.architect_agent.generate_database_design(
                requirements
            ),
        )
        self._validate_text(database_design, "Database Design")
        self._save_text(
            project_dir / "database_design.md",
            database_design,
        )

        # Stage 4
        implementation_plan = self._run_stage(
            "Planner Agent",
            lambda: self.planner_agent.generate_plan(
                requirements=requirements,
                architecture=architecture,
            ),
        )

        if not isinstance(implementation_plan, dict):
            raise ValueError("Planner Agent must return a dictionary.")

        self._save_json(
            project_dir / "implementation_plan.json",
            implementation_plan,
        )

        print("\nAll planning stages completed successfully!", flush=True)

        return {
            "project_name": project_name,
            "project_directory": str(project_dir),
            "requirements": requirements,
            "architecture": architecture,
            "database_design": database_design,
            "implementation_plan": implementation_plan,
            "artifacts": {
                "requirements": str(project_dir / "requirements.md"),
                "architecture": str(project_dir / "architecture.md"),
                "database_design": str(
                    project_dir / "database_design.md"
                ),
                "implementation_plan": str(
                    project_dir / "implementation_plan.json"
                ),
            },
        }

    @staticmethod
    def _validate_text(content, stage_name):
        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                f"{stage_name} returned empty or invalid output."
            )

    @staticmethod
    def _save_text(path: Path, content: str):
        path.write_text(content.strip() + "\n", encoding="utf-8")

    @staticmethod
    def _save_json(path: Path, content: dict):
        path.write_text(
            json.dumps(content, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
