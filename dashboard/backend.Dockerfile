FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY dashboard/app/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY dashboard/app/backend /app/dashboard/app/backend
COPY artifacts/models /app/artifacts/models

WORKDIR /app/dashboard/app/backend

ENV MODEL_ARTIFACTS_PATH=/app/artifacts/models

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
