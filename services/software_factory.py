
from core.llm_client import LLMClient
from services.planning_workflow import PlanningWorkflow
from services.coding_workflow import CodingWorkflow


class SoftwareFactory:
    """Runs the complete planning-to-code-generation pipeline."""

    def __init__(self, llm_client: LLMClient):
        self.planning_workflow = (
            PlanningWorkflow.from_llm_client(llm_client)
        )
        self.coding_workflow = (
            CodingWorkflow.from_llm_client(llm_client)
        )

    def run(self, project_name: str, user_request: str) -> dict:
        print("\n========== CODEPILOT SOFTWARE FACTORY ==========")

        planning_result = self.planning_workflow.run(
            project_name=project_name,
            user_request=user_request,
        )

        coding_result = self.coding_workflow.run(planning_result)

        return {
            "project_name": project_name,
            "project_directory": planning_result["project_directory"],
            "planning_result": planning_result,
            "coding_result": coding_result,
            "generated_files": coding_result.metadata.get(
                "generated_files", []
            ),
            "success": coding_result.status.value == "success",
        }
