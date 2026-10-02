"""ST-21/ST-22: structured context for the executive summary drafter (PL-02).

Built ONLY from src.metrics (Q-PORTFOLIO, Q-BY-PROJECT, Q-OVERDUE-DETAIL): no raw CSV, no key, no
full table. ``top_overdue_actions`` is limited to the top-N rows by days_overdue (desc); owner and
action_name are sent only inside those rows (GOV-AI-01; a user decision, not a DPO/legal approval).

Config (environment only):
  AI_TOP_N  optional positive int; default DEFAULT_TOP_N. The docs leave N = null (calibrate later
            on context size / cost / PDPA policy); 10 is a deliberately small interim default.

The ``con`` argument of ``build_context`` is accepted for the summary_service contract but unused:
metrics opens its own short-lived read-only connection (so a write connection must NOT be open on
the same file in this process while the context is built).
"""

from __future__ import annotations

import os
import re
from typing import Any

from src import metrics, settings

DEFAULT_TOP_N = 10  # interim documented default (docs: null = calibrate later)
TOP_FIELDS = ("action_id", "project_name", "action_name", "owner", "due_date", "days_overdue")


MAX_TEXT_LEN = 200  # cap (chars) for every free-text field sent to the model (prompt-injection hardening)
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]")
_TEXT_FIELDS = ("action_name", "owner", "project_name")


def sanitize_text(value: Any, limit: int = MAX_TEXT_LEN) -> Any:
    """Strip control characters (incl. newlines/tabs) and cap length; non-str passes through."""
    if not isinstance(value, str):
        return value
    return _CONTROL_CHARS.sub(" ", value).strip()[:limit]


def _clean_row(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {k: sanitize_text(row.get(k)) if k in _TEXT_FIELDS else row.get(k) for k in fields}


def top_n() -> int:
    """N for top_overdue_actions: AI_TOP_N if a positive integer, else DEFAULT_TOP_N."""
    try:
        n = int(os.environ.get("AI_TOP_N", ""))
    except ValueError:
        return DEFAULT_TOP_N
    return n if n > 0 else DEFAULT_TOP_N


def build_context(con: Any, project_filter: str | None, *, db_path=None) -> dict[str, Any]:
    """Context dict for the provider. Raises ValueError when there is no successful run."""
    run = metrics.get_run_info(db_path)
    if run is None:
        raise ValueError("no successful ingestion run")
    if project_filter == settings.ALL_PROJECTS_LABEL:
        project_filter = None
    n = top_n()
    overdue = sorted(  # stable: keeps the SQL tie-break order
        metrics.overdue_detail(project_filter, db_path), key=lambda r: -(r.get("days_overdue") or 0)
    )
    return {
        "source_run_id": run["run_id"],
        "reference_date": run["reference_date"],
        "project_filter": project_filter or None,
        "portfolio": metrics.portfolio(project_filter, db_path),
        "projects": [dict(r, **{k: sanitize_text(r[k]) for k in _TEXT_FIELDS if k in r})
                     for r in metrics.by_project(project_filter, db_path)],
        "top_overdue_actions": [_clean_row(r, TOP_FIELDS) for r in overdue[:n]],
        "top_n": n,
        "overdue_total": len(overdue),
    }
