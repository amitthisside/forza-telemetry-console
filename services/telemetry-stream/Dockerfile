FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /workspace

COPY packages/telemetry-models /workspace/packages/telemetry-models
COPY packages/event-contracts /workspace/packages/event-contracts
COPY services/telemetry-stream /workspace/services/telemetry-stream

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /workspace/packages/telemetry-models \
    && pip install --no-cache-dir /workspace/packages/event-contracts \
    && pip install --no-cache-dir /workspace/services/telemetry-stream

USER appuser
EXPOSE 8000
CMD ["uvicorn", "telemetry_stream.main:app", "--host", "0.0.0.0", "--port", "8000"]
