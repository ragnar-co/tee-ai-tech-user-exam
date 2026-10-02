"""DASH-01/02/03 app tests (TESTING_STRATEGY T-D01..T-D11, T-A01..T-A04 via the UI).

Callbacks are exercised through the Flask test client (POST /_dash-update-component), i.e. the
same path the browser uses. The AI provider is always an httpx.MockTransport: never real network.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb
import httpx
import pytest
from plotly.utils import PlotlyJSONEncoder

import dashboard.app as dash_app
from dashboard.components import cards
from dashboard.viz_theme import ALL_PROJECTS, IDS
from src import metrics
from src.ai import summary_service
from src.ai.provider import MODEL_NAME, OpenRouterProvider

KEY = "sk-SENTINEL-DUMMY-1234"
BASE = "https://mock.example/api/v1"
ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.integration


# --------------------------------------------------------------------------- helpers
def call(app, output_id, values, triggered=None):
    """POST to /_dash-update-component for the callback that owns `output_id.children`."""
    key, spec = next((k, v) for k, v in app.callback_map.items() if f"{output_id}." in k)
    inputs = [{"id": i["id"], "property": i["property"], "value": values.get(i["id"])}
              for i in spec["inputs"]]
    outs = [{"id": o.split(".")[0], "property": o.split(".")[1]}
            for o in key.strip(".").split("...")] if key.startswith("..") else [
        {"id": key.rsplit(".", 1)[0], "property": key.rsplit(".", 1)[1]}]
    body = {"output": key, "outputs": outs if len(outs) > 1 else outs[0], "inputs": inputs,
            "changedPropIds": [f"{triggered or inputs[0]['id']}.{spec['inputs'][0]['property']}"
                               if not triggered else triggered]}
    resp = app.server.test_client().post("/_dash-update-component", json=body)
    assert resp.status_code == 200, resp.get_data(as_text=True)[:500]
    return resp.get_json()["response"]


def find(node, cid):
    """First component with props.id == cid in a serialised Dash tree."""
    if isinstance(node, dict):
        if node.get("props", {}).get("id") == cid:
            return node
        for v in node.values():
            r = find(v, cid)
            if r is not None:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find(v, cid)
            if r is not None:
                return r
    return None


def text(node) -> str:
    """All string content of a serialised tree."""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        return " ".join(text(v) for v in node.values())
    if isinstance(node, list):
        return " ".join(text(v) for v in node)
    return ""


def graph_ys(block) -> list[list[str]]:
    return [list(t.get("y") or []) for t in block["props"]["figure"]["data"]]


def vals(project=ALL_PROJECTS, **kw):
    return {IDS.PROJECT_DROPDOWN: project, IDS.THEME_MODE: "light", IDS.CVD_TOGGLE: [],
            IDS.COMPOSITION_TOGGLE: [], **kw}


def norm(p):
    return None if p == ALL_PROJECTS else p


def kpi_value(tree, cid) -> str:
    card = find(tree, cid)
    assert card is not None, cid
    return card["props"]["children"][1]["props"]["children"]


@pytest.fixture
def app(golden_db):
    return dash_app.create_app(golden_db, provider=_provider(lambda r: _ok(r)))


def _ok(request):
    return httpx.Response(200, json={"choices": [{"message": {"content": "สรุปจาก mock"}}]})


def _provider(handler, key=KEY, base=BASE):
    return OpenRouterProvider(api_key=key, base_url=base, transport=httpx.MockTransport(handler))


# --------------------------------------------------------------------------- T-D01 / T-D02
def test_td01_app_imports_and_serves(app):
    assert dash_app.app is not None and dash_app.server is dash_app.app.server
    c = app.server.test_client()
    assert c.get("/").status_code == 200
    layout = c.get("/_dash-layout")
    assert layout.status_code == 200
    ids = {n["props"].get("id") for n in _walk(layout.get_json()) if "props" in n}
    for need in (IDS.PROJECT_DROPDOWN, IDS.THEME_MODE, IDS.CVD_TOGGLE, IDS.COMPOSITION_TOGGLE,
                 IDS.HEADER, IDS.DQ_PANEL, IDS.EXEC_GENERATE_BTN):
        assert need in ids
    for path in ("/overdue", "/executive-summary"):
        assert c.get(path).status_code == 200


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def test_td02_project_selector_options(app, golden_db):
    tree = app.server.test_client().get("/_dash-layout").get_json()
    dd = find(tree, IDS.PROJECT_DROPDOWN)["props"]
    projects = metrics.list_projects(golden_db)
    assert len(projects) == 3
    assert [o["value"] for o in dd["options"]] == [ALL_PROJECTS, *projects]
    assert dd["value"] == ALL_PROJECTS and dd["clearable"] is False


# --------------------------------------------------------------------------- T-D03 / T-D04 / T-D05
def test_td03_all_projects_kpis_match_metrics(app, golden_db):
    pf = metrics.portfolio(None, golden_db)
    ov = call(app, "ov-kpi", vals())["ov-kpi"]["children"]
    assert kpi_value(ov, IDS.KPI_TOTAL) == f"{pf['total_actions']:,}"
    assert kpi_value(ov, IDS.KPI_COMPLETED) == f"{pf['completed_actions']:,}"
    assert kpi_value(ov, IDS.KPI_OPEN) == f"{pf['open_actions']:,}"
    assert kpi_value(ov, IDS.KPI_OVERDUE) == f"{pf['overdue_actions']:,}"
    assert kpi_value(ov, IDS.KPI_COMPLETION_RATE) == f"{pf['completion_rate'] * 100:.1f}%"
    od = call(app, "od-kpi", vals())["od-kpi"]["children"]
    assert kpi_value(od, IDS.KPI_OVERDUE_D2) == f"{pf['overdue_actions']:,}"
    assert kpi_value(od, IDS.KPI_OWNERS_OVERDUE) == f"{pf['owners_with_overdue_actions']:,}"


def test_td04_single_project_restricts_everything(app, golden_db):
    for proj in metrics.list_projects(golden_db):
        pf = metrics.portfolio(proj, golden_db)
        r = call(app, "ov-kpi", vals(proj))
        assert kpi_value(r["ov-kpi"]["children"], IDS.KPI_TOTAL) == f"{pf['total_actions']:,}"
        assert kpi_value(r["ov-kpi"]["children"], IDS.KPI_OVERDUE) == f"{pf['overdue_actions']:,}"
        for cid in (IDS.CH_TOTAL_BY_PROJECT, IDS.CH_COMPLETED_BY_PROJECT,
                    IDS.CH_OVERDUE_BY_PROJECT, IDS.CH_COMPLETION_RATE):
            assert graph_ys(find(r["ov-charts"]["children"], cid)) == [[proj]]
        grid = find(r["ov-table"]["children"], IDS.GRID_PROJECT_SUMMARY)["props"]["rowData"]
        assert [row["project_name"] for row in grid] == [proj]
        assert grid[0]["total_actions"] == pf["total_actions"]
        o = call(app, "od-kpi", vals(proj))
        rows = (find(o["od-grid"]["children"], IDS.GRID_OVERDUE) or {"props": {"rowData": []}})
        assert {x["project_name"] for x in rows["props"]["rowData"]} <= {proj}
        assert len(rows["props"]["rowData"]) == pf["overdue_actions"]
        assert find(o["od-charts"]["children"], IDS.CH_OVERDUE_BY_PROJECT_D2) is None  # CH-17 hidden


def test_td04_all_projects_shows_every_project_and_ch17(app, golden_db):
    projects = metrics.list_projects(golden_db)
    r = call(app, "ov-kpi", vals())
    ys = graph_ys(find(r["ov-charts"]["children"], IDS.CH_TOTAL_BY_PROJECT))[0]
    assert sorted(ys) == sorted(projects)
    o = call(app, "od-kpi", vals())
    assert find(o["od-charts"]["children"], IDS.CH_OVERDUE_BY_PROJECT_D2) is not None


def test_td05_overdue_grid_reconciles_with_metrics(app, golden_db):
    for proj in (ALL_PROJECTS, *metrics.list_projects(golden_db)):
        detail = metrics.overdue_detail(norm(proj), golden_db)
        pf = metrics.portfolio(norm(proj), golden_db)
        o = call(app, "od-kpi", vals(proj))
        grid = find(o["od-grid"]["children"], IDS.GRID_OVERDUE)
        if not detail:
            assert grid is None
            continue
        rows = grid["props"]["rowData"]
        assert [r["action_id"] for r in rows] == [d["action_id"] for d in detail]
        assert len(rows) == pf["overdue_actions"]
        days = [r["days_overdue"] for r in rows]
        assert days == sorted(days, reverse=True)
        heads = [c["headerName"] for c in grid["props"]["columnDefs"] if "headerName" in c]
        assert {"Project", "Action", "Owner", "Due Date", "Days Overdue", "Status"} <= set(heads)


def test_composition_toggle_is_wired_default_plain(app):
    off = call(app, "ov-kpi", vals())["ov-charts"]["children"]
    assert find(off, IDS.CH_COMPOSITION) is None
    on = call(app, "ov-kpi", vals(**{IDS.COMPOSITION_TOGGLE: ["stacked"]}))["ov-charts"]["children"]
    fig = find(on, IDS.CH_COMPOSITION)["props"]["figure"]
    assert fig["layout"]["barmode"] == "stack"


def test_theme_and_colorblind_args_reach_charts(app):
    def fill(**kw):
        r = call(app, "ov-kpi", vals(**{IDS.COMPOSITION_TOGGLE: ["stacked"], **kw}))
        fig = find(r["ov-charts"]["children"], IDS.CH_COMPOSITION)["props"]["figure"]
        return fig["data"][1]["marker"]["color"]

    assert fill(**{IDS.CVD_TOGGLE: ["cvd"]}) != fill()
    assert fill(**{IDS.THEME_MODE: "dark"}) != fill()


# --------------------------------------------------------------------------- T-D06 / T-D08
def test_td06_chart_types_are_horizontal_bars(app):
    r = call(app, "ov-kpi", vals(**{IDS.COMPOSITION_TOGGLE: ["stacked"]}))["ov-charts"]["children"]
    for cid in (IDS.CH_TOTAL_BY_PROJECT, IDS.CH_COMPLETED_BY_PROJECT, IDS.CH_OVERDUE_BY_PROJECT,
                IDS.CH_COMPLETION_RATE, IDS.CH_COMPOSITION):
        for tr in find(r, cid)["props"]["figure"]["data"]:
            assert tr["type"] == "bar" and tr["orientation"] == "h"


def test_td08_provenance_header_and_dq_panel(app, golden_db):
    run = metrics.get_run_info(golden_db)
    tree = app.server.test_client().get("/_dash-layout").get_json()
    header = text(find(tree, IDS.HEADER))
    assert run["reference_date"] == "2026-09-15" and "2026-09-15" in header
    assert run["source_file"] in header and str(run["completed_at"]) in header
    assert "Run & validation summary" in text(find(tree, IDS.DQ_PANEL))


# --------------------------------------------------------------------------- T-D07
def test_td07_project_without_data_does_not_crash(app):
    r = call(app, "ov-kpi", vals("NO-SUCH-PROJECT"))
    assert "ไม่มีข้อมูลสำหรับ project นี้" in text(r["ov-kpi"]["children"])
    assert "0%" not in text(r["ov-kpi"]["children"]) and r["ov-charts"]["children"] == []
    o = call(app, "od-kpi", vals("NO-SUCH-PROJECT"))
    assert "ไม่มีข้อมูลสำหรับ project นี้" in text(o["od-grid"]["children"])


def test_td07_no_run_database(tmp_path):
    for p in (tmp_path / "missing.duckdb",):
        a = dash_app.create_app(p, provider=_provider(_ok))
        c = a.server.test_client()
        assert c.get("/_dash-layout").status_code == 200
        tree = c.get("/_dash-layout").get_json()
        assert "ยังไม่มีข้อมูล" in text(find(tree, IDS.HEADER))
        r = call(a, "ov-kpi", vals())
        assert "ยังไม่มีข้อมูล" in text(r["ov-kpi"]["children"])
        assert "0%" not in text(r["ov-kpi"]["children"])
        o = call(a, "od-kpi", vals())
        assert "ยังไม่มีข้อมูล" in text(o["od-kpi"]["children"])
        e = call(a, "exec-loading", vals(**{IDS.EXEC_GENERATE_BTN: 0}), IDS.PROJECT_DROPDOWN + ".value")
        assert "Executive Summary" in text(e["exec-loading"]["children"])


def test_td07_empty_overdue_is_distinct_from_no_data(tmp_path):
    from tests.conftest import write_csv

    db = tmp_path / "e.duckdb"
    csv = write_csv(tmp_path / "a.csv", [["A1", "P", "x", "Owner-001", "2030-01-01", "todo"]])
    from datetime import date

    from src import ingest

    assert ingest.run_ingest(csv, date(2026, 9, 15), db).status == "succeeded"
    a = dash_app.create_app(db, provider=_provider(_ok))
    o = call(a, "od-kpi", vals("P"))
    assert "ไม่มี overdue action ณ reference date 2026-09-15" in text(o["od-grid"]["children"])


# --------------------------------------------------------------------------- T-D09 / T-D10 / T-D11
def test_td09_labels_match_glossary(app):
    r = call(app, "ov-kpi", vals())["ov-kpi"]["children"]
    t = text(r)
    for label in ("Total Actions", "Completed", "Open", "Overdue", "Completion Rate"):
        assert label in t


def test_td10_td11_no_writes_and_no_metric_logic_in_dashboard():
    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE)\b|date_diff|due_date\s*<|status\s*!=|date\.today|datetime\.now"
        r"|\.today\(\)")
    offenders = []
    for f in (ROOT / "dashboard").rglob("*.py"):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if forbidden.search(line):
                offenders.append(f"{f.name}:{n}: {line.strip()}")
    assert offenders == []


# --------------------------------------------------------------------------- DASH-03 / T-A*
def click(app, project=ALL_PROJECTS):
    return call(app, "exec-loading", {IDS.PROJECT_DROPDOWN: project, IDS.EXEC_GENERATE_BTN: 1},
                IDS.EXEC_GENERATE_BTN + ".n_clicks")["exec-loading"]["children"]


def summaries(db):
    con = duckdb.connect(str(db), read_only=True)
    try:
        return con.execute("SELECT * FROM executive_summaries ORDER BY summary_id").fetchall()
    finally:
        con.close()


def test_exec_generate_saves_and_displays(golden_db):
    seen = []

    def handler(request):
        seen.append(request)
        return _ok(request)

    a = dash_app.create_app(golden_db, provider=_provider(handler))
    proj = metrics.list_projects(golden_db)[0]
    panel = click(a, proj)
    assert len(seen) == 1 and str(seen[0].url) == BASE + "/chat/completions"
    body = json.loads(seen[0].content)
    assert body["model"] == MODEL_NAME
    ctx = json.loads(body["messages"][-1]["content"].split("\n", 1)[1])
    assert ctx["project_filter"] == proj and ctx["source_run_id"] == 1  # T-A04: from src.metrics
    assert ctx["portfolio"] == metrics.portfolio(proj, golden_db)
    assert ctx["top_overdue_actions"] == [
        {k: d[k] for k in ("action_id", "project_name", "action_name", "owner", "due_date",
                           "days_overdue")} for d in metrics.overdue_detail(proj, golden_db)[:10]]
    assert KEY not in seen[0].content.decode()
    rows = summaries(golden_db)
    assert len(rows) == 1
    saved = summary_service.get_latest(lambda: duckdb.connect(str(golden_db), read_only=True), proj)
    assert saved["source_run_id"] == 1 and str(saved["reference_date"]) == "2026-09-15"
    t = text(panel)
    assert "สรุปจาก mock" in t and "Draft" in t and MODEL_NAME in t and "2026-09-15" in t
    assert str(saved["created_at"]) in t
    assert KEY not in repr(rows) and KEY not in t


def test_exec_latest_saved_summary_shown_on_load(golden_db):
    a = dash_app.create_app(golden_db, provider=_provider(_ok))
    click(a)  # All Projects
    tree = dash_app.create_app(golden_db, provider=_provider(_ok)).server.test_client().get(
        "/_dash-layout").get_json()
    assert "สรุปจาก mock" in text(find(tree, IDS.EXEC_PANEL))
    # a different project has no saved summary yet
    proj = metrics.list_projects(golden_db)[0]
    other = call(a, "exec-loading", {IDS.PROJECT_DROPDOWN: proj, IDS.EXEC_GENERATE_BTN: 0},
                 IDS.PROJECT_DROPDOWN + ".value")["exec-loading"]["children"]
    assert "สรุปจาก mock" not in text(other) and "ยังไม่มีสรุป" in text(other)


@pytest.mark.parametrize("env", [{"OPENAI_API_KEY": None}, {"OPENAI_BASE_URL": None},
                                 {"OPENAI_API_KEY": None, "OPENAI_BASE_URL": None}])
def test_ta03_missing_env_disables_button(golden_db, monkeypatch, env):
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    monkeypatch.setenv("OPENAI_BASE_URL", BASE)
    for k in env:
        monkeypatch.delenv(k)
    calls = []
    monkeypatch.setattr(httpx.Client, "send", lambda *a, **k: calls.append(1))  # no HTTP at all
    a = dash_app.create_app(golden_db)  # default provider = env-driven OpenRouterProvider
    tree = a.server.test_client().get("/_dash-layout").get_json()
    btn = find(tree, IDS.EXEC_GENERATE_BTN)["props"]
    assert btn["disabled"] is True
    assert "OPENAI_" in text(find(tree, IDS.EXEC_CONFIG_MSG))
    panel = click(a)  # even a forced click does nothing
    assert calls == [] and summaries(golden_db) == []
    assert find(panel, IDS.EXEC_GENERATE_BTN)["props"]["disabled"] is True
    # core dashboard unaffected
    assert kpi_value(call(a, "ov-kpi", vals())["ov-kpi"]["children"], IDS.KPI_TOTAL)


def test_env_enabled_button_when_configured(golden_db, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    monkeypatch.setenv("OPENAI_BASE_URL", BASE)
    tree = dash_app.create_app(golden_db).server.test_client().get("/_dash-layout").get_json()
    assert find(tree, IDS.EXEC_GENERATE_BTN)["props"]["disabled"] is False


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500, 503])
def test_ta02_ai_failure_shows_error_and_saves_nothing(golden_db, status, caplog):
    a = dash_app.create_app(golden_db, provider=_provider(lambda r: httpx.Response(status)))
    panel = click(a)
    err = find(panel, IDS.EXEC_ERROR)
    assert err is not None and f"HTTP {status}" in text(err)
    assert summaries(golden_db) == []
    assert find(panel, IDS.EXEC_SUMMARY_TEXT) is None  # no fake summary
    assert KEY not in text(panel) and KEY not in caplog.text
    assert kpi_value(call(a, "ov-kpi", vals())["ov-kpi"]["children"], IDS.KPI_TOTAL)


def test_ta02_timeout_shows_error_and_saves_nothing(golden_db):
    def boom(request):
        raise httpx.ConnectTimeout("t", request=request)

    panel = click(dash_app.create_app(golden_db, provider=_provider(boom)))
    assert "timeout" in text(find(panel, IDS.EXEC_ERROR)) and summaries(golden_db) == []


def test_stale_summary_warning(golden_db):
    a = dash_app.create_app(golden_db, provider=_provider(_ok))
    click(a)
    con = duckdb.connect(str(golden_db))
    con.execute("UPDATE executive_summaries SET source_run_id = 99")  # test-only tamper
    con.close()
    panel = dash_app.exec_view(None, False, a.summary_service)
    assert "ไม่ใช่ run ล่าสุด" in json.dumps(panel, cls=PlotlyJSONEncoder, ensure_ascii=False)
    assert cards.executive_summary_panel is not None
