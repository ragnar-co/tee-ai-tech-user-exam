"""T-X01, T-X02: CSV (source system) vs DuckDB reconciliation on the real sample CSV.

Trace map: T-X01 test_x01_* (aggregates, per portfolio / project / owner) |
T-X02 test_x02_* (row-level checksum of (action_id, flags, days_overdue), every row, 0 tolerance).
The independent computation is tests/reference_calc.py (csv module + METRIC_SPEC, no DuckDB).
"""

from __future__ import annotations

import hashlib
from collections import Counter

import pytest

from src import ingest, metrics
from tests import reference_calc
from tests.conftest import REFERENCE_DATE, SAMPLE_CSV, sql_rows

pytestmark = [pytest.mark.integration, pytest.mark.sample]


@pytest.fixture(scope="module")
def sample_db(tmp_path_factory):
    db = tmp_path_factory.mktemp("recon") / "sample.duckdb"
    assert ingest.run_ingest(SAMPLE_CSV, REFERENCE_DATE, db).exit_code == 0
    return db


def _digest(rows) -> str:
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda r: r[0]):
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()


def test_x01_aggregates_match_csv(sample_db):
    rows = reference_calc.load(SAMPLE_CSV)
    assert metrics.portfolio(db_path=sample_db) == pytest.approx(
        {k: v for k, v in reference_calc.portfolio(rows, REFERENCE_DATE).items()
         if k != "max_days_overdue"})
    for p in sorted({r["project_name"] for r in rows}):
        exp = reference_calc.portfolio(rows, REFERENCE_DATE, p)
        got = metrics.portfolio(p, db_path=sample_db)
        assert got == pytest.approx({k: v for k, v in exp.items() if k != "max_days_overdue"}), p
    by_owner = Counter(r["owner"] for r in rows
                       if reference_calc.flags(r, REFERENCE_DATE)["is_overdue"])
    got_owner = {o["owner"]: o["overdue_actions"] for o in metrics.by_owner(db_path=sample_db)}
    assert got_owner == dict(by_owner)


def test_x02_row_level_checksum_all_rows(sample_db):
    rows = reference_calc.load(SAMPLE_CSV)
    expected = []
    for r in rows:
        f = reference_calc.flags(r, REFERENCE_DATE)
        expected.append((r["action_id"], f["is_completed"], f["is_open"], f["is_overdue"],
                         f["days_overdue"]))
    got = sql_rows(sample_db, "SELECT action_id, is_completed, is_open, is_overdue, days_overdue "
                              "FROM stg_actions")
    assert len(got) == len(expected) == len({e[0] for e in expected})  # ids unique, none dropped
    assert _digest(got) == _digest(expected)
    assert sorted(got) == sorted(expected)  # equality: a checksum miss shows the offending row
    # the loaded text columns are byte-identical to the CSV too
    src = sorted((r["action_id"], r["project_name"], r["action_name"], r["owner"], r["due_date"],
                  r["status"]) for r in rows)
    stg = sorted((a, p, n, o, str(d), s) for a, p, n, o, d, s in sql_rows(
        sample_db, "SELECT action_id, project_name, action_name, owner, due_date, status "
                   "FROM stg_actions"))
    assert stg == src
