import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from statistics import mean, pvariance
from typing import Final

import httpx
from event_contracts import TelemetryFrameEvent
from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

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


class LapSummary(BaseModel):
    lap_id: str
    lap_number: int
    lap_time_ms: int | None = None


class SessionIndexEntry(BaseModel):
    session_id: str
    started_at: str
    ended_at: str | None = None


class ReplayFrame(BaseModel):
    frame_index: int
    lap_id: str | None = None
    speed: float
    throttle: float
    brake: float
    position_x: float
    position_z: float


class AnalysisResponse(BaseModel):
    session_id: str
    coaching_messages: int
    diagnostics: int
    lap_count: int = 0
    best_lap_ms: int | None = None
    consistency_score: float = 0.0


class LapAnalysisResponse(BaseModel):
    lap_id: str
    status: str
    frame_count: int = 0
    avg_speed_kmh: float = 0.0
    best_speed_kmh: float = 0.0
    avg_throttle: float = 0.0
    avg_brake: float = 0.0


class HistoryBestLap(BaseModel):
    session_id: str
    lap_id: str
    lap_number: int
    lap_time_ms: int


class HistoryGroupCount(BaseModel):
    key: str
    sessions: int


class HistorySummary(BaseModel):
    sessions: int
    session_count_active: int = 0
    session_count_completed: int = 0
    best_lap_ms: int | None = None
    average_lap_ms: float | None = None
    average_session_best_lap_ms: float | None = None
    improvement_trend_ms: float | None = None
    consistency_score: float = 0.0
    best_laps: list[HistoryBestLap] = Field(default_factory=list)
    sessions_by_track: list[HistoryGroupCount] = Field(default_factory=list)
    sessions_by_car: list[HistoryGroupCount] = Field(default_factory=list)


class AnalyticsConsumerStats(BaseModel):
    telemetry_events_consumed: int
    telemetry_events_rejected: int
    nats_enabled: bool


class CoachingPriorityMessage(BaseModel):
    rule_id: str
    message: str
    severity: str
    confidence: float
    rank: int
    priority_score: float
    repeat_count: int


class DiagnosticZone(BaseModel):
    zone_id: str
    x: float
    z: float
    occurrences: int


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


async def fetch_session_laps(session_id: str) -> list[LapSummary]:
    async with httpx.AsyncClient(timeout=4.0) as client:
        response = await client.get(
            f"{settings.session_service_base_url}/api/v1/sessions/{session_id}/laps"
        )
    if response.status_code != 200:
        return []
    return [LapSummary.model_validate(row) for row in response.json()]


async def fetch_session_index() -> list[SessionIndexEntry]:
    async with httpx.AsyncClient(timeout=4.0) as client:
        response = await client.get(f"{settings.session_service_base_url}/api/v1/sessions")
    if response.status_code != 200:
        return []
    return [SessionIndexEntry.model_validate(row) for row in response.json()]


async def fetch_session_replay(session_id: str, limit: int = 5000) -> list[ReplayFrame]:
    async with httpx.AsyncClient(timeout=6.0) as client:
        response = await client.get(
            f"{settings.session_service_base_url}/api/v1/sessions/{session_id}/replay?limit={limit}"
        )
    if response.status_code != 200:
        return []
    payload = response.json()
    return [ReplayFrame.model_validate(frame) for frame in payload.get("frames", [])]


def _group_from_session_id(session_id: str, marker: str) -> str | None:
    parts = session_id.split(":")
    for part in parts:
        if part.startswith(marker):
            return part.split("=", 1)[1] if "=" in part else part.removeprefix(marker)
    return None


def consistency_score(lap_times_ms: list[int]) -> float:
    if len(lap_times_ms) <= 1:
        return 0.0
    avg = mean(lap_times_ms)
    variance = pvariance(lap_times_ms)
    stddev = variance**0.5
    if avg <= 0:
        return 0.0
    score = max(0.0, 1.0 - (stddev / avg))
    return round(min(1.0, score), 3)


def rank_coaching(
    messages: list[CoachingMessage],
    snapshot: SessionSignalSnapshot,
) -> list[CoachingPriorityMessage]:
    severity_weight = {"high": 1.0, "medium": 0.7, "low": 0.4}
    ranked = []
    repeat_count = max(1, snapshot.rear_slip_events)
    for message in messages:
        priority = message.confidence * severity_weight.get(message.severity.value, 0.4)
        ranked.append((priority, message))
    ranked.sort(key=lambda item: item[0], reverse=True)

    payload: list[CoachingPriorityMessage] = []
    for index, (score, message) in enumerate(ranked, start=1):
        payload.append(
            CoachingPriorityMessage(
                rule_id=message.rule_id,
                message=message.message,
                severity=message.severity.value,
                confidence=message.confidence,
                rank=index,
                priority_score=round(score, 3),
                repeat_count=repeat_count,
            )
        )
    return payload


def derive_diagnostic_zones(frames: list[ReplayFrame]) -> list[DiagnosticZone]:
    if not frames:
        return []
    buckets: dict[str, tuple[float, float, int]] = {}
    for frame in frames:
        if frame.brake < 0.75 and frame.speed < 120:
            continue
        key = f"{round(frame.position_x / 20) * 20}:{round(frame.position_z / 20) * 20}"
        center_x = round(frame.position_x / 20) * 20
        center_z = round(frame.position_z / 20) * 20
        _, _, count = buckets.get(key, (center_x, center_z, 0))
        buckets[key] = (center_x, center_z, count + 1)

    zones = [
        DiagnosticZone(zone_id=f"zone-{idx+1}", x=x, z=z, occurrences=count)
        for idx, (_k, (x, z, count)) in enumerate(
            sorted(buckets.items(), key=lambda item: item[1][2], reverse=True)[:5]
        )
    ]
    return zones


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

    laps: list[LapSummary] = []
    try:
        laps = await fetch_session_laps(session_id)
    except Exception:
        laps = []

    lap_times = [lap.lap_time_ms for lap in laps if lap.lap_time_ms is not None]
    return AnalysisResponse(
        session_id=session_id,
        coaching_messages=len(coaching),
        diagnostics=len(diagnostics),
        lap_count=len(laps),
        best_lap_ms=min(lap_times) if lap_times else None,
        consistency_score=consistency_score(lap_times) if lap_times else 0.0,
    )


@api.get("/analysis/laps/{lap_id}", response_model=LapAnalysisResponse)
async def lap_analysis(lap_id: str, session_id: str | None = None) -> LapAnalysisResponse:
    resolved_session_id = session_id
    if resolved_session_id is None and "-lap-" in lap_id:
        resolved_session_id = lap_id.rsplit("-lap-", 1)[0]

    if resolved_session_id is None:
        return LapAnalysisResponse(lap_id=lap_id, status="missing_session_id")

    frames = await fetch_session_replay(resolved_session_id)
    lap_frames = [frame for frame in frames if frame.lap_id == lap_id]
    if not lap_frames:
        return LapAnalysisResponse(lap_id=lap_id, status="not_found")

    speeds = [frame.speed for frame in lap_frames]
    throttles = [frame.throttle for frame in lap_frames]
    brakes = [frame.brake for frame in lap_frames]
    return LapAnalysisResponse(
        lap_id=lap_id,
        status="ok",
        frame_count=len(lap_frames),
        avg_speed_kmh=round(mean(speeds), 3),
        best_speed_kmh=round(max(speeds), 3),
        avg_throttle=round(mean(throttles), 3),
        avg_brake=round(mean(brakes), 3),
    )


@api.get("/coaching/sessions/{session_id}")
async def coaching_for_session(
    session_id: str,
    brake_release_variance: float | None = Query(default=None, ge=0.0),
    rear_slip_events: int | None = Query(default=None, ge=0),
    early_throttle_pct: float | None = Query(default=None, ge=0.0, le=1.0),
    exit_speed_delta_kmh: float | None = None,
) -> dict[str, list[CoachingPriorityMessage]]:
    live_snapshot = await snapshot_for_session(session_id)
    snapshot = apply_overrides(
        live_snapshot,
        brake_release_variance,
        rear_slip_events,
        early_throttle_pct,
        exit_speed_delta_kmh,
    )
    ranked = rank_coaching(evaluate_coaching(snapshot), snapshot)
    return {"messages": ranked}


@api.get("/diagnostics/sessions/{session_id}")
async def diagnostics_for_session(
    session_id: str,
    rear_slip_events: int | None = Query(default=None, ge=0),
    exit_speed_delta_kmh: float | None = None,
) -> dict[str, list[DiagnosticSignal] | list[DiagnosticZone]]:
    live_snapshot = await snapshot_for_session(session_id)
    snapshot = apply_overrides(
        live_snapshot,
        None,
        rear_slip_events,
        None,
        exit_speed_delta_kmh,
    )
    diagnostics = evaluate_diagnostics(snapshot)
    try:
        frames = await fetch_session_replay(session_id)
    except Exception:
        frames = []
    zones = derive_diagnostic_zones(frames)
    return {"diagnostics": diagnostics, "zones": zones}


@api.get("/history/summary", response_model=HistorySummary)
async def history_summary() -> HistorySummary:
    session_index: list[SessionIndexEntry] = []
    try:
        session_index = await fetch_session_index()
    except Exception:
        session_index = []

    async with store_lock:
        live_sessions = len(store.sessions)

    if not session_index:
        return HistorySummary(sessions=live_sessions, best_lap_ms=None, consistency_score=0.0)

    lap_rows: list[tuple[str, LapSummary]] = []
    for session in session_index:
        try:
            laps = await fetch_session_laps(session.session_id)
        except Exception:
            laps = []
        lap_rows.extend((session.session_id, lap) for lap in laps if lap.lap_time_ms is not None)

    lap_times = [lap.lap_time_ms for _, lap in lap_rows if lap.lap_time_ms is not None]
    best_laps_sorted = sorted(
        (
            HistoryBestLap(
                session_id=session_id,
                lap_id=lap.lap_id,
                lap_number=lap.lap_number,
                lap_time_ms=int(lap.lap_time_ms),
            )
            for session_id, lap in lap_rows
            if lap.lap_time_ms is not None
        ),
        key=lambda row: row.lap_time_ms,
    )
    best_laps = best_laps_sorted[:5]

    per_session_best: list[int] = []
    for session in session_index:
        session_lap_times = [
            lap.lap_time_ms
            for sid, lap in lap_rows
            if sid == session.session_id and lap.lap_time_ms is not None
        ]
        if session_lap_times:
            per_session_best.append(int(min(session_lap_times)))

    improvement_trend_ms: float | None = None
    if len(per_session_best) >= 2:
        improvement_trend_ms = round(float(per_session_best[0] - per_session_best[-1]), 3)

    track_counts: dict[str, int] = {}
    car_counts: dict[str, int] = {}
    for session in session_index:
        track_key = _group_from_session_id(session.session_id, "track=")
        car_key = _group_from_session_id(session.session_id, "car=")
        if track_key is not None:
            track_counts[track_key] = track_counts.get(track_key, 0) + 1
        if car_key is not None:
            car_counts[car_key] = car_counts.get(car_key, 0) + 1

    return HistorySummary(
        sessions=len(session_index),
        session_count_active=sum(1 for session in session_index if session.ended_at is None),
        session_count_completed=sum(1 for session in session_index if session.ended_at is not None),
        best_lap_ms=min(lap_times) if lap_times else None,
        average_lap_ms=round(mean(lap_times), 3) if lap_times else None,
        average_session_best_lap_ms=round(mean(per_session_best), 3) if per_session_best else None,
        improvement_trend_ms=improvement_trend_ms,
        consistency_score=consistency_score(lap_times) if lap_times else 0.0,
        best_laps=best_laps,
        sessions_by_track=[
            HistoryGroupCount(key=key, sessions=count)
            for key, count in sorted(track_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        sessions_by_car=[
            HistoryGroupCount(key=key, sessions=count)
            for key, count in sorted(car_counts.items(), key=lambda item: item[1], reverse=True)
        ],
    )


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
