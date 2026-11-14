from enum import Enum
from pydantic import BaseModel, Field

class InvestigationStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class InvestigationCreate(BaseModel):
    binary_id: str
    objective: str = Field(min_length=3, max_length=2000)
    max_tool_calls: int = Field(default=30, ge=1, le=500)
    dynamic_execution: bool = False

class Investigation(BaseModel):
    id: str
    binary_id: str
    objective: str
    status: InvestigationStatus = InvestigationStatus.CREATED
    max_tool_calls: int
    dynamic_execution: bool = False
    findings: list[dict] = Field(default_factory=list)
