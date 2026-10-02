"""PL-02 persistence tests against a temp DuckDB (T-A01, T-A02, T-A03, T-A05)."""

from __future__ import annotations

import logging
from datetime import date

import duckdb
import httpx
import pytest

from src.ai import summary_service as svc
from src.ai.prompt import PROMPT_VERSION
from src.ai.provider import MODEL_NAME, OpenRouterProvider

KEY = "sk-SENTINEL-DUMMY-0000"
BASE = "https://mock.example/api/v1"

DDL = """CREATE SEQUENCE seq_summary_id START 1;
CREATE TABLE executive_summaries (
 summary_id BIGINT PRIMARY KEY DEFAULT nextval('seq_summary_id'), created_at TIMESTAMP NOT NULL, reference_date DATE NOT NULL,
 project_filter VARCHAR, source_run_id BIGINT NOT NULL, summary_text VARCHAR NOT NULL,
 provider VARCHAR NOT NULL, model_name VARCHAR NOT NULL, prompt_version VARCHAR NOT NULL)"""


@pytest.fixture
def connect(tmp_path):
    path = str(tmp_path / "t.duckdb")
    con = duckdb.connect(path)
    con.execute(DDL)
    con.close()
    return lambda: duckdb.connect(path)


def builder(con, project_filter):
    return {"source_run_id": 7, "reference_date": date(2026, 9, 15), "project_filter": project_filter,
            "aggregates": {"overdue": 2}, "top_overdue_actions": [{"owner": "Owner-001"}]}


def provider(handler, key=KEY, base=BASE):
    return OpenRouterProvider(api_key=key, base_url=base, transport=httpx.MockTransport(handler))


def ok(text="ร่าง (DRAFT) สรุปผล"):
    return lambda r: httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def all_rows(connect):
    con = connect()
    try:
        return con.execute("SELECT * FROM executive_summaries ORDER BY summary_id").fetchall()
    finally:
        con.close()


def test_success_saves_row(connect):
    res = svc.generate_and_save(None, provider=provider(ok()), context_builder=builder, connect=connect)
    assert res["ok"]
    row = res["row"]
    assert row["summary_id"] == 1 and row["source_run_id"] == 7
    assert row["reference_date"] == date(2026, 9, 15)
    assert row["project_filter"] is None
    assert row["provider"] == "openrouter" and row["model_name"] == MODEL_NAME
    assert row["prompt_version"] == PROMPT_VERSION and row["created_at"] is not None
    assert len(all_rows(connect)) == 1


def test_draft_label_added_when_missing(connect):
    res = svc.generate_and_save("P01", provider=provider(ok("สรุปเฉยๆ")), context_builder=builder, connect=connect)
    assert "DRAFT" in res["row"]["summary_text"]
    assert res["row"]["project_filter"] == "P01"


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500, 503])
def test_http_failure_saves_nothing(connect, status):
    res = svc.generate_and_save(None, provider=provider(lambda r: httpx.Response(status)), context_builder=builder, connect=connect)
    assert not res["ok"] and str(status) in res["error"] and "Traceback" not in res["error"]
    assert all_rows(connect) == []


def test_timeout_saves_nothing(connect):
    def h(r):
        raise httpx.ConnectTimeout("t", request=r)

    res = svc.generate_and_save(None, provider=provider(h), context_builder=builder, connect=connect)
    assert not res["ok"] and all_rows(connect) == []


@pytest.mark.parametrize("key,base", [("", BASE), (KEY, ""), ("", "")])
def test_unconfigured_no_http_no_row(connect, key, base):
    calls = []
    p = provider(lambda r: calls.append(r) or httpx.Response(200), key, base)
    res = svc.generate_and_save(None, provider=p, context_builder=builder, connect=connect)
    assert not res["ok"] and "OPENAI" in res["error"]
    assert calls == [] and all_rows(connect) == []


def test_context_builder_failure_no_crash(connect):
    def bad(con, pf):
        raise RuntimeError("no run")

    res = svc.generate_and_save(None, provider=provider(ok()), context_builder=bad, connect=connect)
    assert not res["ok"] and all_rows(connect) == []


def test_latest_and_history(connect):
    for pf in (None, "P01", None):
        svc.generate_and_save(pf, provider=provider(ok()), context_builder=builder, connect=connect)
    assert svc.get_latest(connect)["summary_id"] == 3
    assert svc.get_latest(connect, "P01")["summary_id"] == 2
    assert svc.get_latest(connect, "P99") is None
    hist = svc.list_history(connect, limit=2)
    assert [r["summary_id"] for r in hist] == [3, 2]


def test_key_sentinel_never_in_rows_or_logs(connect, caplog):
    caplog.set_level(logging.DEBUG)
    svc.generate_and_save(None, provider=provider(ok()), context_builder=builder, connect=connect)
    svc.generate_and_save(None, provider=provider(lambda r: httpx.Response(401, text=KEY)), context_builder=builder, connect=connect)
    assert KEY not in repr(all_rows(connect))
    assert KEY not in caplog.text


def test_summary_ids_unique_under_repeated_saves(connect):
    ids = []
    for _ in range(4):
        r = svc.generate_and_save(None, provider=provider(lambda req: httpx.Response(
            200, json={"choices": [{"message": {"content": "ร่าง ok"}}]})),
            context_builder=builder, connect=connect)
        assert r["ok"], r
        ids.append(r["row"]["summary_id"])
    assert ids == sorted(set(ids)) and len(ids) == 4
