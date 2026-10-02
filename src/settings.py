"""Project-wide constants. No secrets live here (CON-21)."""

from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT_DIR / "sql"

# DuckDB warehouse (CON-01).
DB_PATH = ROOT_DIR / "data" / "cybersecurity.duckdb"

# Iteration-1 reference date confirmed by the user (ANALYTICS_CHANGELOG). It is documentation /
# a guard constant only: PIPELINE_SPEC requires --reference-date on every ingest and forbids a
# default, so this value is NOT used as a CLI default and never read by metric logic (CON-06).
REFERENCE_DATE = "2026-10-02"

# Label the UI uses for "no project filter"; the data-access layer maps it to NULL.
ALL_PROJECTS_LABEL = "All Projects"

# Values of enum action_status (owner: DATA_MODEL_SPEC.md). Used only by DQ-09.
ACTION_STATUS_VALUES = ("done", "in_progress", "todo")

# The six source columns of the weekly CSV (DATA_CONTRACT.md).
REQUIRED_COLUMNS = ("action_id", "project_name", "action_name", "owner", "due_date", "status")

# Upper bound on the size of an input CSV, in bytes; larger files are refused with exit code 2
# before anything is read or written. Operational guard only (not a business rule): override with
# the INGEST_MAX_BYTES environment variable. Default 256 MiB (~ 20x the 140k-row stress file).
MAX_INPUT_BYTES = int(os.environ.get("INGEST_MAX_BYTES") or 256 * 1024 * 1024)
