
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class AgentResponse(BaseModel):
    """Standard response returned by every CodePilot agent."""

    agent_name: str
    status: AgentStatus
    output: str = ""
    error: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
