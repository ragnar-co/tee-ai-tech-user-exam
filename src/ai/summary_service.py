"""PL-02 executive_summary_generate: ST-21..ST-25 orchestration and persistence.

The context builder is injected: ``context_builder(con, project_filter) -> dict`` and must return
at least ``source_run_id`` (int) and ``reference_date`` (date or ISO string) plus the aggregates and
``top_overdue_actions`` that are sent to the model. Nothing is saved if the provider fails.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import closing
from datetime import UTC, date, datetime
from typing import Any

import duckdb

from src.ai.prompt import DRAFT_LABEL, PROMPT_VERSION
from src.ai.provider import MODEL_NAME, PROVIDER_NAME, AIProviderError, ExecutiveSummaryProvider

log = logging.getLogger(__name__)

ContextBuilder = Callable[[duckdb.DuckDBPyConnection, "str | None"], dict[str, Any]]
ConnectionFactory = Callable[[], duckdb.DuckDBPyConnection]

COLUMNS = (
    "summary_id", "created_at", "reference_date", "project_filter", "source_run_id",
    "summary_text", "provider", "model_name", "prompt_version",
)
_SELECT = f"SELECT {', '.join(COLUMNS)} FROM executive_summaries"



def ensure_draft_label(text: str) -> str:
    """ST-24: guarantee the draft label is present."""
    head = text[:200]
    if "ร่าง" in head or "draft" in head.lower():
        return text
    return f"[{DRAFT_LABEL}]\n{text}"


def _row_dict(row: tuple) -> dict[str, Any]:
    return dict(zip(COLUMNS, row, strict=True))


def generate_and_save(
    project_filter: str | None,
    *,
    provider: ExecutiveSummaryProvider,
    context_builder: ContextBuilder,
    connect: ConnectionFactory,
) -> dict[str, Any]:
    """Returns {"ok": True, "row": {...}} or {"ok": False, "error": "<readable message>"}."""
    if hasattr(provider, "is_configured") and not provider.is_configured():
        msg = getattr(provider, "missing_config_message", lambda: "ยังไม่ได้ตั้งค่า AI provider")()
        return {"ok": False, "error": msg}
    try:
        with closing(connect()) as con:
            context = context_builder(con, project_filter)
    except Exception as exc:  # noqa: BLE001  context errors must not crash the dashboard
        log.warning("context build failed (%s)", type(exc).__name__)
        return {"ok": False, "error": "สร้างข้อมูล context จาก DuckDB ไม่สำเร็จ: ยังไม่มีข้อมูลหรือฐานข้อมูลไม่พร้อม"}
    log.info("ai_context_send run=%s model=%s prompt=%s fields=%s",
             context.get("source_run_id"), MODEL_NAME, PROMPT_VERSION, sorted(context))
    try:
        text = provider.generate(context)
    except AIProviderError as exc:
        return {"ok": False, "error": exc.message}
    except Exception as exc:  # noqa: BLE001  unexpected: still no crash, no key in message
        log.warning("provider failed (%s)", type(exc).__name__)
        return {"ok": False, "error": "สร้าง AI Summary ไม่สำเร็จ: เกิดข้อผิดพลาดที่ไม่คาดคิด"}
    text = ensure_draft_label(text)
    ref = context["reference_date"]
    if isinstance(ref, str):
        ref = date.fromisoformat(ref)
    with closing(connect()) as con:
        sid = con.execute("SELECT nextval('seq_summary_id')").fetchone()[0]  # DATA_MODEL_SPEC
        con.execute(
            "INSERT INTO executive_summaries (summary_id, created_at, reference_date, project_filter,"
            " source_run_id, summary_text, provider, model_name, prompt_version)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [sid, datetime.now(UTC).replace(tzinfo=None, microsecond=0), ref, project_filter,
             int(context["source_run_id"]), text, PROVIDER_NAME, MODEL_NAME, PROMPT_VERSION],
        )
        row = con.execute(_SELECT + " WHERE summary_id = ?", [sid]).fetchone()
    return {"ok": True, "row": _row_dict(row)}


def get_latest(connect: ConnectionFactory, project_filter: str | None = None) -> dict[str, Any] | None:
    """Latest summary; project_filter=None means the All Projects summary (project_filter IS NULL)."""
    with closing(connect()) as con:
        if project_filter is None:
            row = con.execute(_SELECT + " WHERE project_filter IS NULL ORDER BY created_at DESC, summary_id DESC LIMIT 1").fetchone()
        else:
            row = con.execute(_SELECT + " WHERE project_filter = ? ORDER BY created_at DESC, summary_id DESC LIMIT 1", [project_filter]).fetchone()
    return _row_dict(row) if row else None


def list_history(connect: ConnectionFactory, limit: int = 10) -> list[dict[str, Any]]:
    with closing(connect()) as con:
        rows = con.execute(_SELECT + " ORDER BY created_at DESC, summary_id DESC LIMIT ?", [int(limit)]).fetchall()
    return [_row_dict(r) for r in rows]
