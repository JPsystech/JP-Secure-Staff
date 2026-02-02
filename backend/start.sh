#!/usr/bin/env bash
# Production start: migrations then uvicorn. Railway sets PORT; default 8000.
set -e

# PORT: Railway injects PORT at runtime. Must be a positive integer for uvicorn.
# Use default 8000 if unset or not a number (avoids "$PORT is not a valid integer").
if [[ -z "${PORT}" ]] || ! [[ "${PORT}" =~ ^[0-9]+$ ]]; then
  export PORT=8000
fi

echo "Running migrations..."
alembic upgrade head

echo "Starting uvicorn on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
