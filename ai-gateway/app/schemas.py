from typing import Any, Literal
from pydantic import BaseModel, Field

class Event(BaseModel):
    event_id: str | None = None
    source: str
    timestamp: str | None = None
    severity: int | str | None = None
    category: str | None = None
    src_ip: str | None = None
    dst_ip: str | None = None
    rule_id: str | None = None
    raw_event: dict[str, Any] = Field(default_factory=dict)

class AnalyzeRequest(BaseModel):
    source: str
    events: list[Event] = Field(min_length=1)

class Decision(BaseModel):
    classification: str
    severity: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0, le=1)
    playbook: str | None = None
    action: str | None = None
    requires_approval: bool = True
    reasoning_summary: str
    observables: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)

class AnalyzeResponse(BaseModel):
    decision: Decision
    model: str
    event_count: int
    automation_allowed: bool
