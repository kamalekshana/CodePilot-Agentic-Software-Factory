
from pydantic import BaseModel, ConfigDict, Field


class FixTask(BaseModel):
    """A structured correction task created by the Debugging Agent."""

    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1)
    error_summary: str = Field(min_length=1)
    root_cause: str = Field(min_length=1)
    correction_instructions: str = Field(min_length=1)
    related_test: str = ""
    priority: str = "high"
