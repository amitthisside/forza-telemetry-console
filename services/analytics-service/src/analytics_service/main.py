from typing import Final

from fastapi import FastAPI
from fastapi.responses import Response

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"
app = FastAPI(title="analytics-service", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=METRICS_PAYLOAD, media_type="text/plain; version=0.0.4")


@app.get("/analysis/sessions/{session_id}")
def session_analysis(session_id: str) -> dict[str, str]:
    return {"session_id": session_id, "status": "not_implemented"}


@app.get("/history/summary")
def history_summary() -> dict[str, str]:
    return {"status": "not_implemented"}
