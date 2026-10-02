"""Independent pure-Python metric calculator (T-F01 / T-X01): METRIC_SPEC formulas, no DuckDB."""

from __future__ import annotations

import csv
from datetime import date


def load(path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def flags(row: dict, ref: date) -> dict:
    due = date.fromisoformat(row["due_date"])
    done = row["status"] == "done"
    overdue = (not done) and due < ref
    return {
        "is_completed": done,
        "is_open": not done,
        "is_overdue": overdue,
        "days_overdue": (ref - due).days if overdue else 0,
    }


def portfolio(rows: list[dict], ref: date, project: str | None = None) -> dict:
    rs = [(r, flags(r, ref)) for r in rows if project is None or r["project_name"] == project]
    total = len(rs)
    completed = sum(f["is_completed"] for _, f in rs)
    overdue = sum(f["is_overdue"] for _, f in rs)
    opened = sum(f["is_open"] for _, f in rs)
    return {
        "total_actions": total,
        "completed_actions": completed,
        "open_actions": opened,
        "overdue_actions": overdue,
        "open_not_overdue_actions": opened - overdue,
        "owners_with_overdue_actions": len({r["owner"] for r, f in rs if f["is_overdue"]}),
        "completion_rate": completed / total if total else 0,
        "max_days_overdue": max((f["days_overdue"] for _, f in rs if f["is_overdue"]), default=0),
    }
