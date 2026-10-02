"""DuckDB connection helpers (single writer = ingest; dashboard is read-only; CON-15 / F8)."""

from __future__ import annotations

from pathlib import Path

import duckdb

from . import settings


def connect_writer(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open the warehouse for writing (ingest only). Creates the parent directory."""
    path = Path(db_path or settings.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def connect_readonly(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open the warehouse read-only (dashboard / data-access layer)."""
    return duckdb.connect(str(Path(db_path or settings.DB_PATH)), read_only=True)


def load_sql(relative_path: str) -> str:
    """Read a SQL file under sql/ (metric formulas live only in these files; F2)."""
    return (settings.SQL_DIR / relative_path).read_text(encoding="utf-8")


def fetch_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict]:
    """Turn the pending result of `cursor` into a list of dicts."""
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in cursor.fetchall()]
