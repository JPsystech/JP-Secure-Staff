#!/bin/sh
# Production start: run migrations then uvicorn. Use in Docker or manually.
set -e
cd "$(dirname "$0")/.."

echo "Running migrations..."
alembic upgrade head || { echo "Migration failed"; exit 1; }

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
