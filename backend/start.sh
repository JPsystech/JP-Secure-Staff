#!/usr/bin/env bash
# Production start for Railway: migrations then uvicorn. PORT must be a valid integer.
set -e

# PORT: Railway injects PORT at runtime. uvicorn requires a literal integer (no $PORT string).
# Default 8000 if unset or not numeric; prevents "Invalid value for '--port': '$PORT' is not a valid integer".
PORT_NUM=8000
if [[ -n "${PORT}" ]] && [[ "${PORT}" =~ ^[0-9]+$ ]]; then
  PORT_NUM="${PORT}"
fi

echo "Running migrations..."
alembic upgrade head

echo "Starting uvicorn on 0.0.0.0:${PORT_NUM}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_NUM}"
