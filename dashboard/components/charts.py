"""Plotly figure builders (CT-02 / CT-03 / CT-04). Pure presentation: every number comes in.

Backgrounds are transparent so the page's CSS variables drive light/dark; series colours follow
`mode` / `colorblind` from viz_theme. Sorting here is display order only (CT-02: high to low).
"""

from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html

from dashboard.viz_theme import (
    CHART_DEFAULTS,
    FONT_RULES,
    LABELS,
    MSG_NO_PROJECT_DATA,
    get_palette,
    plotly_layout,
)

_UNIT = {"count": "รายการ", "rate": "%"}


def _base_layout(mode: str, colorblind: bool, title: str | None) -> dict:
    layout = plotly_layout(mode, colorblind)
    layout["paper_bgcolor"] = "rgba(0,0,0,0)"
    layout["plot_bgcolor"] = "rgba(0,0,0,0)"
    layout["title"] = {"text": title, "font": layout["title"]["font"], "x": 0, "xanchor": "left"}
    layout["margin"] = {**CHART_DEFAULTS["margin"], "l": 16, "r": 40}
    layout["autosize"] = True
    layout["showlegend"] = False
    return layout


def empty_figure(
    message: str = MSG_NO_PROJECT_DATA,
    mode: str = "light",
    colorblind: bool = False,
    title: str | None = None,
) -> go.Figure:
    """Figure with no traces and a centred message (no-data state, never an exception)."""
    p = get_palette(mode, colorblind)
    fig = go.Figure()
    fig.update_layout(**_base_layout(mode, colorblind, title))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(
        text=message, showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5,
        font={"size": FONT_RULES["axis"]["size"] + 2, "color": p["text_muted"]},
    )
    fig.update_layout(height=160)
    return fig


def _hbar_height(n: int) -> int:
    return max(160, 64 + 34 * n)


def _sorted_desc(rows: list[dict], key: str) -> list[dict]:
    return sorted(rows, key=lambda r: (-(r.get(key) or 0), str(r.get("project_name", ""))))


def _axis_style(fig: go.Figure, p: dict) -> None:
    fig.update_yaxes(autorange="reversed", automargin=True, title=None, showgrid=False)
    fig.update_xaxes(gridcolor=p["grid"], rangemode="tozero", zeroline=False)


def _role_color(p: dict, role: str) -> str:
    return p["roles"].get(role, p["series"][0])


def bar_by_project_figure(
    rows: list[dict] | None,
    metric: str = "total_actions",
    reference_date: str | None = None,
    mode: str = "light",
    colorblind: bool = False,
    title: str | None = None,
) -> go.Figure:
    """CH-06/07/08/10/17: horizontal single-series bar per project, sorted high to low.

    metric: total_actions | completed_actions | overdue_actions | completion_rate.
    """
    label = LABELS[metric]
    title = title or f"{label} by Project"
    if not rows:
        return empty_figure(MSG_NO_PROJECT_DATA, mode, colorblind, title)
    p = get_palette(mode, colorblind)
    is_rate = metric == "completion_rate"
    color = {
        "total_actions": p["series"][5],
        "completed_actions": _role_color(p, "completed"),
        "overdue_actions": _role_color(p, "overdue"),
        "completion_rate": _role_color(p, "completed"),
    }[metric]
    data = _sorted_desc(rows, metric)
    names = [r["project_name"] for r in data]
    values = [r.get(metric) or 0 for r in data]
    unit = _UNIT["rate" if is_rate else "count"]
    ref = f"<br>Reference date: {reference_date}" if reference_date else ""
    fmt = ".1%" if is_rate else ",d"
    fig = go.Figure(
        go.Bar(
            x=values, y=names, orientation="h", marker={"color": color},
            text=values, texttemplate="%{x:" + fmt + "}", textposition="outside",
            cliponaxis=False, customdata=names,
            hovertemplate=(
                "%{y}<br>" + label + " : %{x:" + fmt + "} " + unit + ref + "<extra></extra>"
            ),
            name=label,
        )
    )
    fig.update_layout(**_base_layout(mode, colorblind, title), height=_hbar_height(len(data)))
    fig.update_layout(bargap=CHART_DEFAULTS["bar_gap"])
    _axis_style(fig, p)
    if is_rate:
        # DASHBOARD_SPEC CH-10: axis reads 0-100%; outside labels get extra right margin instead.
        fig.update_xaxes(range=[0, 1], tickformat=".0%", tickvals=[0, 0.25, 0.5, 0.75, 1])
        fig.update_layout(margin={**CHART_DEFAULTS["margin"], "l": 16, "r": 64})
    return fig


def composition_figure(
    rows: list[dict] | None,
    reference_date: str | None = None,
    mode: str = "light",
    colorblind: bool = False,
    title: str | None = None,
) -> go.Figure:
    """CH-09 (intermediate, user-opened view): stacked completed / open not overdue / overdue.

    Segments use colour AND fill pattern so colour is never the only channel.
    """
    title = title or "Composition by Project (intermediate view)"
    if not rows:
        return empty_figure(MSG_NO_PROJECT_DATA, mode, colorblind, title)
    p = get_palette(mode, colorblind)
    data = _sorted_desc(rows, "total_actions")
    names = [r["project_name"] for r in data]
    ref = f"<br>Reference date: {reference_date}" if reference_date else ""
    spec = [
        ("completed_actions", "completed", ""),
        ("open_not_overdue_actions", "open_non_overdue", "/"),
        ("overdue_actions", "overdue", "x"),
    ]
    fig = go.Figure()
    for key, role, pattern in spec:
        vals = [r.get(key) or 0 for r in data]
        fig.add_trace(
            go.Bar(
                x=vals, y=names, orientation="h", name=LABELS[key], customdata=names,
                marker={
                    "color": _role_color(p, role),
                    "pattern": {"shape": pattern, "fgcolor": p["background"], "size": 6},
                    "line": {"color": p["background"], "width": 1},
                },
                hovertemplate=(
                    "%{y}<br>" + LABELS[key] + " : %{x:,d} " + _UNIT["count"] + ref
                    + "<extra></extra>"
                ),
            )
        )
    fig.update_layout(**_base_layout(mode, colorblind, title))
    fig.update_layout(
        barmode="stack", showlegend=True, height=_hbar_height(len(data)) + 40,
        legend={"orientation": "h", "y": -0.15, "x": 0},
    )
    _axis_style(fig, p)
    return fig


def overdue_by_owner_figure(
    rows: list[dict] | None,
    top_n: int | None = None,
    reference_date: str | None = None,
    mode: str = "light",
    colorblind: bool = False,
    title: str | None = None,
) -> go.Figure:
    """CH-16: overdue count per owner, single neutral series, no rank numbers.

    top_n is None until the owner decides N (spec: N = null); caller passes it when known.
    """
    title = title or "Overdue Actions by Owner"
    if not rows:
        return empty_figure(MSG_NO_PROJECT_DATA, mode, colorblind, title)
    p = get_palette(mode, colorblind)
    data = sorted(rows, key=lambda r: (-(r.get("overdue_actions") or 0), str(r.get("owner", ""))))
    if top_n is not None:
        data = data[: max(top_n, 0)]
    owners = [r["owner"] for r in data]
    values = [r.get("overdue_actions") or 0 for r in data]
    ref = f"<br>Reference date: {reference_date}" if reference_date else ""
    fig = go.Figure(
        go.Bar(
            x=values, y=owners, orientation="h", marker={"color": p["series"][5]},
            text=values, texttemplate="%{x:,d}", textposition="outside", cliponaxis=False,
            customdata=owners, name=LABELS["overdue_actions"],
            hovertemplate="%{y}<br>Overdue : %{x:,d} รายการ" + ref + "<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout(mode, colorblind, title), height=_hbar_height(len(data)))
    fig.update_layout(bargap=CHART_DEFAULTS["bar_gap"])
    _axis_style(fig, p)
    return fig


def chart_summary(figure: go.Figure) -> str:
    """Alt-text summary generated from the figure's own data (no hard-coded numbers)."""
    if not figure.data:
        return "ไม่มีข้อมูล"
    first = figure.data[0]
    labels = list(first.y or [])
    if not labels:
        return "ไม่มีข้อมูล"
    if len(figure.data) > 1:
        return f"{len(labels)} categories, {len(figure.data)} series"
    return f"{len(labels)} categories; first (highest): {labels[0]}"


def chart_block(
    component_id: str,
    figure: go.Figure,
    title: str,
    reference_date: str | None = None,
    note: str | None = None,
) -> html.Div:
    """Graph wrapped with aria-label ("{title}: {summary}. Reference date {date}") and optional
    note (e.g. the 'intermediate' literacy tag for CH-09)."""
    figure = go.Figure(figure)
    figure.update_layout(title=None, margin={"t": 8})
    aria = f"{title}: {chart_summary(figure)}. Reference date {reference_date or '-'}"
    children = [html.H3(title, className="chart-title")]
    if note:
        children.append(html.Div(note, className="chart-note"))
    children.append(
        dcc.Graph(
            id=component_id, figure=figure, className="chart-graph",
            config={"displaylogo": False, "responsive": True, "displayModeBar": False},
            style={"width": "100%"},
        )
    )
    return html.Section(children, className="card chart-card", role="group", **{"aria-label": aria})
