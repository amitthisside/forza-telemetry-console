from typing import Final

from fastapi import APIRouter, FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"

app = FastAPI(title="session-service", version="0.1.0")
api = APIRouter(prefix="/api/v1")


class SessionSummary(BaseModel):
    session_id: str
    started_at: str
    ended_at: str | None = None


class LapSummary(BaseModel):
    lap_id: str
    lap_number: int


@api.get("/sessions", response_model=list[SessionSummary])
def list_sessions() -> list[SessionSummary]:
    return []


@api.get("/sessions/{session_id}", response_model=SessionSummary)
def get_session(session_id: str) -> SessionSummary:
    return SessionSummary(session_id=session_id, started_at="not_implemented")


@api.get("/sessions/{session_id}/laps", response_model=list[LapSummary])
def get_session_laps(session_id: str) -> list[LapSummary]:
    _ = session_id
    return []


@api.get("/sessions/{session_id}/frames")
def get_session_frames(session_id: str) -> dict[str, list[dict[str, str]]]:
    _ = session_id
    return {"frames": []}


@api.get("/sessions/{session_id}/export/json")
def export_session_json(session_id: str) -> dict[str, str]:
    return {"session_id": session_id, "format": "json"}


@api.get("/sessions/{session_id}/export/csv")
def export_session_csv(session_id: str) -> Response:
    payload = f"session_id,format\n{session_id},csv\n"
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
