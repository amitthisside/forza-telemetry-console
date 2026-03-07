from typing import Final

from fastapi import APIRouter, FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"

app = FastAPI(title="analytics-service", version="0.1.0")
api = APIRouter(prefix="/api/v1")


class AnalysisResponse(BaseModel):
    session_id: str
    status: str


class HistorySummary(BaseModel):
    sessions: int
    best_lap_ms: int | None = None


@api.get("/analysis/sessions/{session_id}", response_model=AnalysisResponse)
def session_analysis(session_id: str) -> AnalysisResponse:
    return AnalysisResponse(session_id=session_id, status="not_implemented")


@api.get("/analysis/laps/{lap_id}")
def lap_analysis(lap_id: str) -> dict[str, str]:
    return {"lap_id": lap_id, "status": "not_implemented"}


@api.get("/coaching/sessions/{session_id}")
def coaching_for_session(session_id: str) -> dict[str, list[dict[str, str]]]:
    _ = session_id
    return {"messages": []}


@api.get("/diagnostics/sessions/{session_id}")
def diagnostics_for_session(session_id: str) -> dict[str, list[dict[str, str]]]:
    _ = session_id
    return {"diagnostics": []}


@api.get("/history/summary", response_model=HistorySummary)
def history_summary() -> HistorySummary:
    return HistorySummary(sessions=0)


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
