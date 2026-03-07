import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Final

from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field

from telemetry_stream.config import StreamSettings
from telemetry_stream.consumer import consume_telemetry_subject
from telemetry_stream.hub import WebSocketHub
from telemetry_stream.ring_buffer import FrameRingBuffer

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"

settings = StreamSettings.from_env()
ring_buffer = FrameRingBuffer(settings.ring_buffer_size)
hub = WebSocketHub(settings.subscriber_queue_size)


@dataclass
class StreamStats:
    frames_ingested: int = 0
    frames_broadcast: int = 0


stats = StreamStats()
latest_frame: dict[str, object] | None = None
stop_event = asyncio.Event()
consumer_task: asyncio.Task[None] | None = None


class StreamChannelsResponse(BaseModel):
    channels: list[str]


class StreamStatsResponse(BaseModel):
    frames_ingested: int
    frames_broadcast: int
    telemetry_subscribers: int
    overlay_subscribers: int


class RecentFramesResponse(BaseModel):
    frames: list[dict[str, object]] = Field(default_factory=list)


class OverlayStateResponse(BaseModel):
    connected: bool
    frame: dict[str, object] | None = None



def publish_frame(frame: dict[str, object]) -> None:
    global latest_frame
    stats.frames_ingested += 1
    latest_frame = frame
    ring_buffer.append(frame)
    stats.frames_broadcast += hub.broadcast("telemetry", frame)
    stats.frames_broadcast += hub.broadcast("overlay", frame)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global consumer_task

    if settings.nats_enabled:
        stop_event.clear()
        consumer_task = asyncio.create_task(
            consume_telemetry_subject(
                nats_url=settings.nats_url,
                subject=settings.telemetry_subject,
                on_frame=publish_frame,
                stop_event=stop_event,
            )
        )
    try:
        yield
    finally:
        if consumer_task is not None:
            stop_event.set()
            await consumer_task


app = FastAPI(title="telemetry-stream", version="0.1.0", lifespan=lifespan)
api = APIRouter(prefix="/api/v1")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=METRICS_PAYLOAD, media_type="text/plain; version=0.0.4")


@api.get("/streams/channels", response_model=StreamChannelsResponse)
def list_stream_channels() -> StreamChannelsResponse:
    return StreamChannelsResponse(channels=["dashboard", "overlay", "diagnostics-preview"])


@api.get("/streams/stats", response_model=StreamStatsResponse)
def stream_stats() -> StreamStatsResponse:
    return StreamStatsResponse(
        frames_ingested=stats.frames_ingested,
        frames_broadcast=stats.frames_broadcast,
        telemetry_subscribers=hub.subscriber_count("telemetry"),
        overlay_subscribers=hub.subscriber_count("overlay"),
    )


@api.get("/streams/recent", response_model=RecentFramesResponse)
def recent_frames(limit: int = 20) -> RecentFramesResponse:
    safe_limit = max(1, min(limit, 200))
    return RecentFramesResponse(frames=ring_buffer.recent(safe_limit))


@api.get("/overlay/state", response_model=OverlayStateResponse)
def overlay_state() -> OverlayStateResponse:
    return OverlayStateResponse(
        connected=hub.subscriber_count("overlay") > 0,
        frame=latest_frame,
    )


@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket) -> None:
    await _handle_websocket_channel(websocket, "telemetry")


@app.websocket("/ws/overlay")
async def ws_overlay(websocket: WebSocket) -> None:
    await _handle_websocket_channel(websocket, "overlay")


async def _handle_websocket_channel(websocket: WebSocket, channel: str) -> None:
    await websocket.accept()
    queue = hub.subscribe(channel)
    try:
        await websocket.send_json({"type": "connected", "channel": channel})
        for frame in ring_buffer.recent(10):
            await websocket.send_json({"type": "frame", "channel": channel, "data": frame})

        while True:
            message = await queue.get()
            await websocket.send_json({"type": "frame", "channel": channel, "data": message})
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(channel, queue)


app.include_router(api)
