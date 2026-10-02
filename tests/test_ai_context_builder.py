"""ST-21/ST-22 context builder: built only from src.metrics, top-N, no key (T-A04, T-A05)."""

from __future__ import annotations

import json

import pytest

from src import metrics
from src.ai import context_builder as cb

FIELDS = {"action_id", "project_name", "action_name", "owner", "due_date", "days_overdue"}


def test_all_projects_context_matches_metrics(golden_db):
    ctx = cb.build_context(None, None, db_path=golden_db)
    assert ctx["source_run_id"] == 1 and ctx["reference_date"] == "2026-09-15"
    assert ctx["project_filter"] is None
    assert ctx["portfolio"] == metrics.portfolio(None, golden_db)
    assert ctx["projects"] == metrics.by_project(None, golden_db)
    detail = metrics.overdue_detail(None, golden_db)
    assert [a["action_id"] for a in ctx["top_overdue_actions"]] == [d["action_id"] for d in detail]
    assert all(set(a) == FIELDS for a in ctx["top_overdue_actions"])
    assert ctx["overdue_total"] == len(detail)


def test_project_filter_and_all_label(golden_db):
    proj = metrics.list_projects(golden_db)[0]
    ctx = cb.build_context(None, proj, db_path=golden_db)
    assert ctx["project_filter"] == proj
    assert {p["project_name"] for p in ctx["projects"]} == {proj}
    assert {a["project_name"] for a in ctx["top_overdue_actions"]} <= {proj}
    assert cb.build_context(None, "All Projects", db_path=golden_db)["project_filter"] is None


def test_top_n_default_env_and_invalid(golden_db, monkeypatch):
    monkeypatch.delenv("AI_TOP_N", raising=False)
    assert cb.top_n() == cb.DEFAULT_TOP_N
    monkeypatch.setenv("AI_TOP_N", "2")
    ctx = cb.build_context(None, None, db_path=golden_db)
    days = [a["days_overdue"] for a in ctx["top_overdue_actions"]]
    assert len(days) == min(2, ctx["overdue_total"]) and days == sorted(days, reverse=True)
    for bad in ("abc", "0", "-3"):
        monkeypatch.setenv("AI_TOP_N", bad)
        assert cb.top_n() == cb.DEFAULT_TOP_N


def test_no_run_raises_and_no_secret(tmp_path, golden_db, monkeypatch):
    with pytest.raises(ValueError):
        cb.build_context(None, None, db_path=tmp_path / "none.duckdb")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-SENTINEL")
    assert "sk-SENTINEL" not in json.dumps(cb.build_context(None, None, db_path=golden_db))
