from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from session_service.models import LapModel, SessionModel, TelemetryFrameModel


def list_sessions(db: Session) -> list[SessionModel]:
    stmt = select(SessionModel).order_by(SessionModel.started_at.desc())
    return list(db.scalars(stmt))


def get_session(db: Session, session_id: str) -> SessionModel | None:
    return db.get(SessionModel, session_id)


def list_laps(db: Session, session_id: str) -> list[LapModel]:
    stmt = select(LapModel).where(LapModel.session_id == session_id).order_by(LapModel.lap_number)
    return list(db.scalars(stmt))


def list_frames(db: Session, session_id: str, limit: int = 1000) -> list[TelemetryFrameModel]:
    stmt = (
        select(TelemetryFrameModel)
        .where(TelemetryFrameModel.session_id == session_id)
        .order_by(TelemetryFrameModel.frame_index)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def list_frames_window(
    db: Session,
    session_id: str,
    start_frame: int = 0,
    end_frame: int | None = None,
    step: int = 1,
    limit: int = 2000,
) -> list[TelemetryFrameModel]:
    stmt = select(TelemetryFrameModel).where(
        TelemetryFrameModel.session_id == session_id,
        TelemetryFrameModel.frame_index >= start_frame,
    )
    if end_frame is not None:
        stmt = stmt.where(TelemetryFrameModel.frame_index <= end_frame)
    stmt = stmt.order_by(TelemetryFrameModel.frame_index)
    rows = list(db.scalars(stmt.limit(max(1, min(limit * max(1, step), 10000)))))
    if step <= 1:
        return rows[:limit]
    return rows[::step][:limit]


def list_track_points(db: Session, session_id: str, limit: int = 5000) -> list[TelemetryFrameModel]:
    stmt = (
        select(TelemetryFrameModel)
        .where(TelemetryFrameModel.session_id == session_id)
        .order_by(TelemetryFrameModel.frame_index)
        .limit(max(1, min(limit, 10000)))
    )
    return list(db.scalars(stmt))


def get_lap_by_number(db: Session, session_id: str, lap_number: int) -> LapModel | None:
    stmt = (
        select(LapModel)
        .where(
            LapModel.session_id == session_id,
            LapModel.lap_number == lap_number,
        )
        .limit(1)
    )
    return db.scalars(stmt).first()


def get_latest_frame(db: Session, session_id: str) -> TelemetryFrameModel | None:
    stmt = (
        select(TelemetryFrameModel)
        .where(TelemetryFrameModel.session_id == session_id)
        .order_by(TelemetryFrameModel.frame_index.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def get_earliest_frame(db: Session, session_id: str) -> TelemetryFrameModel | None:
    stmt = (
        select(TelemetryFrameModel)
        .where(TelemetryFrameModel.session_id == session_id)
        .order_by(TelemetryFrameModel.frame_index.asc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def ensure_session(db: Session, session_id: str, started_at) -> SessionModel:
    session = db.get(SessionModel, session_id)
    if session is not None:
        return session

    started_naive = started_at.astimezone(UTC).replace(tzinfo=None)
    session = SessionModel(id=session_id, started_at=started_naive, ended_at=None)
    db.add(session)
    return session


def close_session(db: Session, session_id: str, ended_at) -> None:
    session = db.get(SessionModel, session_id)
    if session is None or session.ended_at is not None:
        return
    session.ended_at = ended_at.astimezone(UTC).replace(tzinfo=None)


def ensure_lap(db: Session, session_id: str, lap_number: int, started_at) -> LapModel:
    lap = get_lap_by_number(db, session_id, lap_number)
    if lap is not None:
        if lap.started_at is None:
            lap.started_at = started_at.astimezone(UTC).replace(tzinfo=None)
        return lap

    lap = LapModel(
        id=f"{session_id}-lap-{lap_number}",
        session_id=session_id,
        lap_number=lap_number,
        started_at=started_at.astimezone(UTC).replace(tzinfo=None),
        ended_at=None,
        lap_time_ms=None,
    )
    db.add(lap)
    return lap


def close_lap(db: Session, lap_id: str, ended_at, lap_time_ms: int | None = None) -> None:
    lap = db.get(LapModel, lap_id)
    if lap is None:
        return
    if lap.ended_at is None:
        lap.ended_at = ended_at.astimezone(UTC).replace(tzinfo=None)
    if lap_time_ms is not None and lap_time_ms >= 0:
        lap.lap_time_ms = lap_time_ms
    elif lap.lap_time_ms is None and lap.started_at is not None and lap.ended_at is not None:
        lap.lap_time_ms = int((lap.ended_at - lap.started_at).total_seconds() * 1000)


def append_frame(
    db: Session,
    session_id: str,
    frame,
    lap_id: str | None = None,
) -> TelemetryFrameModel:
    model = TelemetryFrameModel(
        session_id=session_id,
        lap_id=lap_id,
        received_at=frame.received_at.astimezone(UTC).replace(tzinfo=None),
        frame_index=frame.frame_index,
        speed=frame.speed,
        rpm=frame.rpm,
        gear=frame.gear,
        throttle=frame.throttle,
        brake=frame.brake,
        steering=frame.steering,
        position_x=frame.world_position.x,
        position_y=frame.world_position.y,
        position_z=frame.world_position.z,
    )
    db.add(model)
    return model
