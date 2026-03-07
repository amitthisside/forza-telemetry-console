import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Annotated, Literal

from event_contracts import TelemetryFrameEvent
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from session_service.config import SessionSettings
from session_service.consumer import consume_telemetry_subject
from session_service.db import SessionLocal, get_db, init_db
from session_service.models import SessionModel
from session_service.repository import (
    append_frame,
    close_lap,
    close_session,
    ensure_lap,
    ensure_session,
    get_earliest_frame,
    get_latest_frame,
)
from session_service.repository import (
    get_session as repo_get_session,
)
from session_service.repository import (
    list_frames as repo_list_frames,
)
from session_service.repository import (
    list_frames_window as repo_list_frames_window,
)
from session_service.repository import (
    list_laps as repo_list_laps,
)
from session_service.repository import (
    list_sessions as repo_list_sessions,
)
from session_service.repository import (
    list_track_points as repo_list_track_points,
)

INACTIVE_SESSION_TIMEOUT = timedelta(seconds=12)
DbSession = Annotated[Session, Depends(get_db)]
logger = logging.getLogger(__name__)
settings = SessionSettings.from_env()


@dataclass
class ConsumerStats:
    telemetry_events_consumed: int = 0
    telemetry_events_rejected: int = 0


@dataclass
class SessionOpsStats:
    lap_boundary_transitions: int = 0
    inactive_session_closures: int = 0
    replay_queries: int = 0
    replay_query_duration_ms_total: float = 0.0
    replay_rows_returned: int = 0


@dataclass
class SessionRuntimeState:
    current_lap_number: int | None = None
    current_lap_id: str | None = None
    last_seen_at: datetime | None = None
    last_lap_distance: float | None = None
    last_race_time_ms: int | None = None


consumer_stats = ConsumerStats()
ops_stats = SessionOpsStats()
runtime_states: dict[str, SessionRuntimeState] = {}
stop_event = asyncio.Event()
consumer_task: asyncio.Task[None] | None = None


class SessionSummary(BaseModel):
    session_id: str
    started_at: datetime
    ended_at: datetime | None = None


class LapSummary(BaseModel):
    lap_id: str
    lap_number: int
    started_at: datetime | None = None
    ended_at: datetime | None = None
    lap_time_ms: int | None = None


class FrameSummary(BaseModel):
    frame_index: int
    lap_id: str | None = None
    received_at: datetime
    speed: float
    rpm: float
    throttle: float
    brake: float
    position_x: float
    position_y: float
    position_z: float


class SessionReplayResponse(BaseModel):
    session_id: str
    frames: list[FrameSummary]


class TrackPathPoint(BaseModel):
    frame_index: int
    lap_id: str | None = None
    x: float
    y: float
    z: float
    color_value: float


class TrackPathResponse(BaseModel):
    session_id: str
    color_by: str
    points: list[TrackPathPoint]


class SessionTimeline(BaseModel):
    session_id: str
    frame_start: int | None = None
    frame_end: int | None = None
    frame_count: int
    laps: list[LapSummary]


class SessionConsumerStats(BaseModel):
    telemetry_events_consumed: int
    telemetry_events_rejected: int
    nats_enabled: bool


def _frame_time(frame_event: TelemetryFrameEvent) -> datetime:
    if frame_event.frame.received_at.tzinfo is None:
        return frame_event.frame.received_at.replace(tzinfo=UTC)
    return frame_event.frame.received_at.astimezone(UTC)


def _close_current_lap(
    db: Session,
    state: SessionRuntimeState,
    closed_at: datetime,
    lap_time_ms: int | None,
) -> None:
    if state.current_lap_id is None:
        return
    close_lap(db, state.current_lap_id, closed_at, lap_time_ms)


def _start_lap(
    db: Session,
    session_id: str,
    state: SessionRuntimeState,
    lap_number: int,
    started_at: datetime,
) -> str:
    lap = ensure_lap(db, session_id, lap_number, started_at)
    state.current_lap_number = lap_number
    state.current_lap_id = lap.id
    return lap.id


def _resolve_lap_for_frame(
    db: Session,
    event: TelemetryFrameEvent,
    state: SessionRuntimeState,
) -> str:
    frame = event.frame
    timestamp = _frame_time(event)

    lap_number = frame.lap_number
    lap_distance = frame.lap_distance
    race_time_ms = frame.current_race_time_ms

    if state.current_lap_number is None:
        initial_lap = lap_number if lap_number is not None else 1
        return _start_lap(db, event.session_id, state, initial_lap, timestamp)

    if lap_number is not None:
        if lap_number > state.current_lap_number:
            _close_current_lap(db, state, timestamp, frame.lap_time_ms)
            ops_stats.lap_boundary_transitions += 1
            logger.info(
                "lap_transition reason=lap_number_increment session_id=%s lap=%s",
                event.session_id,
                lap_number,
            )
            return _start_lap(db, event.session_id, state, lap_number, timestamp)
        if lap_number < state.current_lap_number:
            _close_current_lap(db, state, timestamp, frame.lap_time_ms)
            ops_stats.lap_boundary_transitions += 1
            logger.info(
                "lap_transition reason=lap_number_reset session_id=%s lap=%s",
                event.session_id,
                lap_number,
            )
            return _start_lap(db, event.session_id, state, lap_number, timestamp)

    lap_distance_reset = (
        lap_distance is not None
        and state.last_lap_distance is not None
        and state.last_lap_distance > 500.0
        and lap_distance < 100.0
    )
    race_time_reset = (
        race_time_ms is not None
        and state.last_race_time_ms is not None
        and race_time_ms < state.last_race_time_ms
    )

    if lap_number is None and (lap_distance_reset or race_time_reset):
        next_lap = state.current_lap_number + 1
        _close_current_lap(db, state, timestamp, frame.lap_time_ms)
        ops_stats.lap_boundary_transitions += 1
        logger.info(
            (
                "lap_transition reason=inferred_reset session_id=%s lap=%s "
                "lap_distance_reset=%s race_time_reset=%s"
            ),
            event.session_id,
            next_lap,
            lap_distance_reset,
            race_time_reset,
        )
        return _start_lap(db, event.session_id, state, next_lap, timestamp)

    return state.current_lap_id or _start_lap(db, event.session_id, state, 1, timestamp)


def _close_inactive_sessions(db: Session, active_session_id: str, now: datetime) -> None:
    stale_sessions: list[str] = []
    for session_id, state in runtime_states.items():
        if session_id == active_session_id:
            continue
        if state.last_seen_at is None:
            continue
        if now - state.last_seen_at < INACTIVE_SESSION_TIMEOUT:
            continue
        _close_current_lap(db, state, now, None)
        close_session(db, session_id, now)
        ops_stats.inactive_session_closures += 1
        logger.info("session_closed reason=inactive_timeout session_id=%s", session_id)
        stale_sessions.append(session_id)

    for session_id in stale_sessions:
        runtime_states.pop(session_id, None)


def process_telemetry_event(event: TelemetryFrameEvent) -> None:
    db = SessionLocal()
    try:
        now = _frame_time(event)
        _close_inactive_sessions(db, event.session_id, now)

        state = runtime_states.setdefault(event.session_id, SessionRuntimeState())
        ensure_session(db, event.session_id, event.published_at)
        lap_id = _resolve_lap_for_frame(db, event, state)
        append_frame(db, event.session_id, event.frame, lap_id=lap_id)

        state.last_seen_at = now
        state.last_lap_distance = event.frame.lap_distance
        state.last_race_time_ms = event.frame.current_race_time_ms

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


def _require_session(db: Session, session_id: str) -> SessionModel:
    session = repo_get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


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
    session = _require_session(db, session_id)

    return SessionSummary(
        session_id=session.id,
        started_at=session.started_at.replace(tzinfo=UTC),
        ended_at=session.ended_at.replace(tzinfo=UTC) if session.ended_at is not None else None,
    )


@api.get("/sessions/{session_id}/laps", response_model=list[LapSummary])
def get_session_laps(session_id: str, db: DbSession) -> list[LapSummary]:
    _require_session(db, session_id)
    laps = repo_list_laps(db, session_id)
    return [
        LapSummary(
            lap_id=lap.id,
            lap_number=lap.lap_number,
            started_at=lap.started_at.replace(tzinfo=UTC) if lap.started_at is not None else None,
            ended_at=lap.ended_at.replace(tzinfo=UTC) if lap.ended_at is not None else None,
            lap_time_ms=lap.lap_time_ms,
        )
        for lap in laps
    ]


@api.get("/sessions/{session_id}/frames")
def get_session_frames(
    session_id: str,
    db: DbSession,
    limit: int = 1000,
    start_frame: int = 0,
    end_frame: int | None = None,
    step: int = 1,
) -> dict[str, list[FrameSummary]]:
    _require_session(db, session_id)
    started = perf_counter()
    frames = repo_list_frames_window(
        db,
        session_id,
        start_frame=max(0, start_frame),
        end_frame=end_frame,
        step=max(1, min(step, 50)),
        limit=max(1, min(limit, 5000)),
    )
    payload = [
        FrameSummary(
            frame_index=frame.frame_index,
            lap_id=frame.lap_id,
            received_at=frame.received_at.replace(tzinfo=UTC),
            speed=frame.speed,
            rpm=frame.rpm,
            throttle=frame.throttle,
            brake=frame.brake,
            position_x=frame.position_x,
            position_y=frame.position_y,
            position_z=frame.position_z,
        )
        for frame in frames
    ]
    ops_stats.replay_queries += 1
    ops_stats.replay_query_duration_ms_total += (perf_counter() - started) * 1000.0
    ops_stats.replay_rows_returned += len(payload)
    return {"frames": payload}


@api.get("/sessions/{session_id}/replay", response_model=SessionReplayResponse)
def replay_session_frames(
    session_id: str,
    db: DbSession,
    start_frame: int = 0,
    end_frame: int | None = None,
    step: int = 1,
    limit: int = 2000,
) -> SessionReplayResponse:
    _require_session(db, session_id)
    started = perf_counter()
    frames = repo_list_frames_window(
        db,
        session_id,
        start_frame=max(0, start_frame),
        end_frame=end_frame,
        step=max(1, min(step, 50)),
        limit=max(1, min(limit, 5000)),
    )
    payload = SessionReplayResponse(
        session_id=session_id,
        frames=[
            FrameSummary(
                frame_index=frame.frame_index,
                lap_id=frame.lap_id,
                received_at=frame.received_at.replace(tzinfo=UTC),
                speed=frame.speed,
                rpm=frame.rpm,
                throttle=frame.throttle,
                brake=frame.brake,
                position_x=frame.position_x,
                position_y=frame.position_y,
                position_z=frame.position_z,
            )
            for frame in frames
        ],
    )
    ops_stats.replay_queries += 1
    ops_stats.replay_query_duration_ms_total += (perf_counter() - started) * 1000.0
    ops_stats.replay_rows_returned += len(frames)
    return payload


@api.get("/sessions/{session_id}/track/path", response_model=TrackPathResponse)
def track_path(
    session_id: str,
    db: DbSession,
    color_by: Literal["speed", "throttle", "brake"] = Query(default="speed"),
    limit: int = 5000,
) -> TrackPathResponse:
    _require_session(db, session_id)
    started = perf_counter()
    rows = repo_list_track_points(db, session_id, limit=max(1, min(limit, 10000)))

    def color_value(frame) -> float:
        if color_by == "throttle":
            return frame.throttle
        if color_by == "brake":
            return frame.brake
        return frame.speed

    payload = TrackPathResponse(
        session_id=session_id,
        color_by=color_by,
        points=[
            TrackPathPoint(
                frame_index=frame.frame_index,
                lap_id=frame.lap_id,
                x=frame.position_x,
                y=frame.position_y,
                z=frame.position_z,
                color_value=color_value(frame),
            )
            for frame in rows
        ],
    )
    ops_stats.replay_queries += 1
    ops_stats.replay_query_duration_ms_total += (perf_counter() - started) * 1000.0
    ops_stats.replay_rows_returned += len(rows)
    return payload


@api.get("/sessions/{session_id}/timeline", response_model=SessionTimeline)
def session_timeline(session_id: str, db: DbSession) -> SessionTimeline:
    _require_session(db, session_id)
    started = perf_counter()
    first = get_earliest_frame(db, session_id)
    last = get_latest_frame(db, session_id)
    laps = repo_list_laps(db, session_id)

    frame_start = first.frame_index if first is not None else None
    frame_end = last.frame_index if last is not None else None
    frame_count = 0 if frame_start is None or frame_end is None else (frame_end - frame_start + 1)

    payload = SessionTimeline(
        session_id=session_id,
        frame_start=frame_start,
        frame_end=frame_end,
        frame_count=frame_count,
        laps=[
            LapSummary(
                lap_id=lap.id,
                lap_number=lap.lap_number,
                started_at=(
                    lap.started_at.replace(tzinfo=UTC) if lap.started_at is not None else None
                ),
                ended_at=lap.ended_at.replace(tzinfo=UTC) if lap.ended_at is not None else None,
                lap_time_ms=lap.lap_time_ms,
            )
            for lap in laps
        ],
    )
    ops_stats.replay_queries += 1
    ops_stats.replay_query_duration_ms_total += (perf_counter() - started) * 1000.0
    return payload


@api.get("/sessions/{session_id}/export/json")
def export_session_json(session_id: str, db: DbSession) -> dict[str, object]:
    _require_session(db, session_id)
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
    _require_session(db, session_id)
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
    replay_avg_ms = (
        ops_stats.replay_query_duration_ms_total / ops_stats.replay_queries
        if ops_stats.replay_queries > 0
        else 0.0
    )
    payload = "\n".join(
        [
            "# TYPE app_up gauge",
            "app_up 1",
            "# TYPE session_lap_boundary_transitions_total counter",
            f"session_lap_boundary_transitions_total {ops_stats.lap_boundary_transitions}",
            "# TYPE session_inactive_closures_total counter",
            f"session_inactive_closures_total {ops_stats.inactive_session_closures}",
            "# TYPE session_replay_queries_total counter",
            f"session_replay_queries_total {ops_stats.replay_queries}",
            "# TYPE session_replay_rows_returned_total counter",
            f"session_replay_rows_returned_total {ops_stats.replay_rows_returned}",
            "# TYPE session_replay_query_avg_ms gauge",
            f"session_replay_query_avg_ms {round(replay_avg_ms, 3)}",
        ]
    )
    return Response(content=f"{payload}\n", media_type="text/plain; version=0.0.4")


app.include_router(api)
