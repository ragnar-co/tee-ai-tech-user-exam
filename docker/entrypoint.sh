#!/bin/sh
# 1) Load the CSV into DuckDB (idempotent: same file + reference date = no-op, exit 0).
# 2) Start the dashboard. A failed ingest stops the container (no stale/partial data served).
set -eu

echo "[entrypoint] ingest ${INGEST_INPUT} (reference date ${REFERENCE_DATE})"
python -m src.ingest \
  --input "${INGEST_INPUT}" \
  --reference-date "${REFERENCE_DATE}" \
  --db "${DASH_DB_PATH}"

# One worker: DuckDB access is serialised in-process; threads keep the UI responsive
# while a slow AI call is in flight.
exec gunicorn dashboard.app:server \
  --bind "${DASH_HOST}:${DASH_PORT}" \
  --workers 1 --threads 4 --timeout 120 \
  --access-logfile -
