import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from statistics import pvariance
from typing import Final

from event_contracts import TelemetryFrameEvent
from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import Response
from pydantic import BaseModel

from analytics_service.config import AnalyticsSettings
from analytics_service.consumer import consume_telemetry_subject
from analytics_service.rules import (
    CoachingMessage,
    DiagnosticSignal,
    SessionSignalSnapshot,
    evaluate_coaching,
    evaluate_diagnostics,
)

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"
logger = logging.getLogger(__name__)
settings = AnalyticsSettings.from_env()


@dataclass
class SessionAccumulator:
    frames_seen: int = 0
    rear_slip_events: int = 0
    early_throttle_events: int = 0
    brake_release_deltas: list[float] = field(default_factory=list)
    _last_brake: float | None = None
    best_speed_kmh: float = 0.0
    latest_speed_kmh: float = 0.0

    def ingest(self, event: TelemetryFrameEvent) -> None:
        frame = event.frame
        self.frames_seen += 1
        self.latest_speed_kmh = frame.speed
        self.best_speed_kmh = max(self.best_speed_kmh, frame.speed)

        rear_slip = max(frame.tire_slip.rl, frame.tire_slip.rr)
        if rear_slip >= 1.0:
            self.rear_slip_events += 1

        if frame.throttle >= 0.55 and rear_slip >= 0.75:
            self.early_throttle_events += 1

        if self._last_brake is not None:
            delta = abs(frame.brake - self._last_brake)
            if delta > 0.01:
                self.brake_release_deltas.append(delta)
                if len(self.brake_release_deltas) > 512:
                    self.brake_release_deltas.pop(0)
        self._last_brake = frame.brake

    def snapshot(self) -> SessionSignalSnapshot:
        brake_variance = (
            pvariance(self.brake_release_deltas) if len(self.brake_release_deltas) > 1 else 0.0
        )
        early_throttle_pct = (
            float(self.early_throttle_events) / float(self.frames_seen)
            if self.frames_seen > 0
            else 0.0
        )
        exit_speed_delta = self.latest_speed_kmh - self.best_speed_kmh
        return SessionSignalSnapshot(
            brake_release_variance=brake_variance,
            rear_slip_events=self.rear_slip_events,
            early_throttle_pct=early_throttle_pct,
            exit_speed_delta_kmh=exit_speed_delta,
        )


@dataclass
class AnalyticsStore:
    sessions: dict[str, SessionAccumulator] = field(default_factory=dict)

    def ingest(self, event: TelemetryFrameEvent) -> None:
        accumulator = self.sessions.setdefault(event.session_id, SessionAccumulator())
        accumulator.ingest(event)

    def snapshot(self, session_id: str) -> SessionSignalSnapshot:
        accumulator = self.sessions.get(session_id)
        if accumulator is None:
            return SessionSignalSnapshot()
        return accumulator.snapshot()


@dataclass
class ConsumerStats:
    telemetry_events_consumed: int = 0
    telemetry_events_rejected: int = 0


store = AnalyticsStore()
consumer_stats = ConsumerStats()
store_lock = asyncio.Lock()
stop_event = asyncio.Event()
consumer_task: asyncio.Task[None] | None = None


async def process_telemetry_event(event: TelemetryFrameEvent) -> None:
    async with store_lock:
        store.ingest(event)
        consumer_stats.telemetry_events_consumed += 1


@asynccontextmanager
async def lifespan(_: FastAPI):
    global consumer_task

    if settings.nats_enabled:
        stop_event.clear()

        def on_event(event: TelemetryFrameEvent) -> None:
            asyncio.create_task(process_telemetry_event(event))

        consumer_task = asyncio.create_task(
            consume_telemetry_subject(
                nats_url=settings.nats_url,
                subject=settings.telemetry_subject,
                on_event=on_event,
                stop_event=stop_event,
            )
        )

    try:
        yield
    finally:
        if consumer_task is not None:
            stop_event.set()
            await consumer_task


app = FastAPI(title="analytics-service", version="0.1.0", lifespan=lifespan)
api = APIRouter(prefix="/api/v1")


class AnalysisResponse(BaseModel):
    session_id: str
    coaching_messages: int
    diagnostics: int


class LapAnalysisResponse(BaseModel):
    lap_id: str
    status: str


class HistorySummary(BaseModel):
    sessions: int
    best_lap_ms: int | None = None
    consistency_score: float = 0.0


class AnalyticsConsumerStats(BaseModel):
    telemetry_events_consumed: int
    telemetry_events_rejected: int
    nats_enabled: bool


def build_snapshot(
    brake_release_variance: float,
    rear_slip_events: int,
    early_throttle_pct: float,
    exit_speed_delta_kmh: float,
) -> SessionSignalSnapshot:
    return SessionSignalSnapshot(
        brake_release_variance=brake_release_variance,
        rear_slip_events=rear_slip_events,
        early_throttle_pct=early_throttle_pct,
        exit_speed_delta_kmh=exit_speed_delta_kmh,
    )


def apply_overrides(
    base: SessionSignalSnapshot,
    brake_release_variance: float | None,
    rear_slip_events: int | None,
    early_throttle_pct: float | None,
    exit_speed_delta_kmh: float | None,
) -> SessionSignalSnapshot:
    return SessionSignalSnapshot(
        brake_release_variance=(
            base.brake_release_variance
            if brake_release_variance is None
            else brake_release_variance
        ),
        rear_slip_events=base.rear_slip_events if rear_slip_events is None else rear_slip_events,
        early_throttle_pct=(
            base.early_throttle_pct if early_throttle_pct is None else early_throttle_pct
        ),
        exit_speed_delta_kmh=(
            base.exit_speed_delta_kmh if exit_speed_delta_kmh is None else exit_speed_delta_kmh
        ),
    )


async def snapshot_for_session(session_id: str) -> SessionSignalSnapshot:
    async with store_lock:
        return store.snapshot(session_id)


@api.get("/analysis/sessions/{session_id}", response_model=AnalysisResponse)
async def session_analysis(
    session_id: str,
    brake_release_variance: float | None = Query(default=None, ge=0.0),
    rear_slip_events: int | None = Query(default=None, ge=0),
    early_throttle_pct: float | None = Query(default=None, ge=0.0, le=1.0),
    exit_speed_delta_kmh: float | None = None,
) -> AnalysisResponse:
    live_snapshot = await snapshot_for_session(session_id)
    snapshot = apply_overrides(
        live_snapshot,
        brake_release_variance,
        rear_slip_events,
        early_throttle_pct,
        exit_speed_delta_kmh,
    )
    coaching = evaluate_coaching(snapshot)
    diagnostics = evaluate_diagnostics(snapshot)
    return AnalysisResponse(
        session_id=session_id,
        coaching_messages=len(coaching),
        diagnostics=len(diagnostics),
    )


@api.get("/analysis/laps/{lap_id}", response_model=LapAnalysisResponse)
def lap_analysis(lap_id: str) -> LapAnalysisResponse:
    return LapAnalysisResponse(lap_id=lap_id, status="not_implemented")


@api.get("/coaching/sessions/{session_id}")
async def coaching_for_session(
    session_id: str,
    brake_release_variance: float | None = Query(default=None, ge=0.0),
    rear_slip_events: int | None = Query(default=None, ge=0),
    early_throttle_pct: float | None = Query(default=None, ge=0.0, le=1.0),
    exit_speed_delta_kmh: float | None = None,
) -> dict[str, list[CoachingMessage]]:
    live_snapshot = await snapshot_for_session(session_id)
    snapshot = apply_overrides(
        live_snapshot,
        brake_release_variance,
        rear_slip_events,
        early_throttle_pct,
        exit_speed_delta_kmh,
    )
    return {"messages": evaluate_coaching(snapshot)}


@api.get("/diagnostics/sessions/{session_id}")
async def diagnostics_for_session(
    session_id: str,
    rear_slip_events: int | None = Query(default=None, ge=0),
    exit_speed_delta_kmh: float | None = None,
) -> dict[str, list[DiagnosticSignal]]:
    live_snapshot = await snapshot_for_session(session_id)
    snapshot = apply_overrides(
        live_snapshot,
        None,
        rear_slip_events,
        None,
        exit_speed_delta_kmh,
    )
    return {"diagnostics": evaluate_diagnostics(snapshot)}


@api.get("/history/summary", response_model=HistorySummary)
async def history_summary() -> HistorySummary:
    async with store_lock:
        sessions = len(store.sessions)
    return HistorySummary(sessions=sessions, best_lap_ms=None, consistency_score=0.0)


@api.get("/ingest/stats", response_model=AnalyticsConsumerStats)
def ingest_stats() -> AnalyticsConsumerStats:
    return AnalyticsConsumerStats(
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
