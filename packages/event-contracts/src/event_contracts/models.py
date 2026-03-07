from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field
from telemetry_models import TelemetryFrame


class SessionEventType(StrEnum):
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    LAP_STARTED = "lap.started"
    LAP_COMPLETED = "lap.completed"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TelemetryFrameEvent(BaseModel):
    event_id: str
    published_at: datetime
    source: str = "telemetry-ingest"
    frame: TelemetryFrame


class SessionEvent(BaseModel):
    event_id: str
    published_at: datetime
    event_type: SessionEventType
    session_id: str
    lap_number: int | None = Field(default=None, ge=0)
    payload: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class DerivedEvent(BaseModel):
    event_id: str
    published_at: datetime
    session_id: str
    lap_number: int | None = Field(default=None, ge=0)
    event_type: str
    severity: Severity = Severity.INFO
    payload: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class CoachingMessageEvent(BaseModel):
    event_id: str
    published_at: datetime
    session_id: str
    lap_number: int | None = Field(default=None, ge=0)
    rule_id: str
    message: str
    severity: Severity = Severity.INFO
    confidence: float = Field(ge=0.0, le=1.0)
