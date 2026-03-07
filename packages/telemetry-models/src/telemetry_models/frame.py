from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryFrame(BaseModel):
    received_at: datetime
    frame_index: int = Field(ge=0)
    speed: float = 0.0
    rpm: float = 0.0
    gear: int = 0
    throttle: float = Field(default=0.0, ge=0.0, le=1.0)
    brake: float = Field(default=0.0, ge=0.0, le=1.0)
    steering: float = Field(default=0.0, ge=-1.0, le=1.0)
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
