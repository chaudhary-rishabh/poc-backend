# syntax=docker/dockerfile:1

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim AS runtime

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

COPY --from=builder /install /usr/local

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini

RUN chown -R app:app /app
USER app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

# Shell form (not exec-array) so $PORT is substituted at container start —
# Cloud Run injects PORT dynamically per revision, it isn't known at build time.
# --timeout-keep-alive raised to 900s (15 min) to match the LLM provider client
# timeouts and the Cloud Run --timeout deploy flag — long high-effort generation
# calls must not be cut short by a short keep-alive default.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 900
