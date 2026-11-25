
import json
import re

from core.base_agent import BaseAgent
from core.llm_client import LLMClient
from schemas.implementation_plan import ImplementationPlan


class PlannerAgent(BaseAgent):
    """Creates validated implementation plans from technical documents."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            name="Planner Agent",
            role="Software Implementation Planning",
            llm_client=llm_client,
            description=(
                "Converts software requirements and architecture "
                "into an ordered, dependency-aware implementation plan."
            ),
        )

    @property
    def system_prompt(self) -> str:
        return """
You are the Planner Agent in CodePilot, an Agentic Software Factory.

Create a structured implementation plan using the supplied
requirements and architecture documents.

RULES:
1. Treat supplied documents as the source of truth.
2. Do not invent confirmed features or requirements.
3. Mark recommended implementation decisions as recommendations.
4. Break the project into clear, actionable development tasks.
5. Give every task a unique ID such as TASK-001.
6. Assign priority: high, medium, or low.
7. Include dependencies using existing task IDs only.
8. Include measurable completion criteria for every task.
9. Ensure dependencies are logically correct.
10. Ensure execution_order respects all dependencies.
11. Include every task exactly once in execution_order.
12. Do not create circular dependencies.

OUTPUT:
Return ONLY valid JSON.

Required structure:
{
  "project_name": "Project name",
  "summary": "Implementation plan summary",
  "tasks": [
    {
      "task_id": "TASK-001",
      "title": "Task title",
      "description": "Detailed description",
      "priority": "high",
      "dependencies": [],
      "completion_criteria": [
        "A clear completion condition"
      ]
    }
  ],
  "execution_order": ["TASK-001"]
}

Do not use Markdown code fences.
Do not include explanations outside the JSON.
"""

    def generate_plan(
        self,
        requirements: str,
        architecture: str,
    ) -> dict:
        """Generate and validate a dependency-aware implementation plan."""

        if not isinstance(requirements, str) or not requirements.strip():
            raise ValueError("Requirements document cannot be empty.")

        if not isinstance(architecture, str) or not architecture.strip():
            raise ValueError("Architecture document cannot be empty.")

        user_prompt = f"""
Create the implementation plan using these two documents.

SOFTWARE REQUIREMENTS:
{requirements.strip()}

SYSTEM ARCHITECTURE:
{architecture.strip()}

Return the complete implementation plan as valid JSON.
"""

        result = self.run(user_prompt)

        # Extract JSON if the model unexpectedly adds code fences.
        cleaned = result.strip()
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            plan_data = json.loads(cleaned)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Planner Agent returned invalid JSON: {error}"
            ) from error

        try:
            validated_plan = ImplementationPlan.model_validate(plan_data)
        except Exception as error:
            raise RuntimeError(
                f"Planner Agent returned an invalid implementation plan: {error}"
            ) from error

        return validated_plan.model_dump(mode="json")
