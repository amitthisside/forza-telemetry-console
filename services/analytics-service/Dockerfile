FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /workspace

COPY services/analytics-service /workspace/services/analytics-service

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /workspace/services/analytics-service

USER appuser
EXPOSE 8000
CMD ["uvicorn", "analytics_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
