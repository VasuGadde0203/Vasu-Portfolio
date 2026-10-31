FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY knowledge ./knowledge
COPY scripts ./scripts

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Railway injects PORT. Migrations are idempotent; ingestion is a separate, explicit step.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app_factory --factory --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
