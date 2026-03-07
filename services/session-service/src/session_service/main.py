import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Final

from event_contracts import TelemetryFrameEvent
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from session_service.config import SessionSettings
from session_service.consumer import consume_telemetry_subject
from session_service.db import SessionLocal, get_db, init_db
from session_service.repository import (
    append_frame,
    ensure_session,
)
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
logger = logging.getLogger(__name__)
settings = SessionSettings.from_env()


@dataclass
class ConsumerStats:
    telemetry_events_consumed: int = 0
    telemetry_events_rejected: int = 0


consumer_stats = ConsumerStats()
stop_event = asyncio.Event()
consumer_task: asyncio.Task[None] | None = None


def process_telemetry_event(event: TelemetryFrameEvent) -> None:
    db = SessionLocal()
    try:
        ensure_session(db, event.session_id, event.published_at)
        append_frame(db, event.session_id, event.frame)
        db.commit()
        consumer_stats.telemetry_events_consumed += 1
    except Exception as exc:  # pragma: no cover - database failure path
        db.rollback()
        consumer_stats.telemetry_events_rejected += 1
        logger.warning("Failed to persist telemetry event %s: %s", event.event_id, exc)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    global consumer_task

    init_db()
    if settings.nats_enabled:
        stop_event.clear()
        consumer_task = asyncio.create_task(
            consume_telemetry_subject(
                nats_url=settings.nats_url,
                subject=settings.telemetry_subject,
                on_event=process_telemetry_event,
                stop_event=stop_event,
            )
        )

    try:
        yield
    finally:
        if consumer_task is not None:
            stop_event.set()
            await consumer_task


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


class SessionConsumerStats(BaseModel):
    telemetry_events_consumed: int
    telemetry_events_rejected: int
    nats_enabled: bool


@api.get("/sessions", response_model=list[SessionSummary])
def list_sessions(db: DbSession) -> list[SessionSummary]:
    sessions = repo_list_sessions(db)
    return [
        SessionSummary(
            session_id=s.id,
            started_at=s.started_at.replace(tzinfo=UTC),
            ended_at=s.ended_at.replace(tzinfo=UTC) if s.ended_at is not None else None,
        )
        for s in sessions
    ]


@api.get("/sessions/{session_id}", response_model=SessionSummary)
def get_session(session_id: str, db: DbSession) -> SessionSummary:
    session = repo_get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    return SessionSummary(
        session_id=session.id,
        started_at=session.started_at.replace(tzinfo=UTC),
        ended_at=session.ended_at.replace(tzinfo=UTC) if session.ended_at is not None else None,
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
            received_at=frame.received_at.replace(tzinfo=UTC),
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
                "received_at": frame.received_at.replace(tzinfo=UTC).isoformat(),
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
            f"{session_id},{frame.frame_index},{frame.received_at.replace(tzinfo=UTC).isoformat()},{frame.speed},{frame.rpm}"
        )
    payload = "\n".join(lines) + "\n"
    return Response(content=payload, media_type="text/csv")


@api.get("/ingest/stats", response_model=SessionConsumerStats)
def ingest_stats() -> SessionConsumerStats:
    return SessionConsumerStats(
        telemetry_events_consumed=consumer_stats.telemetry_events_consumed,
        telemetry_events_rejected=consumer_stats.telemetry_events_rejected,
        nats_enabled=settings.nats_enabled,
    )


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
