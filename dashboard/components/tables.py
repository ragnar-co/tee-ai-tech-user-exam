"""AG Grid builders: project summary (CH-11 / CT-09) and overdue actions (CH-15 / CT-04)."""

from __future__ import annotations

import dash_ag_grid as dag
from dash import html

from dashboard.components.cards import no_overdue_state, no_project_data_state
from dashboard.viz_theme import FONT_RULES, IDS, LABELS

_INT_FMT = {"function": "d3.format(',d')(params.value)"}
_PCT_FMT = {"function": "params.data.total_actions > 0 ? d3.format('.1%')(params.value) : '-'"}

PROJECT_SUMMARY_COLUMNS = [
    {"field": "project_name", "headerName": "Project", "sort": "asc", "flex": 2,
     "minWidth": 160, "tooltipField": "project_name"},
    {"field": "total_actions", "headerName": LABELS["total_actions"], "type": "rightAligned",
     "valueFormatter": _INT_FMT, "minWidth": 110},
    {"field": "completed_actions", "headerName": LABELS["completed_actions"],
     "type": "rightAligned", "valueFormatter": _INT_FMT, "minWidth": 110},
    {"field": "open_actions", "headerName": LABELS["open_actions"], "type": "rightAligned",
     "valueFormatter": _INT_FMT, "minWidth": 90},
    {"field": "overdue_actions", "headerName": LABELS["overdue_actions"],
     "type": "rightAligned", "valueFormatter": _INT_FMT, "minWidth": 100},
    {"field": "completion_rate", "headerName": LABELS["completion_rate"],
     "type": "rightAligned", "valueFormatter": _PCT_FMT, "minWidth": 130},
]

OVERDUE_COLUMNS = [
    {"field": "action_id", "hide": True},
    {"field": "project_name", "headerName": "Project", "minWidth": 150, "flex": 1,
     "tooltipField": "project_name"},
    {"field": "action_name", "headerName": "Action", "minWidth": 220, "flex": 3,
     "tooltipField": "action_name"},
    {"field": "owner", "headerName": "Owner", "minWidth": 110, "flex": 1},
    {"field": "due_date", "headerName": "Due Date", "minWidth": 120, "sort": "asc",
     "sortIndex": 1},
    {"field": "days_overdue", "headerName": LABELS["days_overdue"], "type": "rightAligned",
     "minWidth": 120, "sort": "desc", "sortIndex": 0, "filter": "agNumberColumnFilter"},
    {"field": "status", "headerName": "Status", "minWidth": 100},
]

_DEFAULT_COL_DEF = {"sortable": True, "filter": True, "resizable": True}
_GRID_OPTIONS = {
    "animateRows": False,
    "tooltipShowDelay": 300,
    "suppressCellFocus": False,
    "rowSelection": {"mode": "singleRow", "checkboxes": False, "enableClickSelection": True},
    "ensureDomOrder": True,
}
_GRID_STYLE = {"width": "100%", "fontFamily": FONT_RULES["family"]}


def project_summary_grid(rows: list[dict] | None) -> html.Section:
    """CH-11: one row per project, default sort by project, numbers verbatim from input."""
    title = html.H3("Project summary", className="chart-title")
    if not rows:
        return html.Section([title, no_project_data_state()], className="card",
                            id=f"{IDS.GRID_PROJECT_SUMMARY}-section")
    grid = dag.AgGrid(
        id=IDS.GRID_PROJECT_SUMMARY, rowData=[dict(r) for r in rows],
        columnDefs=PROJECT_SUMMARY_COLUMNS, defaultColDef=_DEFAULT_COL_DEF,
        dashGridOptions={**_GRID_OPTIONS, "domLayout": "autoHeight"},
        getRowId="params.data.project_name", className="ag-theme-quartz", style=_GRID_STYLE,
    )
    return html.Section([title, grid], className="card", id=f"{IDS.GRID_PROJECT_SUMMARY}-section")


def overdue_grid(
    rows: list[dict] | None, reference_date: str | None = None, scope_has_data: bool = True
) -> html.Section:
    """CH-15: overdue actions; default sort Days Overdue DESC then Due Date ASC.

    rows == [] with scope_has_data=True -> "no overdue as of {date}" (distinct from no-data).
    The grid scrolls inside a fixed-height box (virtualised) because the list can be long.
    """
    title = html.H3("Overdue Actions", className="chart-title")
    sec_id = f"{IDS.GRID_OVERDUE}-section"
    if rows is None or not scope_has_data:
        return html.Section([title, no_project_data_state()], className="card", id=sec_id)
    if not rows:
        return html.Section([title, no_overdue_state(reference_date)], className="card", id=sec_id)
    keys = [c["field"] for c in OVERDUE_COLUMNS]
    data = [{k: r.get(k) for k in keys} for r in rows]
    grid = dag.AgGrid(
        id=IDS.GRID_OVERDUE, rowData=data, columnDefs=OVERDUE_COLUMNS,
        defaultColDef=_DEFAULT_COL_DEF, dashGridOptions=_GRID_OPTIONS,
        getRowId="params.data.action_id", className="ag-theme-quartz", style={**_GRID_STYLE, "height": "560px"},
        columnSize="responsiveSizeToFit",
    )
    return html.Section([title, grid], className="card", id=sec_id)
