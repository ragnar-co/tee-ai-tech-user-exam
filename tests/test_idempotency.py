"""T-I05, T-I06: run versioning and idempotent reload (test_i05*, test_i06*)."""

from __future__ import annotations

from datetime import date

import pytest

from src import ingest, metrics
from tests.conftest import GOLDEN_CSV, TEST_REFERENCE_DATE, sql_rows

pytestmark = pytest.mark.integration


def _counts(db):
    return sql_rows(
        db,
        "SELECT (SELECT count(*) FROM ingestion_runs), (SELECT count(*) FROM raw_actions), "
        "(SELECT count(*) FROM stg_actions), (SELECT count(*) FROM data_quality_results)",
    )[0]


def test_i05_same_file_same_date_is_noop(db_path):
    first = ingest.run_ingest(GOLDEN_CSV, TEST_REFERENCE_DATE, db_path)
    before = _counts(db_path)
    second = ingest.run_ingest(GOLDEN_CSV, TEST_REFERENCE_DATE, db_path)
    assert second.exit_code == 0 and second.status == "noop"
    assert second.run_id == first.run_id
    assert _counts(db_path) == before == (1, 12, 12, 0)
    assert sql_rows(db_path, "SELECT count(*) FROM ingestion_runs WHERE status='succeeded'")[0][0] == 1
    assert metrics.portfolio(db_path=db_path)["total_actions"] == 12  # no duplicate counting


def test_i06_same_file_new_reference_date_is_new_run(db_path):
    a = ingest.run_ingest(GOLDEN_CSV, date(2026, 9, 15), db_path)
    b = ingest.run_ingest(GOLDEN_CSV, date(2026, 9, 14), db_path)
    assert a.run_id != b.run_id and b.status == "succeeded"
    got = dict(sql_rows(
        db_path,
        "SELECT run_id, count(*) FILTER (WHERE is_overdue) FROM stg_actions GROUP BY run_id"))
    assert got == {a.run_id: 5, b.run_id: 4}  # both runs kept, untouched
    assert sql_rows(db_path, "SELECT count(*) FROM stg_actions")[0][0] == 24
    assert metrics.portfolio(db_path=db_path)["overdue_actions"] == 4  # latest run


def test_i05b_modified_file_same_date_is_new_run(tmp_path, db_path):
    ingest.run_ingest(GOLDEN_CSV, TEST_REFERENCE_DATE, db_path)
    changed = tmp_path / "c.csv"
    changed.write_text(GOLDEN_CSV.read_text(encoding="utf-8") + "D001,P04 - Delta,Synthetic,"
                       "Owner-004,2026-09-01,todo\n", encoding="utf-8")
    r = ingest.run_ingest(changed, TEST_REFERENCE_DATE, db_path)
    assert r.status == "succeeded" and metrics.portfolio(db_path=db_path)["total_actions"] == 13
