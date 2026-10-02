# syntax=docker/dockerfile:1
# Cybersecurity Project Action Dashboard — Dash + DuckDB, served by gunicorn.
# Build:  docker build -t cybersecurity-action-dashboard .
# Run:    docker compose up --build        (see docker-compose.yml)

# ---- Stage 1: dependencies (cached layer; project code is NOT pip-installed,
#      the app reads sql/ and data/ relative to its source tree) -------------
FROM python:3.12-slim AS deps
WORKDIR /build
COPY pyproject.toml .
RUN python -c "import tomllib; d = tomllib.load(open('pyproject.toml','rb'))['project']; \
print('\n'.join(d['dependencies'] + d['optional-dependencies']['prod']))" > requirements.txt \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: runtime image -------------------------------------------------
FROM python:3.12-slim AS runner
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DASH_HOST=0.0.0.0 \
    DASH_PORT=8050 \
    DASH_DB_PATH=/app/data/cybersecurity.duckdb \
    INGEST_INPUT=/app/src/tee_cybersecurity_actions_mock.csv \
    REFERENCE_DATE=2026-10-02

COPY --from=deps /install /usr/local
COPY src/ ./src/
COPY sql/ ./sql/
COPY dashboard/ ./dashboard/
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

# Non-root user; /app/data holds the DuckDB file (mount a volume here).
RUN useradd --create-home --uid 1001 appuser \
 && mkdir -p /app/data \
 && chown -R appuser:appuser /app \
 && chmod +x /usr/local/bin/entrypoint.sh
USER appuser

EXPOSE 8050

# Dash serves its layout at /_dash-layout (no dedicated health route needed).
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import os,urllib.request as u; u.urlopen('http://127.0.0.1:%s/_dash-layout' % os.environ.get('DASH_PORT','8050'), timeout=4)" || exit 1

ENTRYPOINT ["entrypoint.sh"]
