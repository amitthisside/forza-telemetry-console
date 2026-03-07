from typing import Final

from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import Response
from pydantic import BaseModel

from analytics_service.rules import (
    CoachingMessage,
    DiagnosticSignal,
    SessionSignalSnapshot,
    evaluate_coaching,
    evaluate_diagnostics,
)

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"

app = FastAPI(title="analytics-service", version="0.1.0")
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


@api.get("/analysis/sessions/{session_id}", response_model=AnalysisResponse)
def session_analysis(
    session_id: str,
    brake_release_variance: float = Query(default=0.0, ge=0.0),
    rear_slip_events: int = Query(default=0, ge=0),
    early_throttle_pct: float = Query(default=0.0, ge=0.0, le=1.0),
    exit_speed_delta_kmh: float = 0.0,
) -> AnalysisResponse:
    snapshot = build_snapshot(
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
def coaching_for_session(
    session_id: str,
    brake_release_variance: float = Query(default=0.0, ge=0.0),
    rear_slip_events: int = Query(default=0, ge=0),
    early_throttle_pct: float = Query(default=0.0, ge=0.0, le=1.0),
    exit_speed_delta_kmh: float = 0.0,
) -> dict[str, list[CoachingMessage]]:
    _ = session_id
    snapshot = build_snapshot(
        brake_release_variance,
        rear_slip_events,
        early_throttle_pct,
        exit_speed_delta_kmh,
    )
    return {"messages": evaluate_coaching(snapshot)}


@api.get("/diagnostics/sessions/{session_id}")
def diagnostics_for_session(
    session_id: str,
    rear_slip_events: int = Query(default=0, ge=0),
    exit_speed_delta_kmh: float = 0.0,
) -> dict[str, list[DiagnosticSignal]]:
    _ = session_id
    snapshot = build_snapshot(0.0, rear_slip_events, 0.0, exit_speed_delta_kmh)
    return {"diagnostics": evaluate_diagnostics(snapshot)}


@api.get("/history/summary", response_model=HistorySummary)
def history_summary() -> HistorySummary:
    return HistorySummary(sessions=0, best_lap_ms=None, consistency_score=0.0)


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
