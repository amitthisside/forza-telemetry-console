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


def ensure_session(db: Session, session_id: str, started_at) -> SessionModel:
    session = db.get(SessionModel, session_id)
    if session is not None:
        return session

    started_naive = started_at.astimezone(UTC).replace(tzinfo=None)
    session = SessionModel(id=session_id, started_at=started_naive, ended_at=None)
    db.add(session)
    return session


def append_frame(db: Session, session_id: str, frame) -> TelemetryFrameModel:
    model = TelemetryFrameModel(
        session_id=session_id,
        lap_id=None,
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
