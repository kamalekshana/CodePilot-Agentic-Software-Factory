
from pathlib import Path

from agents.coding_agent import CodingAgent
from core.llm_client import LLMClient
from schemas.agent_response import AgentStatus
from services.project1_adapter import Project1Adapter
from services.workspace_manager import WorkspaceManager


class CodingWorkflow:
    """Connects planning output to Project 1 code generation."""

    def __init__(
        self,
        coding_agent: CodingAgent,
        workspace_manager: WorkspaceManager,
    ):
        self.coding_agent = coding_agent
        self.workspace_manager = workspace_manager

    @classmethod
    def from_llm_client(cls, llm_client: LLMClient):
        workspace_manager = WorkspaceManager()
        adapter = Project1Adapter(
            llm_client=llm_client,
            workspace_manager=workspace_manager,
        )
        coding_agent = CodingAgent(
            llm_client=llm_client,
            project1_adapter=adapter,
            workspace_manager=workspace_manager,
        )
        return cls(coding_agent, workspace_manager)

    def run(self, planning_result: dict):
        """Generate source files from a completed planning result."""

        if not isinstance(planning_result, dict):
            raise ValueError("Planning result must be a dictionary.")

        required_fields = (
            "project_name",
            "project_directory",
            "requirements",
            "architecture",
            "implementation_plan",
        )

        for field in required_fields:
            if not planning_result.get(field):
                raise ValueError(f"Planning result is missing: {field}")

        project_name = planning_result["project_name"]
        workspace = self.workspace_manager._resolve_project_dir(
            Path(planning_result["project_directory"])
        )

        # Keep the user's project name canonical across workflow stages.
        # The Planner's generated name may contain an unnecessary suffix.
        implementation_plan = dict(
            planning_result["implementation_plan"]
        )
        implementation_plan["project_name"] = project_name

        print("\nStarting Coding Agent workflow...", flush=True)

        result = self.coding_agent.generate_project(
            project_name=project_name,
            requirements=planning_result["requirements"],
            architecture=planning_result["architecture"],
            implementation_plan=implementation_plan,
            workspace=workspace,
        )

        if result.status == AgentStatus.SUCCESS:
            print(
                f"\nCoding completed: "
                f"{len(result.metadata.get('generated_files', []))} files generated.",
                flush=True,
            )
        else:
            print(
                f"\nCoding workflow failed: {result.error}",
                flush=True,
            )

        return result
