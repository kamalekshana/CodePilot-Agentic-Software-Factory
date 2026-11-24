
from abc import ABC, abstractmethod

from core.llm_client import LLMClient
from schemas.agent_response import AgentResponse, AgentStatus


class BaseAgent(ABC):
    """Reusable foundation for all specialized CodePilot agents."""

    def __init__(
        self,
        name: str,
        role: str,
        llm_client: LLMClient,
        description: str = "",
    ):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Agent name cannot be empty.")

        if not isinstance(role, str) or not role.strip():
            raise ValueError("Agent role cannot be empty.")

        if llm_client is None:
            raise ValueError("An LLM client must be provided.")

        self.name = name
        self.role = role
        self.description = description
        self.llm_client = llm_client

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Each specialized agent must define its own system prompt."""
        pass

    def execute(self, task_input: str) -> AgentResponse:
        """Execute a task and return a standardized response."""

        if not isinstance(task_input, str) or not task_input.strip():
            raise ValueError("Agent task input cannot be empty.")

        try:
            prompt = self.system_prompt

            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("Agent system prompt cannot be empty.")

            result = self.llm_client.generate_response(
                system_prompt=prompt,
                user_prompt=task_input,
            )

            if not isinstance(result, str) or not result.strip():
                raise RuntimeError("The LLM returned an empty response.")

            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output=result.strip(),
            )

        except Exception as error:
            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=f"{type(error).__name__}: {error}",
            )

    def run(self, task_input: str) -> str:
        """Execute a task and return its plain-text output."""

        response = self.execute(task_input)

        if response.status == AgentStatus.FAILED:
            raise RuntimeError(response.error)

        return response.output

    def get_info(self) -> dict:
        """Return basic information about this agent."""

        return {
            "name": self.name,
            "role": self.role,
            "description": self.description,
        }
