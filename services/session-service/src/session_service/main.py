from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Final

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from session_service.db import get_db, init_db
from session_service.repository import (
    get_session as repo_get_session,
)
from session_service.repository import (
    list_frames as repo_list_frames,
)
from session_service.repository import (
    list_laps as repo_list_laps,
)
from session_service.repository import (
    list_sessions as repo_list_sessions,
)

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"
DbSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="session-service", version="0.1.0", lifespan=lifespan)
api = APIRouter(prefix="/api/v1")


class SessionSummary(BaseModel):
    session_id: str
    started_at: datetime
    ended_at: datetime | None = None


class LapSummary(BaseModel):
    lap_id: str
    lap_number: int


class FrameSummary(BaseModel):
    frame_index: int
    received_at: datetime
    speed: float
    rpm: float


@api.get("/sessions", response_model=list[SessionSummary])
def list_sessions(db: DbSession) -> list[SessionSummary]:
    sessions = repo_list_sessions(db)
    return [
        SessionSummary(session_id=s.id, started_at=s.started_at, ended_at=s.ended_at)
        for s in sessions
    ]


@api.get("/sessions/{session_id}", response_model=SessionSummary)
def get_session(session_id: str, db: DbSession) -> SessionSummary:
    session = repo_get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    return SessionSummary(
        session_id=session.id,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )


@api.get("/sessions/{session_id}/laps", response_model=list[LapSummary])
def get_session_laps(session_id: str, db: DbSession) -> list[LapSummary]:
    laps = repo_list_laps(db, session_id)
    return [LapSummary(lap_id=lap.id, lap_number=lap.lap_number) for lap in laps]


@api.get("/sessions/{session_id}/frames")
def get_session_frames(
    session_id: str,
    db: DbSession,
    limit: int = 1000,
) -> dict[str, list[FrameSummary]]:
    frames = repo_list_frames(db, session_id, limit=max(1, min(limit, 5000)))
    payload = [
        FrameSummary(
            frame_index=frame.frame_index,
            received_at=frame.received_at,
            speed=frame.speed,
            rpm=frame.rpm,
        )
        for frame in frames
    ]
    return {"frames": payload}


@api.get("/sessions/{session_id}/export/json")
def export_session_json(session_id: str, db: DbSession) -> dict[str, object]:
    frames = repo_list_frames(db, session_id, limit=5000)
    return {
        "session_id": session_id,
        "format": "json",
        "frames": [
            {
                "frame_index": frame.frame_index,
                "received_at": frame.received_at.isoformat(),
                "speed": frame.speed,
                "rpm": frame.rpm,
            }
            for frame in frames
        ],
    }


@api.get("/sessions/{session_id}/export/csv")
def export_session_csv(session_id: str, db: DbSession) -> Response:
    frames = repo_list_frames(db, session_id, limit=5000)
    lines = ["session_id,frame_index,received_at,speed,rpm"]
    for frame in frames:
        lines.append(
            f"{session_id},{frame.frame_index},{frame.received_at.isoformat()},{frame.speed},{frame.rpm}"
        )
    payload = "\n".join(lines) + "\n"
    return Response(content=payload, media_type="text/csv")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=METRICS_PAYLOAD, media_type="text/plain; version=0.0.4")


app.include_router(api)
