"""Dash app: DASH-01 Portfolio Overview, DASH-02 Overdue Actions, DASH-03 Executive Summary (draft).

Run from the repo root:  .venv/bin/python dashboard/app.py   (or ``python -m dashboard.app``)
Environment (all optional):
  DASH_DB_PATH  DuckDB file (default data/cybersecurity.duckdb)
  DASH_HOST     bind address (default 127.0.0.1)      DASH_PORT   port (default 8050)
  DASH_DEBUG    1/true enables Dash debug (default off)
  OPENAI_API_KEY / OPENAI_BASE_URL  enable "Generate Draft" (never stored or logged)

F-rules: callbacks do no metric math: they call src.metrics and the component builders only. The
dashboard reads DuckDB read-only (via src.metrics); the single write is PL-02's executive_summaries
row, saved by src.ai.summary_service on a short-lived writer connection.
"""

from __future__ import annotations

import os
import sys
import threading
from collections.abc import Callable
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:  # allow `python dashboard/app.py` from anywhere
    sys.path.insert(0, str(_ROOT))

import duckdb
from dash import Dash, Input, Output, ctx, dcc, html, no_update

from dashboard.components import cards, charts, filters, tables
from dashboard.viz_theme import IDS
from src import metrics, settings
from src.ai import summary_service
from src.ai.context_builder import build_context
from src.ai.provider import ExecutiveSummaryProvider, OpenRouterProvider
from src.db import connect_readonly, connect_writer

OWNER_CHART_TOP_N = 10  # CH-16 N (docs: null = calibrate later); small interim default
PAGES = (("/", "Portfolio Overview"), ("/overdue", "Overdue Actions"),
         ("/executive-summary", "Executive Summary (draft)"))
PAGE_IDS = {"/": "page-overview", "/overdue": "page-overdue", "/executive-summary": "page-exec"}

# duckdb refuses a second connection with a different config in one process, so every DB touch
# (read-only metrics, summary writer) is serialised.
_DB_LOCK = threading.RLock()


def _chart_mode(theme: str | None) -> str:
    return "dark" if theme == "dark" else "light"


def _has_data(portfolio: dict) -> bool:
    return bool(portfolio.get("total_actions"))


# --------------------------------------------------------------------------- page views
def overview_view(project, theme, cvd, show_composition, db_path=None):
    """DASH-01 body: (kpi row, chart blocks, project summary grid)."""
    mode, cb = _chart_mode(theme), bool(cvd)
    with _DB_LOCK:
        run = metrics.get_run_info(db_path)
        pf = metrics.portfolio(project, db_path)
        rows = metrics.by_project(project, db_path)
    ref = run["reference_date"] if run else None
    rid = run["run_id"] if run else None
    kpi = cards.kpi_row(pf, ref, rid, has_run=run is not None)
    if run is None or not _has_data(pf):
        return kpi, [], tables.project_summary_grid([])
    specs = [
        (IDS.CH_TOTAL_BY_PROJECT, "total_actions", "Total Actions by Project"),
        (IDS.CH_COMPLETED_BY_PROJECT, "completed_actions", "Completed by Project"),
        (IDS.CH_OVERDUE_BY_PROJECT, "overdue_actions", "Overdue by Project"),
        (IDS.CH_COMPLETION_RATE, "completion_rate", "Completion Rate by Project"),
    ]
    blocks = [
        charts.chart_block(
            cid, charts.bar_by_project_figure(rows, metric, ref, mode, cb, title), title, ref)
        for cid, metric, title in specs
    ]
    if show_composition:
        title = "Composition by Project"
        blocks.append(charts.chart_block(
            IDS.CH_COMPOSITION, charts.composition_figure(rows, ref, mode, cb, title), title, ref,
            note="Intermediate view: completed / open (not overdue) / overdue"))
    return kpi, blocks, tables.project_summary_grid(rows)


def overdue_view(project, theme, cvd, db_path=None):
    """DASH-02 body: (kpi row, chart blocks, overdue grid)."""
    mode, cb = _chart_mode(theme), bool(cvd)
    with _DB_LOCK:
        run = metrics.get_run_info(db_path)
        pf = metrics.portfolio(project, db_path)
        detail = metrics.overdue_detail(project, db_path)
        owners = metrics.by_owner(project, db_path)
        projects = metrics.by_project(project, db_path)
    ref = run["reference_date"] if run else None
    rid = run["run_id"] if run else None
    kpi = cards.overdue_kpi_row(pf, ref, rid, has_run=run is not None)
    has = run is not None and _has_data(pf)
    blocks = []
    if has and owners:
        title = "Overdue Actions by Owner"
        blocks.append(charts.chart_block(
            IDS.CH_OVERDUE_BY_OWNER,
            charts.overdue_by_owner_figure(owners, OWNER_CHART_TOP_N, ref, mode, cb, title),
            title, ref, note=f"Top {OWNER_CHART_TOP_N} owners by count (not a performance ranking)"))
    if has and project is None:  # CH-17 only in All Projects mode (single project = 1 bar)
        title = "Overdue Actions by Project"
        blocks.append(charts.chart_block(
            IDS.CH_OVERDUE_BY_PROJECT_D2,
            charts.bar_by_project_figure(projects, "overdue_actions", ref, mode, cb, title),
            title, ref))
    return kpi, blocks, tables.overdue_grid(detail if run else None, ref, scope_has_data=has)


# --------------------------------------------------------------------------- DASH-03
class SummaryService:
    """Wires summary_service to this app's DB path; provider is injectable (tests / real env)."""

    def __init__(self, db_path, provider_factory: Callable[[], ExecutiveSummaryProvider]):
        self.db_path = Path(db_path) if db_path else settings.DB_PATH
        self.provider_factory = provider_factory

    def _read(self):
        return connect_readonly(self.db_path)

    def _write_factory(self):
        """First call -> throw-away in-memory con (the context builder uses src.metrics, which
        opens its own read-only connection); later calls -> the PL-02 writer connection."""
        calls = []

        def factory():
            calls.append(1)
            return duckdb.connect(":memory:") if len(calls) == 1 else connect_writer(self.db_path)

        return factory

    def latest(self, project):
        if not self.db_path.exists():
            return None
        try:
            return summary_service.get_latest(self._read, project)
        except duckdb.Error:
            return None

    def generate(self, project):
        return summary_service.generate_and_save(
            project, provider=self.provider_factory(),
            context_builder=lambda con, pf: build_context(con, pf, db_path=self.db_path),
            connect=self._write_factory())


def exec_view(project, clicked, svc: SummaryService):
    """DASH-03 panel. clicked=True runs PL-02 first; errors are shown, never raised."""
    provider = svc.provider_factory()
    enabled = provider.is_configured()
    msg = None if enabled else provider.missing_config_message()
    error = None
    with _DB_LOCK:
        if clicked and enabled:
            res = svc.generate(project)
            if not res["ok"]:
                error = res["error"]
        run = metrics.get_run_info(svc.db_path)
        summary = svc.latest(project)
    return cards.executive_summary_panel(
        summary, run["reference_date"] if run else None, run["run_id"] if run else None,
        generate_enabled=enabled, config_message=msg, error=error)


# --------------------------------------------------------------------------- layout / app
def _persistent_filter_bar(projects):
    bar = filters.filter_bar(projects)
    dropdown = bar.children[0].children[1]
    dropdown.persistence, dropdown.persistence_type = True, "session"  # survives page links
    return bar


def create_app(db_path=None, provider: ExecutiveSummaryProvider | None = None) -> Dash:
    """Build the app. db_path defaults to env DASH_DB_PATH; provider defaults to OpenRouter (env)."""
    db = Path(db_path or os.environ.get("DASH_DB_PATH") or settings.DB_PATH)
    svc = SummaryService(db, (lambda: provider) if provider else OpenRouterProvider)
    app = Dash(__name__, title="Cybersecurity Action Dashboard", suppress_callback_exceptions=True,
               assets_folder=str(Path(__file__).parent / "assets"))
    app.db_path, app.summary_service = db, svc  # exposed for tests

    def serve_layout():
        with _DB_LOCK:
            run = metrics.get_run_info(db)
            projects = metrics.list_projects(db)
            dq = metrics.data_quality_summary(db)
        return html.Div(
            [
                dcc.Location(id="url"),
                html.Div(id="theme-sink", hidden=True),
                html.H1("Cybersecurity Action Dashboard", className="page-title"),
                html.Nav([dcc.Link(label, href=href, className="nav-link")
                          for href, label in PAGES], className="nav-bar"),
                cards.header_block(run),
                _persistent_filter_bar(projects),
                html.Div([
                    html.Div([html.Div(id="ov-kpi"),
                              dcc.Checklist(id=IDS.COMPOSITION_TOGGLE, value=[],
                                            options=[{"label": "Show composition (stacked) view "
                                                      "- intermediate", "value": "stacked"}],
                                            className="check-inline"),
                              html.Div(id="ov-charts"), html.Div(id="ov-table"),
                              cards.dq_panel(dq)], id="page-overview"),
                    html.Div([html.Div(id="od-kpi"), html.Div(id="od-charts"),
                              html.Div(id="od-grid")], id="page-overdue"),
                    html.Div(dcc.Loading(exec_view(None, False, svc), id="exec-loading"),
                             id="page-exec"),
                ]),
            ],
            className="page",
        )

    app.layout = serve_layout

    @app.callback(
        [Output(pid, "style") for pid in PAGE_IDS.values()], Input("url", "pathname"))
    def show_page(pathname):
        active = PAGE_IDS.get(pathname or "/", "page-overview")
        return [{} if pid == active else {"display": "none"} for pid in PAGE_IDS.values()]

    common = (Input(IDS.PROJECT_DROPDOWN, "value"), Input(IDS.THEME_MODE, "value"),
              Input(IDS.CVD_TOGGLE, "value"))

    @app.callback(Output("ov-kpi", "children"), Output("ov-charts", "children"),
                  Output("ov-table", "children"), *common, Input(IDS.COMPOSITION_TOGGLE, "value"))
    def update_overview(project, theme, cvd, comp):
        return overview_view(filters.normalize_project(project), theme, cvd, bool(comp), db)

    @app.callback(Output("od-kpi", "children"), Output("od-charts", "children"),
                  Output("od-grid", "children"), *common)
    def update_overdue(project, theme, cvd):
        return overdue_view(filters.normalize_project(project), theme, cvd, db)

    @app.callback(Output("exec-loading", "children"), Input(IDS.PROJECT_DROPDOWN, "value"),
                  Input(IDS.EXEC_GENERATE_BTN, "n_clicks"), prevent_initial_call=True)
    def update_exec(project, n_clicks):
        clicked = ctx.triggered_id == IDS.EXEC_GENERATE_BTN and bool(n_clicks)
        if ctx.triggered_id == IDS.EXEC_GENERATE_BTN and not n_clicks:
            return no_update  # button re-created by a re-render, not a click
        return exec_view(filters.normalize_project(project), clicked, svc)

    app.clientside_callback(
        """function(mode){var r=document.documentElement;
        if(mode==='light'||mode==='dark'){r.setAttribute('data-theme',mode);}
        else{r.removeAttribute('data-theme');} return '';}""",
        Output("theme-sink", "children"), Input(IDS.THEME_MODE, "value"))
    return app


app = create_app()
server = app.server

if __name__ == "__main__":
    app.run(
        host=os.environ.get("DASH_HOST", "127.0.0.1"),
        port=int(os.environ.get("DASH_PORT", "8050")),
        debug=os.environ.get("DASH_DEBUG", "").lower() in ("1", "true", "yes"),
    )
