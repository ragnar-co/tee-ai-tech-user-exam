"""KPI cards, provenance header, empty states, data-quality panel and Executive Summary parts.

All values arrive as plain data; nothing here derives a metric (AGENTS F2). Formatting only.
"""

from __future__ import annotations

from collections import Counter

from dash import html

from dashboard.viz_theme import (
    IDS,
    LABELS,
    MSG_NO_OVERDUE,
    MSG_NO_PROJECT_DATA,
    MSG_NO_RUN,
)


def fmt_int(value) -> str:
    return "-" if value is None else f"{int(value):,}"


def fmt_pct(value) -> str:
    return "-" if value is None else f"{float(value) * 100:.1f}%"


# --------------------------------------------------------------------------- empty / error
def empty_state(message: str, kind: str = "info", component_id: str | None = None) -> html.Div:
    """Readable no-data / error panel (role=status; errors use role=alert)."""
    props = {"id": component_id} if component_id else {}
    return html.Div(
        message,
        className=f"empty-state empty-{kind}",
        role="alert" if kind == "error" else "status",
        **props,
    )


def no_run_state() -> html.Div:
    return empty_state(MSG_NO_RUN, "no-run")


def no_project_data_state() -> html.Div:
    return empty_state(MSG_NO_PROJECT_DATA, "no-data")


def no_overdue_state(reference_date: str | None) -> html.Div:
    return empty_state(MSG_NO_OVERDUE.format(date=reference_date or "-"), "no-overdue")


def error_state(message: str) -> html.Div:
    return empty_state(message, "error")


# --------------------------------------------------------------------------- header
def header_block(run: dict | None) -> html.Div:
    """Provenance header: Reference date, Source, Loaded (+ run_id). run = ingestion_runs row."""
    if not run:
        return html.Div(
            [html.Span("Reference date: -"), html.Span(MSG_NO_RUN)],
            id=IDS.HEADER, className="provenance",
        )
    items = [
        ("Reference date", run.get("reference_date")),
        ("Source", run.get("source_file")),
        ("Loaded", run.get("completed_at")),
        ("Run", run.get("run_id")),
    ]
    return html.Div(
        [
            html.Span([html.Span(f"{k}: ", className="prov-key"), html.Span(str(v if v is not None else "-"))],
                      className="prov-item")
            for k, v in items
        ],
        id=IDS.HEADER, className="provenance",
    )


# --------------------------------------------------------------------------- KPI cards
def kpi_card(
    component_id: str,
    label: str,
    value_text: str,
    reference_date: str | None = None,
    run_id=None,
    href: str | None = None,
    role: str | None = None,
) -> html.Component:
    """CT-01 card: label, big value, reference date + run id. No trend arrows, no red/green."""
    body = [
        html.Div(label, className="kpi-label"),
        html.Div(value_text, className="kpi-value"),
        html.Div(
            f"Ref {reference_date or '-'} · run {run_id if run_id is not None else '-'}",
            className="kpi-meta",
        ),
    ]
    cls = "card kpi-card" + (f" kpi-{role}" if role else "")
    if href:
        return html.A(body, id=component_id, href=href, className=cls + " kpi-link",
                      **{"aria-label": f"{label}: {value_text}"})
    return html.Div(body, id=component_id, className=cls, role="group",
                    **{"aria-label": f"{label}: {value_text}"})


def _scope_has_data(portfolio: dict | None) -> bool:
    return bool(portfolio) and (portfolio.get("total_actions") or 0) > 0


def kpi_row(
    portfolio: dict | None,
    reference_date: str | None = None,
    run_id=None,
    show_completion_rate: bool = True,
    overdue_href: str | None = "/overdue",
    table_href: str | None = f"#{IDS.GRID_PROJECT_SUMMARY}",
    has_run: bool = True,
) -> html.Div:
    """DASH-01 KPI row CH-01..CH-05. Empty scope -> empty state, never zeros / 0%."""
    if not has_run or portfolio is None:
        return html.Div(no_run_state(), id=IDS.KPI_ROW, className="kpi-row")
    if not _scope_has_data(portfolio):
        return html.Div(no_project_data_state(), id=IDS.KPI_ROW, className="kpi-row")
    common = {"reference_date": reference_date, "run_id": run_id}
    cards = [
        kpi_card(IDS.KPI_TOTAL, LABELS["total_actions"], fmt_int(portfolio.get("total_actions")),
                 href=table_href, **common),
        kpi_card(IDS.KPI_COMPLETED, LABELS["completed_actions"],
                 fmt_int(portfolio.get("completed_actions")), href=table_href, role="completed",
                 **common),
        kpi_card(IDS.KPI_OPEN, LABELS["open_actions"], fmt_int(portfolio.get("open_actions")),
                 href=table_href, **common),
        kpi_card(IDS.KPI_OVERDUE, LABELS["overdue_actions"],
                 fmt_int(portfolio.get("overdue_actions")), href=overdue_href, role="overdue",
                 **common),
    ]
    if show_completion_rate and portfolio.get("completion_rate") is not None:
        cards.append(
            kpi_card(IDS.KPI_COMPLETION_RATE, LABELS["completion_rate"],
                     fmt_pct(portfolio.get("completion_rate")), href=table_href, **common)
        )
    return html.Div(cards, id=IDS.KPI_ROW, className="kpi-row")


def overdue_kpi_row(
    portfolio: dict | None, reference_date: str | None = None, run_id=None, has_run: bool = True
) -> html.Div:
    """DASH-02 CH-13 (Overdue) + CH-14 (Owners with Overdue). Counts only, no scores."""
    row_id = "kpi-row-d2"
    if not has_run or portfolio is None:
        return html.Div(no_run_state(), id=row_id, className="kpi-row")
    if not _scope_has_data(portfolio):
        return html.Div(no_project_data_state(), id=row_id, className="kpi-row")
    common = {"reference_date": reference_date, "run_id": run_id}
    return html.Div(
        [
            kpi_card(IDS.KPI_OVERDUE_D2, LABELS["overdue_actions"],
                     fmt_int(portfolio.get("overdue_actions")), role="overdue", **common),
            kpi_card(IDS.KPI_OWNERS_OVERDUE, LABELS["owners_with_overdue_actions"],
                     fmt_int(portfolio.get("owners_with_overdue_actions")), **common),
        ],
        id=row_id, className="kpi-row",
    )


# --------------------------------------------------------------------------- CH-12
def dq_panel(dq: dict | None) -> html.Section:
    """CH-12 Run & validation summary from metrics.data_quality_summary() output.

    Shows source file, run_id, row counts, findings per check_name x severity. record_key /
    message (confidential) are deliberately not rendered. No quality score (null in spec).
    """
    title = html.H3("Run & validation summary", className="chart-title")
    run = (dq or {}).get("run")
    if not run:
        return html.Section([title, no_run_state()], id=IDS.DQ_PANEL, className="card")
    facts = [
        ("Source file", run.get("source_file")),
        ("Run ID", run.get("run_id")),
        ("Reference date", run.get("reference_date")),
        ("Source rows", fmt_int(run.get("source_row_count"))),
        ("Valid rows", fmt_int(run.get("valid_row_count"))),
        ("Invalid rows", fmt_int(run.get("invalid_row_count"))),
    ]
    dl = html.Dl([x for k, v in facts for x in (html.Dt(k), html.Dd(str(v)))], className="facts")
    counts = Counter((f.get("check_name"), f.get("severity_class")) for f in dq.get("findings") or [])
    if counts:
        rows = [
            html.Tr([html.Td(str(c)), html.Td(str(s)), html.Td(fmt_int(n), className="num")])
            for (c, s), n in sorted(counts.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1])))
        ]
        table = html.Table(
            [html.Thead(html.Tr([html.Th("Check"), html.Th("Severity"),
                                 html.Th("Findings", className="num")])), html.Tbody(rows)],
            className="simple-table",
        )
    else:
        table = html.Div("ไม่มี finding ใน run นี้", className="muted")
    kids = [title, dl, table]
    attempt = dq.get("latest_attempt")
    if attempt and attempt.get("run_id") != run.get("run_id") and attempt.get("status") == "failed":
        kids.insert(1, error_state(
            f"การโหลดล่าสุด (run {attempt.get('run_id')}) ล้มเหลว — แสดงข้อมูลจาก run {run.get('run_id')}"
        ))
    return html.Section(kids, id=IDS.DQ_PANEL, className="card")


# --------------------------------------------------------------------------- DASH-03
def draft_label() -> html.Span:
    return html.Span("Draft", className="badge badge-draft")


def generate_button(enabled: bool, config_message: str | None = None) -> html.Div:
    """CP-03. Disabled + visible config message when env is missing (T-A03)."""
    msg = config_message or "ตั้งค่า OPENAI_API_KEY และ OPENAI_BASE_URL เพื่อเปิดใช้งาน"
    return html.Div(
        [
            html.Button("Generate Draft", id=IDS.EXEC_GENERATE_BTN, n_clicks=0,
                        disabled=not enabled, className="btn btn-primary"),
            html.Div("" if enabled else msg, id=IDS.EXEC_CONFIG_MSG, className="muted",
                     role="status"),
        ],
        className="generate-row",
    )


def error_alert(message: str | None = None) -> html.Div:
    """Container always present (callback target); empty when no error."""
    if not message:
        return html.Div(id=IDS.EXEC_ERROR, className="alert-slot")
    return html.Div(message, id=IDS.EXEC_ERROR, className="empty-state empty-error", role="alert")


def executive_summary_panel(
    summary: dict | None,
    reference_date: str | None = None,
    latest_run_id=None,
    generate_enabled: bool = True,
    config_message: str | None = None,
    error: str | None = None,
) -> html.Div:
    """CP-01, CP-03..CP-06 + Draft label + stale-run warning (AL-04).

    summary = executive_summaries row: summary_text, created_at, provider, model_name,
    prompt_version, source_run_id, project_filter. None -> 'no saved summary' note.
    """
    parts = [
        html.Div(
            [html.H2("Executive Summary", className="page-title"), draft_label()],
            className="title-row",
        ),
        html.Div([html.Span("Reference date: ", className="prov-key"),
                  html.Span(reference_date or "-", id=IDS.EXEC_REFERENCE_DATE)], className="prov-item"),
        generate_button(generate_enabled, config_message),
        error_alert(error),
    ]
    if not summary:
        parts.append(empty_state("ยังไม่มีสรุปที่บันทึกไว้สำหรับ project นี้", "no-data"))
        parts += [html.Div(id=IDS.EXEC_STALE_WARNING)]
        return html.Div(parts, id=IDS.EXEC_PANEL, className="card exec-panel")
    src = summary.get("source_run_id")
    stale = latest_run_id is not None and src is not None and src != latest_run_id
    parts.append(
        html.Div(
            f"สรุปนี้สร้างจาก run {src} ซึ่งไม่ใช่ run ล่าสุด ({latest_run_id}) — ตัวเลขอาจล้าสมัย",
            id=IDS.EXEC_STALE_WARNING, className="empty-state empty-warning", role="alert",
        ) if stale else html.Div(id=IDS.EXEC_STALE_WARNING)
    )
    parts.append(
        html.Div(
            [html.Span("Draft — ร่างสำหรับผู้ตรวจทาน ยังไม่ผ่านการรับรอง ", className="badge badge-draft"),
             html.P(summary.get("summary_text") or "", id=IDS.EXEC_SUMMARY_TEXT,
                    className="summary-text")],
            className="summary-box",
        )
    )
    model = f"{summary.get('provider') or '-'} / {summary.get('model_name') or '-'}"
    parts.append(
        html.Dl(
            [
                html.Dt("Generated at"), html.Dd(str(summary.get("created_at") or "-"),
                                                 id=IDS.EXEC_GENERATED_AT),
                html.Dt("Model"), html.Dd(f"{model} (Draft)", id=IDS.EXEC_MODEL),
                html.Dt("Prompt version"), html.Dd(str(summary.get("prompt_version") or "-")),
                html.Dt("Source run"), html.Dd(str(src if src is not None else "-")),
                html.Dt("Project filter"), html.Dd(summary.get("project_filter") or "All Projects"),
            ],
            className="facts",
        )
    )
    return html.Div(parts, id=IDS.EXEC_PANEL, className="card exec-panel")
