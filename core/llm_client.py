
from openai import OpenAI

from config.settings import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)


class LLMClient:
    """Shared AI client for all specialized CodePilot agents."""

    def __init__(self):
        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is missing. "
                "Check your project .env file."
            )

        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            timeout=120.0,
            max_retries=0,
        )
        self.model = OPENROUTER_MODEL

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 8000,
    ) -> str:
        """Generate a response while disabling unnecessary model reasoning."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={
                    "reasoning": {
                        "enabled": False
                    }
                },
            )

            if not response.choices:
                raise RuntimeError(
                    f"The AI model {self.model} returned no response choices."
                )

            choice = response.choices[0]
            content = choice.message.content

            if getattr(choice, "finish_reason", None) == "length":
                usage = getattr(response, "usage", None)
                completion_tokens = (
                    getattr(usage, "completion_tokens", "unknown")
                    if usage else "unknown"
                )
                raise RuntimeError(
                    "The AI response was truncated.\n"
                    f"Model: {self.model}\n"
                    f"Requested max_tokens: {max_tokens}\n"
                    f"Completion tokens: {completion_tokens}\n"
                    f"Response ID: {getattr(response, 'id', 'unknown')}"
                )

            if isinstance(content, list):
                content = "".join(
                    item.text
                    for item in content
                    if getattr(item, "text", None)
                )

            if not isinstance(content, str) or not content.strip():
                raise RuntimeError(
                    f"The AI model {self.model} returned no usable text. "
                    f"Finish reason: {getattr(choice, 'finish_reason', None)}."
                )

            return content.strip()

        except Exception as error:
            if isinstance(error, RuntimeError):
                raise
            raise RuntimeError(
                f"LLM request failed: {type(error).__name__}: {error}"
            ) from error
