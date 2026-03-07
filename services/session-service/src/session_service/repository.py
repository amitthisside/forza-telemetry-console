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
