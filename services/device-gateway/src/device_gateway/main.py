from typing import Final

from fastapi import APIRouter, FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"

app = FastAPI(title="device-gateway", version="0.1.0")
api = APIRouter(prefix="/api/v1")


class DeviceStatus(BaseModel):
    status: str


@api.get("/devices")
def list_devices() -> dict[str, list[dict[str, str]]]:
    return {"devices": []}


@api.post("/devices/test")
def test_device_event() -> dict[str, str]:
    return {"status": "queued"}


@api.get("/devices/status", response_model=DeviceStatus)
def device_status() -> DeviceStatus:
    return DeviceStatus(status="disabled")


@api.get("/devices/adapters")
def list_adapters() -> dict[str, list[str]]:
    return {"adapters": ["serial", "udp", "simulated"]}


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
