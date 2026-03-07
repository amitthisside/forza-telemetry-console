from datetime import datetime

from pydantic import BaseModel, Field


class WheelValues(BaseModel):
    fl: float = 0.0
    fr: float = 0.0
    rl: float = 0.0
    rr: float = 0.0


class Vector3(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class Orientation(BaseModel):
    yaw: float | None = None
    pitch: float | None = None
    roll: float | None = None


class TelemetryFrame(BaseModel):
    received_at: datetime
    frame_index: int = Field(ge=0)
    speed: float = Field(default=0.0, ge=0.0)
    rpm: float = Field(default=0.0, ge=0.0)
    gear: int = 0
    throttle: float = Field(default=0.0, ge=0.0, le=1.0)
    brake: float = Field(default=0.0, ge=0.0, le=1.0)
    steering: float = Field(default=0.0, ge=-1.0, le=1.0)
    clutch: float | None = Field(default=None, ge=0.0, le=1.0)

    lap_number: int | None = Field(default=None, ge=0)
    lap_time_ms: int | None = Field(default=None, ge=0)
    current_race_time_ms: int | None = Field(default=None, ge=0)
    lap_distance: float | None = None

    world_position: Vector3 = Field(default_factory=Vector3)
    orientation: Orientation = Field(default_factory=Orientation)

    tire_slip: WheelValues = Field(default_factory=WheelValues)
    wheel_rotation_speed: WheelValues | None = None
    suspension_travel: WheelValues | None = None
    acceleration: Vector3 | None = None
