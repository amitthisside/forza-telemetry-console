from typing import Final

from fastapi import FastAPI, WebSocket
from fastapi.responses import Response

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"
app = FastAPI(title="telemetry-stream", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=METRICS_PAYLOAD, media_type="text/plain; version=0.0.4")


@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected", "channel": "telemetry"})
    await websocket.close()


@app.websocket("/ws/overlay")
async def ws_overlay(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected", "channel": "overlay"})
    await websocket.close()
