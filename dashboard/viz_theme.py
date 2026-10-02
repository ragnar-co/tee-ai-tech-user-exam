"""viz_theme.py - shared visualization theme (source: VIZ_DESIGN_SPEC.md v1.0.0)."""

COLOR_PALETTE = {
    "light": {
        "background": "#FFFFFF",
        "text": "#1B1F24",
        "text_muted": "#4B5563",
        "grid": "#E3E7EC",
        "series": ["#0072B2", "#C24E00", "#B87800", "#007A5A", "#8E4A9E", "#5F6B7A"],
        "semantic": {"positive": "#007A5A", "alert": "#B42318",
                     "warning": "#B87800", "neutral": "#5F6B7A"},
        "roles": {"completed": "#0072B2", "open_non_overdue": "#B87800",
                  "overdue": "#C24E00"},
    },
    "dark": {
        "background": "#121417",
        "text": "#E6EAF0",
        "text_muted": "#A7B0BC",
        "grid": "#2A2F36",
        "series": ["#56B4E9", "#FF8A4C", "#F0B429", "#2EC4A0", "#C792EA", "#9AA5B1"],
        "semantic": {"positive": "#2EC4A0", "alert": "#FF6B5E",
                     "warning": "#F0B429", "neutral": "#9AA5B1"},
        "roles": {"completed": "#56B4E9", "open_non_overdue": "#F0B429",
                  "overdue": "#FF8A4C"},
    },
    # colorblind-safe variant: blue / grey / vermillion differ in hue AND lightness
    "cvd_light": {
        "background": "#FFFFFF",
        "text": "#1B1F24",
        "text_muted": "#4B5563",
        "grid": "#E3E7EC",
        "series": ["#0072B2", "#C24E00", "#5F6B7A", "#B87800", "#8E4A9E", "#007A5A"],
        "semantic": {"positive": "#0072B2", "alert": "#C24E00",
                     "warning": "#5F6B7A", "neutral": "#5F6B7A"},
        "roles": {"completed": "#0072B2", "open_non_overdue": "#5F6B7A",
                  "overdue": "#C24E00"},
    },
    "cvd_dark": {
        "background": "#121417",
        "text": "#E6EAF0",
        "text_muted": "#A7B0BC",
        "grid": "#2A2F36",
        "series": ["#56B4E9", "#FF8A4C", "#9AA5B1", "#F0B429", "#C792EA", "#2EC4A0"],
        "semantic": {"positive": "#56B4E9", "alert": "#FF8A4C",
                     "warning": "#9AA5B1", "neutral": "#9AA5B1"},
        "roles": {"completed": "#56B4E9", "open_non_overdue": "#9AA5B1",
                  "overdue": "#FF8A4C"},
    },
}

FONT_RULES = {
    "family": ("system-ui, -apple-system, 'Segoe UI', 'Noto Sans Thai', "
               "'Sarabun', Roboto, Arial, sans-serif"),
    "title": {"size": 16, "weight": 600},
    "axis": {"size": 12, "weight": 400},
    "tick": {"size": 11, "weight": 400},
    "tooltip": {"size": 12, "weight": 400, "name_weight": 600},
    "annotation": {"size": 11, "weight": 400},
    "kpi_value": {"size": 28, "weight": 700},
}

CHART_DEFAULTS = {
    "margin": {"l": 56, "r": 24, "t": 48, "b": 48},
    "bar_gap": 0.25,
    "y_axis_zero_based": True,          # bar charts must start at 0
    "number_format": ",d",              # thousands separator
    "percent_format": ".1%",
    "transition_ms": 0,                 # no animation on data refresh (see Interaction Spec)
    "load_transition_ms": 300,
    "reduced_motion_ms": 0,
    "hovermode": "closest",
    "show_legend_max_series": 6,
}


def get_palette(mode="light", colorblind=False):
    """Return palette dict. mode: 'light' | 'dark'."""
    key = ("cvd_" if colorblind else "") + mode
    return COLOR_PALETTE[key]


def plotly_layout(mode="light", colorblind=False):
    """Return a dict usable as plotly Figure.update_layout(**plotly_layout())."""
    p = get_palette(mode, colorblind)
    return {
        "paper_bgcolor": p["background"],
        "plot_bgcolor": p["background"],
        "colorway": p["series"],
        "font": {"family": FONT_RULES["family"], "size": FONT_RULES["axis"]["size"],
                 "color": p["text"]},
        "title": {"font": {"size": FONT_RULES["title"]["size"], "color": p["text"]}},
        "margin": CHART_DEFAULTS["margin"],
        "hovermode": CHART_DEFAULTS["hovermode"],
        "xaxis": {"gridcolor": p["grid"], "tickfont": {"size": FONT_RULES["tick"]["size"]}},
        "yaxis": {"gridcolor": p["grid"], "tickfont": {"size": FONT_RULES["tick"]["size"]},
                  "rangemode": "tozero" if CHART_DEFAULTS["y_axis_zero_based"] else "normal"},
        "transition": {"duration": CHART_DEFAULTS["transition_ms"]},
    }


# ---------------------------------------------------------------------------
# Presentation constants below are additions to the spec snippet (labels per
# BUSINESS_GLOSSARY "Label on dashboard"; stable component IDs for callbacks).
# ---------------------------------------------------------------------------

LABELS = {
    "total_actions": "Total Actions",
    "completed_actions": "Completed",
    "open_actions": "Open",
    "overdue_actions": "Overdue",
    "days_overdue": "Days Overdue",
    "completion_rate": "Completion Rate",
    "owners_with_overdue_actions": "Owners with Overdue",
    "open_not_overdue_actions": "Open (Not Overdue)",
}

ALL_PROJECTS = "All Projects"

MSG_NO_RUN = "ยังไม่มีข้อมูล — ยังไม่เคยโหลด CSV สำเร็จ"
MSG_NO_PROJECT_DATA = "ไม่มีข้อมูลสำหรับ project นี้"
MSG_NO_OVERDUE = "ไม่มี overdue action ณ reference date {date}"


class IDS:
    """Stable component IDs (string constants) for later callbacks."""

    # shared / filters
    PROJECT_DROPDOWN = "project-filter"
    THEME_MODE = "theme-mode"
    CVD_TOGGLE = "cvd-toggle"
    HEADER = "provenance-header"
    # DASH-01
    KPI_ROW = "kpi-row"
    KPI_TOTAL = "kpi-total-actions"  # CH-01
    KPI_COMPLETED = "kpi-completed"  # CH-02
    KPI_OPEN = "kpi-open"  # CH-03
    KPI_OVERDUE = "kpi-overdue"  # CH-04
    KPI_COMPLETION_RATE = "kpi-completion-rate"  # CH-05
    CH_TOTAL_BY_PROJECT = "chart-total-by-project"  # CH-06
    CH_COMPLETED_BY_PROJECT = "chart-completed-by-project"  # CH-07
    CH_OVERDUE_BY_PROJECT = "chart-overdue-by-project"  # CH-08
    CH_COMPOSITION = "chart-composition-by-project"  # CH-09
    CH_COMPLETION_RATE = "chart-completion-rate-by-project"  # CH-10
    COMPOSITION_TOGGLE = "composition-view-toggle"
    GRID_PROJECT_SUMMARY = "grid-project-summary"  # CH-11
    DQ_PANEL = "dq-panel"  # CH-12
    # DASH-02
    KPI_OVERDUE_D2 = "kpi-overdue-d2"  # CH-13
    KPI_OWNERS_OVERDUE = "kpi-owners-overdue"  # CH-14
    GRID_OVERDUE = "grid-overdue-actions"  # CH-15
    CH_OVERDUE_BY_OWNER = "chart-overdue-by-owner"  # CH-16
    CH_OVERDUE_BY_PROJECT_D2 = "chart-overdue-by-project-d2"  # CH-17
    # DASH-03
    EXEC_PANEL = "exec-summary-panel"
    EXEC_REFERENCE_DATE = "exec-reference-date"  # CP-01
    EXEC_GENERATE_BTN = "exec-generate-btn"  # CP-03
    EXEC_CONFIG_MSG = "exec-config-message"
    EXEC_ERROR = "exec-error"
    EXEC_SUMMARY_TEXT = "exec-summary-text"  # CP-04
    EXEC_GENERATED_AT = "exec-generated-at"  # CP-05
    EXEC_MODEL = "exec-model"  # CP-06
    EXEC_STALE_WARNING = "exec-stale-warning"


def all_ids() -> list[str]:
    """Every ID constant (used by tests to assert uniqueness)."""
    return [v for k, v in vars(IDS).items() if not k.startswith("_") and isinstance(v, str)]
