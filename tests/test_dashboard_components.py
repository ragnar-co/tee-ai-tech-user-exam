"""Presentation-layer tests: builders accept plain data, never crash on empty data."""

import pytest
from dash import html

from dashboard.components import cards, charts, filters, tables
from dashboard.viz_theme import ALL_PROJECTS, IDS, all_ids, get_palette, plotly_layout

REF = "2026-10-02"
PORTFOLIO = {
    "total_actions": 14013, "completed_actions": 8597, "open_actions": 5416,
    "overdue_actions": 3531, "completion_rate": 0.6135, "open_not_overdue_actions": 1885,
    "owners_with_overdue_actions": 96,
}
BY_PROJECT = [
    {"project_name": "Alpha", "total_actions": 10, "completed_actions": 6, "open_actions": 4,
     "overdue_actions": 1, "open_not_overdue_actions": 3, "completion_rate": 0.6},
    {"project_name": "โครงการไทย", "total_actions": 30, "completed_actions": 9, "open_actions": 21,
     "overdue_actions": 7, "open_not_overdue_actions": 14, "completion_rate": 0.3},
]
OVERDUE = [
    {"action_id": "A1", "project_name": "Alpha", "action_name": "ตรวจสอบระบบ", "owner": "Owner-001",
     "due_date": "2026-09-30", "days_overdue": 2, "status": "in_progress"},
    {"action_id": "A2", "project_name": "Alpha", "action_name": "Patch", "owner": "Owner-002",
     "due_date": "2026-09-01", "days_overdue": 31, "status": "open"},
]
BY_OWNER = [{"owner": "Owner-001", "overdue_actions": 3}, {"owner": "Owner-002", "overdue_actions": 5}]
RUN = {"run_id": 3, "source_file": "x.csv", "reference_date": REF, "completed_at": "2026-10-02 10:00",
       "source_row_count": 10, "valid_row_count": 9, "invalid_row_count": 1, "status": "succeeded"}
DQ = {"run": RUN, "latest_attempt": {**RUN, "run_id": 4, "status": "failed"},
      "severity_counts": {"warning": 2},
      "findings": [{"check_name": "DQ-09", "record_key": "k", "severity_class": "warning",
                    "message": "SECRET-MSG"}] * 2}
SUMMARY = {"summary_text": "สรุปร่าง", "created_at": "2026-10-02", "provider": "openrouter",
           "model_name": "anthropic/claude-sonnet-5", "prompt_version": "v1", "source_run_id": 2,
           "project_filter": None}


def walk(node):
    yield node
    kids = getattr(node, "children", None)
    if isinstance(kids, (list, tuple)):
        for k in kids:
            yield from walk(k)
    elif kids is not None:
        yield from walk(kids)


def find(node, cid):
    return next(n for n in walk(node) if getattr(n, "id", None) == cid)


def text_of(node) -> str:
    return " ".join(str(n) for n in walk(node) if isinstance(n, str))


def ids_in(node) -> list[str]:
    return [n.id for n in walk(node) if getattr(n, "id", None)]


def test_constant_ids_unique():
    ids = all_ids()
    assert len(ids) == len(set(ids)) and len(ids) > 20


def test_theme_palettes():
    for mode in ("light", "dark"):
        for cvd in (False, True):
            assert get_palette(mode, cvd)["roles"]["overdue"]
            assert plotly_layout(mode, cvd)["colorway"]


def test_project_dropdown():
    dd = filters.project_dropdown(["A", "B", "A"], "B")
    drop = find(dd, IDS.PROJECT_DROPDOWN)
    assert [o["value"] for o in drop.options] == [ALL_PROJECTS, "A", "B"]
    assert drop.value == "B"
    empty = filters.project_dropdown(None, "zzz")
    assert find(empty, IDS.PROJECT_DROPDOWN).value == ALL_PROJECTS
    assert filters.normalize_project(ALL_PROJECTS) is None
    assert filters.normalize_project("A") == "A"
    assert filters.filter_bar([]) is not None


def test_kpi_row_full_and_values_verbatim():
    row = cards.kpi_row(PORTFOLIO, REF, 3)
    found = ids_in(row)
    for i in (IDS.KPI_TOTAL, IDS.KPI_COMPLETED, IDS.KPI_OPEN, IDS.KPI_OVERDUE,
              IDS.KPI_COMPLETION_RATE):
        assert i in found
    t = text_of(row)
    assert "14,013" in t and "3,531" in t and "61.4%" in t and REF in t
    assert IDS.KPI_COMPLETION_RATE not in ids_in(cards.kpi_row(PORTFOLIO, REF, 3, False))


@pytest.mark.parametrize("portfolio,has_run,msg", [
    (None, False, "ยังไม่มีข้อมูล"),
    ({**PORTFOLIO, "total_actions": 0, "completion_rate": 0}, True, "ไม่มีข้อมูลสำหรับ project นี้"),
])
def test_kpi_row_empty(portfolio, has_run, msg):
    row = cards.kpi_row(portfolio, REF, 3, has_run=has_run)
    t = text_of(row)
    assert msg in t and "0%" not in t and IDS.KPI_TOTAL not in ids_in(row)


def test_overdue_kpi_row():
    row = cards.overdue_kpi_row(PORTFOLIO, REF, 3)
    assert {IDS.KPI_OVERDUE_D2, IDS.KPI_OWNERS_OVERDUE} <= set(ids_in(row))
    assert "ยังไม่มีข้อมูล" in text_of(cards.overdue_kpi_row(None))


@pytest.mark.parametrize("metric,n_expected_first", [
    ("total_actions", "โครงการไทย"), ("completed_actions", "โครงการไทย"),
    ("overdue_actions", "โครงการไทย"), ("completion_rate", "Alpha"),
])
def test_bar_by_project(metric, n_expected_first):
    fig = charts.bar_by_project_figure(BY_PROJECT, metric, REF)
    assert len(fig.data) == 1 and fig.data[0].type == "bar" and fig.data[0].orientation == "h"
    assert fig.data[0].y[0] == n_expected_first  # sorted high to low
    assert list(fig.data[0].x) == sorted(fig.data[0].x, reverse=True)
    assert fig.layout.yaxis.autorange == "reversed"
    if metric == "completion_rate":
        assert list(fig.layout.xaxis.range) == [0, 1]  # CH-10: axis reads 0-100%
        assert fig.layout.xaxis.tickformat == ".0%"


def test_bar_single_project_and_empty():
    assert len(charts.bar_by_project_figure(BY_PROJECT[:1]).data[0].y) == 1
    for rows in ([], None):
        fig = charts.bar_by_project_figure(rows)
        assert len(fig.data) == 0 and fig.layout.annotations


def test_composition_stacked():
    fig = charts.composition_figure(BY_PROJECT, REF, mode="dark", colorblind=True)
    assert [t.name for t in fig.data] == ["Completed", "Open (Not Overdue)", "Overdue"]
    assert fig.layout.barmode == "stack"
    assert len(charts.composition_figure([]).data) == 0


def test_owner_chart():
    fig = charts.overdue_by_owner_figure(BY_OWNER, top_n=1)
    assert list(fig.data[0].y) == ["Owner-002"]
    assert len(charts.overdue_by_owner_figure(BY_OWNER).data[0].y) == 2
    assert len(charts.overdue_by_owner_figure([]).data) == 0


def test_chart_block_aria():
    blk = charts.chart_block(IDS.CH_TOTAL_BY_PROJECT, charts.bar_by_project_figure(BY_PROJECT),
                             "Total Actions by Project", REF, note="x")
    assert IDS.CH_TOTAL_BY_PROJECT in ids_in(blk)
    assert REF in blk.to_plotly_json()["props"]["aria-label"]
    charts.chart_block(IDS.CH_TOTAL_BY_PROJECT, charts.bar_by_project_figure([]), "T")


def grid_of(section, gid):
    return find(section, gid)


def test_project_summary_grid():
    g = grid_of(tables.project_summary_grid(BY_PROJECT), IDS.GRID_PROJECT_SUMMARY)
    assert len(g.rowData) == 2
    assert [c["headerName"] for c in g.columnDefs] == [
        "Project", "Total Actions", "Completed", "Open", "Overdue", "Completion Rate"]
    assert "ไม่มีข้อมูล" in text_of(tables.project_summary_grid([]))


def test_overdue_grid_default_sort_and_thai():
    sec = tables.overdue_grid(OVERDUE, REF)
    g = grid_of(sec, IDS.GRID_OVERDUE)
    cols = {c["field"]: c for c in g.columnDefs}
    assert cols["days_overdue"]["sort"] == "desc" and cols["days_overdue"]["sortIndex"] == 0
    assert cols["due_date"]["sort"] == "asc" and cols["due_date"]["sortIndex"] == 1
    assert cols["action_id"]["hide"] is True
    shown = [c["headerName"] for c in g.columnDefs if not c.get("hide")]
    assert shown == ["Project", "Action", "Owner", "Due Date", "Days Overdue", "Status"]
    assert g.rowData[0]["action_name"] == "ตรวจสอบระบบ"
    assert g.getRowId == "params.data.action_id"


def test_overdue_grid_empty_states():
    none_overdue = tables.overdue_grid([], REF)
    assert f"ไม่มี overdue action ณ reference date {REF}" in text_of(none_overdue)
    assert IDS.GRID_OVERDUE not in ids_in(none_overdue)
    assert "ไม่มีข้อมูลสำหรับ project นี้" in text_of(tables.overdue_grid([], REF, scope_has_data=False))
    assert "ไม่มีข้อมูล" in text_of(tables.overdue_grid(None))


def test_header_and_dq():
    t = text_of(cards.header_block(RUN))
    assert REF in t and "x.csv" in t and "2026-10-02 10:00" in t
    assert "ยังไม่มีข้อมูล" in text_of(cards.header_block(None))
    p = cards.dq_panel(DQ)
    t = text_of(p)
    assert "DQ-09" in t and "SECRET-MSG" not in t and "ล้มเหลว" in t
    for dq in (None, {}, {"run": None, "findings": []}):
        assert "ยังไม่มีข้อมูล" in text_of(cards.dq_panel(dq))
    assert "ไม่มี finding" in text_of(cards.dq_panel({**DQ, "findings": [], "latest_attempt": None}))


def test_empty_states():
    assert cards.error_state("boom").role == "alert"
    assert "boom" in text_of(cards.error_state("boom"))
    assert cards.no_run_state() is not None


def test_exec_summary_panel():
    p = cards.executive_summary_panel(SUMMARY, REF, latest_run_id=3, generate_enabled=False,
                                      config_message="ตั้งค่า env", error="ล้มเหลว")
    ids = ids_in(p)
    for i in (IDS.EXEC_GENERATE_BTN, IDS.EXEC_SUMMARY_TEXT, IDS.EXEC_GENERATED_AT, IDS.EXEC_MODEL,
              IDS.EXEC_ERROR, IDS.EXEC_STALE_WARNING, IDS.EXEC_REFERENCE_DATE):
        assert i in ids
    assert len(ids) == len(set(ids))
    btn = find(p, IDS.EXEC_GENERATE_BTN)
    assert btn.disabled is True
    t = text_of(p)
    assert "Draft" in t and "ตั้งค่า env" in t and "ล้มเหลว" in t and "ไม่ใช่ run ล่าสุด" in t
    assert "anthropic/claude-sonnet-5" in t


def test_exec_summary_empty_and_fresh():
    p = cards.executive_summary_panel(None, REF, generate_enabled=True)
    btn = find(p, IDS.EXEC_GENERATE_BTN)
    assert btn.disabled is False
    assert "ยังไม่มีสรุป" in text_of(p)
    fresh = cards.executive_summary_panel({**SUMMARY, "source_run_id": 3}, REF, latest_run_id=3)
    assert "ไม่ใช่ run ล่าสุด" not in text_of(fresh)


def test_whole_page_ids_unique():
    page = html.Div([
        filters.filter_bar(["A"]), cards.header_block(RUN), cards.kpi_row(PORTFOLIO, REF, 3),
        charts.chart_block(IDS.CH_TOTAL_BY_PROJECT, charts.bar_by_project_figure(BY_PROJECT), "t"),
        tables.project_summary_grid(BY_PROJECT), cards.dq_panel(DQ),
        cards.overdue_kpi_row(PORTFOLIO, REF, 3), tables.overdue_grid(OVERDUE, REF),
        cards.executive_summary_panel(SUMMARY, REF, 3),
    ])
    ids = ids_in(page)
    assert len(ids) == len(set(ids))
    assert set(ids) <= set(all_ids()) | {"kpi-row-d2", f"{IDS.GRID_PROJECT_SUMMARY}-section",
                                         f"{IDS.GRID_OVERDUE}-section"}
