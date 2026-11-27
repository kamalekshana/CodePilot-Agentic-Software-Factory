
import json

from core.base_agent import BaseAgent
from core.llm_client import LLMClient
from schemas.agent_response import AgentResponse, AgentStatus
from schemas.fix_task import FixTask


class DebuggingAgent(BaseAgent):
    """Analyses software failures and creates structured correction tasks."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            name="Debugging Agent",
            role="Software Error Analysis and Correction Planning",
            llm_client=llm_client,
            description=(
                "Analyses test failures, identifies root causes, "
                "and prepares structured correction tasks."
            ),
        )

    @property
    def system_prompt(self) -> str:
        return """
You are the Debugging Agent in CodePilot.

Analyse the supplied source code and actual test failure information.

Your responsibilities:
1. Identify the exact file responsible for the failure.
2. Explain the likely root cause using the supplied evidence.
3. Provide precise correction instructions.
4. Identify the related failing test.
5. Assign high, medium, or low priority.

Return ONLY valid JSON using this structure:

{
  "filename": "example.py",
  "error_summary": "Short description of the failure",
  "root_cause": "Explanation of the underlying problem",
  "correction_instructions": "Specific instructions to fix it",
  "related_test": "Name of the failing test",
  "priority": "high"
}

Rules:
- Do not invent test results or error messages.
- Do not claim that a correction has been applied.
- Use the exact filename supplied in the project context.
- Do not return Markdown code fences.
- If the evidence is insufficient, explain that in the root_cause.
"""

    def create_fix_task(
        self,
        filename: str,
        source_code: str,
        test_report: str,
        error_details: str = "",
    ) -> AgentResponse:
        """Analyse a failure and return a validated FixTask."""

        try:
            if not filename or not filename.strip():
                raise ValueError("Filename cannot be empty.")

            if not source_code or not source_code.strip():
                raise ValueError("Source code cannot be empty.")

            if not test_report or not test_report.strip():
                raise ValueError("Test report cannot be empty.")

            prompt = f"""
FAILED FILE:
{filename}

SOURCE CODE:
{source_code}

TEST REPORT:
{test_report}

ADDITIONAL ERROR DETAILS:
{error_details or "None supplied"}

Analyse this failure and create one structured correction task.
"""

            response = self.run(prompt)

            # Handle accidental Markdown fences.
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3].strip()

            data = json.loads(cleaned)
            fix_task = FixTask.model_validate(data)

            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output=fix_task.model_dump_json(indent=2),
                metadata={
                    "fix_task": fix_task.model_dump(),
                    "analysis_completed": True,
                },
            )

        except Exception as error:
            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=f"{type(error).__name__}: {error}",
                metadata={"analysis_completed": False},
            )


DebuggingAgent.__test__ = False
