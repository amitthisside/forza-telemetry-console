from typing import Final

from fastapi import APIRouter, FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

METRICS_PAYLOAD: Final[str] = "# TYPE app_up gauge\napp_up 1\n"

app = FastAPI(title="telemetry-ingest", version="0.1.0")
api = APIRouter(prefix="/api/v1")


class ParserSchemaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_name: str = Field(alias="schema")
    minimum_packet_bytes: int


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
    return ParserSchemaResponse(schema_name="forza-telemetry-v1", minimum_packet_bytes=64)


app.include_router(api)
