import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Final

from event_contracts import TelemetryFrameEvent
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from forza_parser import SUPPORTED_PACKET_SIZES
from pydantic import BaseModel, ConfigDict, Field

from telemetry_ingest.config import IngestSettings
from telemetry_ingest.ingest_runtime import IngestStats, start_udp_listener

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"
logger = logging.getLogger(__name__)

settings = IngestSettings.from_env()
stats = IngestStats()


@asynccontextmanager
async def lifespan(_: FastAPI):
    transport = None
    nats_client = None

    def publish_event(_event: TelemetryFrameEvent) -> None:
        return None

    if settings.nats_enabled:
        try:
            import nats

            nats_client = await nats.connect(servers=[settings.nats_url], name="telemetry-ingest")

            def publish_event(event: TelemetryFrameEvent) -> None:
                payload = event.model_dump_json().encode("utf-8")
                asyncio.create_task(nats_client.publish(settings.telemetry_subject, payload))
        except Exception as exc:  # pragma: no cover - network failure path
            logger.warning("NATS publish disabled due to connection error: %s", exc)
            stats.publish_errors += 1

    if settings.udp_enabled:
        transport = await start_udp_listener(
            settings.bind_host,
            settings.bind_port,
            stats,
            source=settings.source,
            session_id=settings.session_id,
            event_publisher=publish_event if settings.nats_enabled else None,
        )
    try:
        yield
    finally:
        if transport is not None:
            transport.close()
        if nats_client is not None:
            await nats_client.close()


app = FastAPI(title="telemetry-ingest", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
api = APIRouter(prefix="/api/v1")


class ParserSchemaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_name: str = Field(alias="schema")
    minimum_packet_bytes: int
    supported_packet_sizes: list[int]


class IngestStatsResponse(BaseModel):
    packets_received: int
    packets_decoded: int
    parser_errors: int
    events_published: int
    publish_errors: int
    udp_enabled: bool
    nats_enabled: bool
    bind_host: str
    bind_port: int


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=METRICS_PAYLOAD, media_type="text/plain; version=0.0.4")


@api.get("/parser/schema", response_model=ParserSchemaResponse)
def parser_schema() -> ParserSchemaResponse:
    return ParserSchemaResponse(
        schema_name="forza-telemetry-v1",
        minimum_packet_bytes=min(SUPPORTED_PACKET_SIZES),
        supported_packet_sizes=sorted(SUPPORTED_PACKET_SIZES),
    )


@api.get("/ingest/stats", response_model=IngestStatsResponse)
def ingest_stats() -> IngestStatsResponse:
    return IngestStatsResponse(
        packets_received=stats.packets_received,
        packets_decoded=stats.packets_decoded,
        parser_errors=stats.parser_errors,
        events_published=stats.events_published,
        publish_errors=stats.publish_errors,
        udp_enabled=settings.udp_enabled,
        nats_enabled=settings.nats_enabled,
        bind_host=settings.bind_host,
        bind_port=settings.bind_port,
    )


app.include_router(api)
