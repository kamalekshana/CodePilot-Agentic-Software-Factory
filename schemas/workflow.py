
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from schemas.task import Task


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class Workflow(BaseModel):
    """Represents an end-to-end CodePilot project workflow."""

    workflow_id: str
    project_name: str
    user_request: str

    status: WorkflowStatus = WorkflowStatus.PENDING

    tasks: list[Task] = Field(default_factory=list)

    current_task_id: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None

    final_output: str = ""
    error: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
