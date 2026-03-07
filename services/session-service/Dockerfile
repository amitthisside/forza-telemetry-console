FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /workspace

COPY services/session-service /workspace/services/session-service

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /workspace/services/session-service

USER appuser
EXPOSE 8000
CMD ["uvicorn", "session_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
