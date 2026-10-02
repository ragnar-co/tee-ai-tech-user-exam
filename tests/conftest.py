"""Shared test constants and helpers. Every test uses its own temp DuckDB file (never data/)."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import duckdb
import pytest

from src import ingest

# Two deliberately different dates (TESTING_STRATEGY rule 1): do not substitute one for the other.
TEST_REFERENCE_DATE = date(2026, 9, 15)  # golden-fixture date; differs from today and REFERENCE_DATE
REFERENCE_DATE = date(2026, 10, 2)  # iteration-1 constant; only for sample-CSV tests

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN_CSV = FIXTURES / "actions_small.csv"
SAMPLE_CSV = Path(__file__).resolve().parent.parent / "src" / "tee_cybersecurity_actions_mock.csv"
HEADER = ["action_id", "project_name", "action_name", "owner", "due_date", "status"]


def write_csv(path: Path, rows: list[list[str]], header: list[str] | None = None) -> Path:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER if header is None else header)
        w.writerows(rows)
    return path


def golden_rows() -> list[list[str]]:
    with open(GOLDEN_CSV, newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))[1:]


def sql_rows(db: Path, sql: str, params=None) -> list[tuple]:
    con = duckdb.connect(str(db), read_only=True)
    try:
        return con.execute(sql, params or []).fetchall()
    finally:
        con.close()


@pytest.fixture
def db_path(tmp_path) -> Path:
    return tmp_path / "test.duckdb"


@pytest.fixture
def golden_db(db_path) -> Path:
    """Golden fixture ingested at TEST_REFERENCE_DATE into a temp DB."""
    r = ingest.run_ingest(GOLDEN_CSV, TEST_REFERENCE_DATE, db_path)
    assert r.exit_code == 0 and r.status == "succeeded"
    return db_path


def ingest_golden_at(db: Path, ref: date):
    return ingest.run_ingest(GOLDEN_CSV, ref, db)
