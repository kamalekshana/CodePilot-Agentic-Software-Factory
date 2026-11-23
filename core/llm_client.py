
from openai import OpenAI

from config.settings import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)


class LLMClient:
    """Shared AI client for all CodePilot agents."""

    def __init__(self):
        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is missing. "
                "Check your project .env file."
            )

        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            timeout=30.0,
            max_retries=0,
        )

        self.model = OPENROUTER_MODEL

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        """Send prompts to the configured model and return its response."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            message = response.choices[0].message
            content = message.content

            if isinstance(content, list):
                content = "".join(
                    item.text
                    for item in content
                    if getattr(item, "text", None)
                )

            if not content:
                content = getattr(message, "reasoning", None)

            if not content:
                raise RuntimeError(
                    "The AI model returned neither text nor reasoning."
                )

            return content.strip()

        except Exception as error:
            raise RuntimeError(
                f"LLM request failed: {type(error).__name__}: {error}"
            ) from error
