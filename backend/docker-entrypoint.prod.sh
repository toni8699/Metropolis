#!/bin/sh
set -e

echo "Applying Alembic migrations..."
alembic upgrade head

echo "Starting Gunicorn (Uvicorn workers + Socket.IO ASGI)..."
exec gunicorn metropolis.asgi:app \
  -k uvicorn.workers.UvicornWorker \
  -w "${WEB_CONCURRENCY:-2}" \
  -b "0.0.0.0:${PORT:-8080}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
  --access-logfile "${GUNICORN_ACCESS_LOG:--}" \
  --error-logfile "${GUNICORN_ERROR_LOG:--}" \
  --log-level "${LOG_LEVEL:-info}"
