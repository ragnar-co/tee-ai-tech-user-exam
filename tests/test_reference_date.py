"""T-R*: the reference date (stored per run) drives MET-04/MET-05; no hidden clock (F1).

Trace map: T-R01..T-R05 test_r01_to_r05 | T-R06 test_r06 | T-R07 test_r07 | T-R08 test_r08 |
T-R09 test_r09 / test_r09b | T-R10 test_r10_* (constant, stored value, ANALYTICS_CHANGELOG entry).
"""

from __future__ import annotations

import re
from datetime import date

import pytest

from src import ingest, metrics, settings
from tests import reference_calc
from tests.conftest import (
    GOLDEN_CSV,
    REFERENCE_DATE,
    SAMPLE_CSV,
    TEST_REFERENCE_DATE,
    sql_rows,
    write_csv,
)

pytestmark = pytest.mark.unit

CHANGELOG = settings.ROOT_DIR / "docs" / "data-analytics" / "ANALYTICS_CHANGELOG.md"


def _one(tmp_path, due, status, ref=TEST_REFERENCE_DATE):
    db = tmp_path / f"{due}-{status}.duckdb"
    csv_path = write_csv(tmp_path / f"{due}-{status}.csv",
                         [["T1", "P01 - Alpha", "Synthetic", "Owner-001", due, status]])
    ingest.run_ingest(csv_path, ref, db)
    return sql_rows(db, "SELECT is_overdue, days_overdue FROM stg_actions")[0]


@pytest.mark.parametrize(
    ("due", "status", "expected"),
    [
        ("2026-09-14", "todo", (True, 1)),  # T-R01
        ("2026-09-15", "todo", (False, 0)),  # T-R02 due == ref
        ("2026-09-16", "todo", (False, 0)),  # T-R03
        ("2026-08-01", "done", (False, 0)),  # T-R04
        ("2026-09-05", "in_progress", (True, 10)),  # T-R05
        ("2026-09-14", "in_progress", (True, 1)),
    ],
)
def test_r01_to_r05(tmp_path, due, status, expected):
    assert _one(tmp_path, due, status) == expected


def test_r06_golden_at_three_dates(tmp_path):
    seen = {}
    for ref, overdue, max_days in [(date(2026, 9, 15), 5, 59), (date(2026, 9, 14), 4, 58),
                                   (date(2026, 10, 2), 8, 76)]:
        db = tmp_path / f"{ref}.duckdb"
        ingest.run_ingest(GOLDEN_CSV, ref, db)
        p = metrics.portfolio(db_path=db)
        detail = metrics.overdue_detail(db_path=db)
        assert p["overdue_actions"] == overdue
        assert max(r["days_overdue"] for r in detail) == max_days
        seen[ref] = {r["action_id"] for r in detail}
    assert "A001" in seen[date(2026, 9, 15)] and "A001" not in seen[date(2026, 9, 14)]


def test_r07_no_clock_in_metric_code():
    root = settings.ROOT_DIR
    targets = [root / "src" / "metrics.py", *(root / "sql" / "10_staging").glob("*.sql"),
               *(root / "sql" / "20_metrics").glob("*.sql")]
    dash = root / "dashboard"
    if dash.exists():
        targets += [p for p in dash.rglob("*.py")]
    pattern = re.compile(r"date\.today|datetime\.now|datetime\.today|current_date|\bnow\s*\(")
    offenders = [str(p) for p in targets if pattern.search(p.read_text(encoding="utf-8"))]
    assert offenders == []


@pytest.mark.sample
def test_r08_sample_informational_numbers(db_path):
    ingest.run_ingest(SAMPLE_CSV, REFERENCE_DATE, db_path)
    exp = reference_calc.portfolio(reference_calc.load(SAMPLE_CSV), REFERENCE_DATE)
    got = metrics.portfolio(db_path=db_path)
    for k, v in got.items():
        assert v == pytest.approx(exp[k])
    detail = metrics.overdue_detail(db_path=db_path)
    assert max(r["days_overdue"] for r in detail) == exp["max_days_overdue"]


@pytest.mark.parametrize("ref", [date(2026, 7, 1), date(2026, 9, 14), date(2026, 9, 15),
                                 date(2027, 1, 1)])
def test_r09_parametrized_dates(tmp_path, ref):
    db = tmp_path / "r.duckdb"
    ingest.run_ingest(GOLDEN_CSV, ref, db)
    exp = reference_calc.portfolio(reference_calc.load(GOLDEN_CSV), ref)
    assert metrics.portfolio(db_path=db)["overdue_actions"] == exp["overdue_actions"]
    assert {date(2026, 7, 1): 0, date(2026, 9, 14): 4, date(2026, 9, 15): 5,
            date(2027, 1, 1): 8}[ref] == exp["overdue_actions"]


@pytest.mark.sample
def test_r09b_sample_at_non_reference_date(tmp_path):
    db = tmp_path / "s.duckdb"
    ingest.run_ingest(SAMPLE_CSV, TEST_REFERENCE_DATE, db)
    exp = reference_calc.portfolio(reference_calc.load(SAMPLE_CSV), TEST_REFERENCE_DATE)
    assert metrics.portfolio(db_path=db)["overdue_actions"] == exp["overdue_actions"]


@pytest.mark.sample
def test_r10_reference_date_guard(db_path):
    assert REFERENCE_DATE == date(2026, 10, 2) == date.fromisoformat(settings.REFERENCE_DATE)
    assert TEST_REFERENCE_DATE != REFERENCE_DATE
    ingest.run_ingest(SAMPLE_CSV, REFERENCE_DATE, db_path)
    assert metrics.get_run_info(db_path=db_path)["reference_date"] == "2026-10-02"


def test_r10_changelog_records_reference_date_decision():  # T-R10
    """The REFERENCE_DATE decision is recorded in ANALYTICS_CHANGELOG and matches T-R08 values."""
    text = CHANGELOG.read_text(encoding="utf-8")
    start = text.index("### Recorded Decision: REFERENCE_DATE")
    end = text.find("\n### ", start + 5)
    entry = text[start:end if end != -1 else None]
    assert "| changed_item | `REFERENCE_DATE` |" in entry
    assert f"| after_value | `{REFERENCE_DATE.isoformat()}`" in entry
    assert "breaking_change" in entry and "approved_by" in entry
    assert "MET-04" in entry and "MET-05" in entry
    # the informational numbers in the entry are the independent calculator's (T-F01), not hand-typed
    exp = reference_calc.portfolio(reference_calc.load(SAMPLE_CSV), REFERENCE_DATE)
    for needle in (f"overdue {exp['overdue_actions']:,}",
                   f"max `days_overdue` {exp['max_days_overdue']}",
                   f"total {exp['total_actions']:,}", f"completed {exp['completed_actions']:,}",
                   f"open {exp['open_actions']:,}"):
        assert needle in entry, needle
