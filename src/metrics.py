"""Data-access layer for the dashboard (read-only; formulas live only in sql/20_metrics, F2).

Every function takes an optional `project` (None or "All Projects" = no filter), reads the latest
successful run, opens a short-lived read-only DuckDB connection, and returns plain Python data.
With no database / no successful run the results are empty-state safe (zeros / empty lists / None).
The project name is only ever bound as a SQL parameter, never concatenated.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from . import settings
from .db import connect_readonly, fetch_dicts, load_sql

_EMPTY_PORTFOLIO = {
    "total_actions": 0,
    "completed_actions": 0,
    "open_actions": 0,
    "overdue_actions": 0,
    "open_not_overdue_actions": 0,
    "owners_with_overdue_actions": 0,
    "completion_rate": 0,
}


def _normalize_project(project: str | None) -> str | None:
    if project is None or project == settings.ALL_PROJECTS_LABEL:
        return None
    if not isinstance(project, str):
        raise TypeError("project must be a string or None")
    return project


def _connect(db_path):
    """Read-only connection, or None when the DB file or its schema does not exist yet."""
    path = Path(db_path or settings.DB_PATH)
    if not path.exists():
        return None
    return connect_readonly(path)


def _latest_run_id(con) -> int | None:
    try:
        return con.execute(load_sql("20_metrics/latest_run.sql")).fetchone()[0]
    except duckdb.CatalogException:
        return None


def _run_query(sql_file: str, project, db_path, empty):
    name = _normalize_project(project)
    con = _connect(db_path)
    if con is None:
        return empty
    try:
        run_id = _latest_run_id(con)
        if run_id is None:
            return empty
        cur = con.execute(load_sql(sql_file), {"run_id": run_id, "project_name": name})
        return fetch_dicts(cur)
    finally:
        con.close()


def _iso(row: dict, *keys: str) -> dict:
    for k in keys:
        if row.get(k) is not None:
            row[k] = row[k].isoformat()
    return row


def get_run_info(db_path=None) -> dict | None:
    """Latest successful run (reference_date etc. as ISO strings), or None if there is none."""
    con = _connect(db_path)
    if con is None:
        return None
    try:
        run_id = _latest_run_id(con)
        if run_id is None:
            return None
        cur = con.execute("SELECT * FROM ingestion_runs WHERE run_id = ?", [run_id])
        return _iso(fetch_dicts(cur)[0], "reference_date", "started_at", "completed_at")
    finally:
        con.close()


def list_projects(db_path=None) -> list[str]:
    """Distinct project names of the latest successful run (without the 'All Projects' label)."""
    rows = _run_query("20_metrics/q_by_project.sql", None, db_path, [])
    return [r["project_name"] for r in rows]


def portfolio(project: str | None = None, db_path=None) -> dict:
    """Q-PORTFOLIO: MET-01..04, 06, 07, 08 for the scope. Zeros when there is no data."""
    rows = _run_query("20_metrics/q_portfolio.sql", project, db_path, [])
    return rows[0] if rows else dict(_EMPTY_PORTFOLIO)


def by_project(project: str | None = None, db_path=None) -> list[dict]:
    """Q-BY-PROJECT: one dict per project (a project filter returns at most 1)."""
    return _run_query("20_metrics/q_by_project.sql", project, db_path, [])


def overdue_detail(project: str | None = None, db_path=None) -> list[dict]:
    """Q-OVERDUE-DETAIL: overdue actions, most overdue first; due_date as ISO string."""
    rows = _run_query("20_metrics/q_overdue_detail.sql", project, db_path, [])
    return [_iso(r, "due_date") for r in rows]


def by_owner(project: str | None = None, db_path=None) -> list[dict]:
    """Q-BY-OWNER: overdue count per owner (counts only, not a performance score)."""
    return _run_query("20_metrics/q_by_owner.sql", project, db_path, [])


def data_quality_summary(db_path=None) -> dict:
    """Latest successful run, its findings, and the most recent attempt (may have failed).

    Returns {"run": dict|None, "latest_attempt": dict|None, "severity_counts": {...},
    "findings": [{check_name, record_key, severity_class, message}, ...]}.
    """
    empty = {"run": None, "latest_attempt": None, "severity_counts": {}, "findings": []}
    con = _connect(db_path)
    if con is None:
        return empty
    try:
        run_id = _latest_run_id(con)
        try:
            attempt = fetch_dicts(
                con.execute("SELECT * FROM ingestion_runs ORDER BY run_id DESC LIMIT 1")
            )
        except duckdb.CatalogException:
            return empty
        latest_attempt = (
            _iso(attempt[0], "reference_date", "started_at", "completed_at") if attempt else None
        )
        if run_id is None:
            return {**empty, "latest_attempt": latest_attempt}
        run = _iso(
            fetch_dicts(con.execute("SELECT * FROM ingestion_runs WHERE run_id = ?", [run_id]))[0],
            "reference_date", "started_at", "completed_at",
        )
        findings = fetch_dicts(
            con.execute(
                "SELECT check_name, record_key, severity_class, message FROM data_quality_results "
                "WHERE run_id = ? ORDER BY check_name, quality_result_id",
                [run_id],
            )
        )
        counts: dict[str, int] = {}
        for f in findings:
            counts[f["severity_class"]] = counts.get(f["severity_class"], 0) + 1
        return {
            "run": run,
            "latest_attempt": latest_attempt,
            "severity_counts": counts,
            "findings": findings,
        }
    finally:
        con.close()
