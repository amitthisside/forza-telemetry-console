from datetime import UTC, datetime

from session_service.models import Base, SessionModel, TelemetryFrameModel
from session_service.repository import list_frames, list_sessions
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_repository_lists_sessions_and_frames() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        db.add(
            SessionModel(
                id="s-1",
                started_at=datetime.now(UTC).replace(tzinfo=None),
                ended_at=None,
            )
        )
        db.add(
            TelemetryFrameModel(
                session_id="s-1",
                lap_id=None,
                received_at=datetime.now(UTC).replace(tzinfo=None),
                frame_index=1,
                speed=120.0,
                rpm=5000.0,
                gear=3,
                throttle=0.8,
                brake=0.0,
                steering=0.1,
                position_x=0.0,
                position_y=0.0,
                position_z=0.0,
            )
        )
        db.commit()

        sessions = list_sessions(db)
        frames = list_frames(db, "s-1")

        assert len(sessions) == 1
        assert sessions[0].id == "s-1"
        assert len(frames) == 1
        assert frames[0].speed == 120.0
