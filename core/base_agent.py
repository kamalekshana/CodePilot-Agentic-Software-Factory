
from abc import ABC, abstractmethod

from core.llm_client import LLMClient


class BaseAgent(ABC):
    """Common foundation for all specialized CodePilot agents."""

    def __init__(
        self,
        name: str,
        role: str,
        llm_client: LLMClient,
    ):
        self.name = name
        self.role = role
        self.llm_client = llm_client

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Each specialized agent must define its own system prompt."""
        pass

    def run(self, task_input: str) -> str:
        """Execute the agent's task using the shared LLM client."""

        if not isinstance(task_input, str) or not task_input.strip():
            raise ValueError("Agent task input cannot be empty.")

        return self.llm_client.generate_response(
            system_prompt=self.system_prompt,
            user_prompt=task_input,
        )

    def get_info(self) -> dict:
        """Return basic information about this agent."""

        return {
            "name": self.name,
            "role": self.role,
        }
