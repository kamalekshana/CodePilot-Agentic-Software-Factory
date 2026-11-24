
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Task(BaseModel):
    """Represents an individual task assigned to an agent."""

    task_id: str
    agent_name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING

    depends_on: list[str] = Field(default_factory=list)

    input_data: str = ""
    output_data: str = ""
    error: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
