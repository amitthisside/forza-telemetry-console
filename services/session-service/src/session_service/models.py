from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class LapModel(Base):
    __tablename__ = "laps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    lap_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class TelemetryFrameModel(Base):
    __tablename__ = "telemetry_frames"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    lap_id: Mapped[str | None] = mapped_column(ForeignKey("laps.id"), nullable=True, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    frame_index: Mapped[int] = mapped_column(Integer, nullable=False)

    speed: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rpm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gear: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    throttle: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    brake: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    steering: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    position_z: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
