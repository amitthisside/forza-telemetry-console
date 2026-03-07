FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY pyproject.toml /app/
COPY src /app/src
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

USER appuser
EXPOSE 8000
CMD ["uvicorn", "device_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
