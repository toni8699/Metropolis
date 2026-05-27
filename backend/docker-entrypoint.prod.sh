#!/bin/sh
set -e

echo "Applying Alembic migrations..."
alembic upgrade head

echo "Starting Gunicorn..."
exec gunicorn -c gunicorn.conf.py "${GUNICORN_APP:-run:app}"
