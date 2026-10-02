"""Global filters (Project dropdown, theme / colour-vision controls). No data access."""

from __future__ import annotations

from dash import dcc, html

from dashboard.viz_theme import ALL_PROJECTS, IDS


def project_options(projects: list[str] | None) -> list[dict]:
    """'All Projects' first, then each project name once (input order kept)."""
    seen: set[str] = set()
    opts = [{"label": ALL_PROJECTS, "value": ALL_PROJECTS}]
    for name in projects or []:
        if name and name != ALL_PROJECTS and name not in seen:
            seen.add(name)
            opts.append({"label": name, "value": name})
    return opts


def normalize_project(value: str | None) -> str | None:
    """Dropdown value -> `project_name` parameter for Q-* (None = All Projects)."""
    return None if value in (None, "", ALL_PROJECTS) else value


def project_dropdown(
    projects: list[str] | None, value: str | None = None, component_id: str = IDS.PROJECT_DROPDOWN
) -> html.Div:
    """Single-select project filter; unknown/None value falls back to All Projects."""
    opts = project_options(projects)
    valid = {o["value"] for o in opts}
    current = value if value in valid else ALL_PROJECTS
    return html.Div(
        [
            html.Label("Project", htmlFor=component_id, className="filter-label"),
            dcc.Dropdown(
                id=component_id, options=opts, value=current, clearable=False, searchable=True,
                className="project-dropdown",
            ),
        ],
        className="filter-group",
    )


def theme_controls() -> html.Div:
    """Light/dark/auto selector and colour-vision-safe toggle (callbacks wire them later)."""
    return html.Div(
        [
            html.Label("Theme", htmlFor=IDS.THEME_MODE, className="filter-label"),
            dcc.RadioItems(
                id=IDS.THEME_MODE,
                options=[
                    {"label": "Auto", "value": "auto"},
                    {"label": "Light", "value": "light"},
                    {"label": "Dark", "value": "dark"},
                ],
                value="auto", inline=True, className="radio-inline",
            ),
            dcc.Checklist(
                id=IDS.CVD_TOGGLE,
                options=[{"label": "Colour-blind safe palette", "value": "cvd"}],
                value=[], className="check-inline",
            ),
        ],
        className="filter-group theme-controls",
    )


def filter_bar(projects: list[str] | None, value: str | None = None) -> html.Div:
    return html.Div([project_dropdown(projects, value), theme_controls()], className="filter-bar")
