"""T-M*: golden-dataset metric validation through the data-access layer (src/metrics.py).

Trace map: test_m01_to_m04 -> T-M01..M04 | test_m05_and_m08 -> T-M05, T-M08 | test_m06_m07 ->
T-M06, T-M07 | test_m09..m15 -> T-M09..T-M15 (same number) | test_f01 -> T-F01.
T-X01/T-X02 live in tests/test_reconciliation.py.
"""

from __future__ import annotations

import random
from datetime import date

import pytest

from src import ingest, metrics
from tests import reference_calc
from tests.conftest import GOLDEN_CSV, TEST_REFERENCE_DATE, write_csv

pytestmark = pytest.mark.unit

P1, P2, P3 = "P01 - Alpha", "P02 - Beta", "P03 - Gamma"


def test_m01_to_m04_portfolio(golden_db):
    p = metrics.portfolio(db_path=golden_db)
    assert (p["total_actions"], p["completed_actions"], p["open_actions"],
            p["overdue_actions"]) == (12, 4, 8, 5)
    assert p["open_not_overdue_actions"] == 3 and p["owners_with_overdue_actions"] == 3
    assert p["completion_rate"] == pytest.approx(1 / 3)


def test_m05_and_m08_overdue_detail(golden_db):
    rows = metrics.overdue_detail(db_path=golden_db)
    assert [r["action_id"] for r in rows] == ["B002", "A005", "C003", "C001", "A001"]
    assert {r["action_id"]: r["days_overdue"] for r in rows} == {
        "A001": 1, "A005": 10, "B002": 59, "C001": 2, "C003": 3}
    assert set(rows[0]) == {"action_id", "project_name", "action_name", "owner", "due_date",
                            "status", "days_overdue"}
    assert rows[0]["due_date"] == "2026-07-18" and all(r["days_overdue"] > 0 for r in rows)


def test_m06_m07_by_project(golden_db):
    got = {r["project_name"]: r for r in metrics.by_project(db_path=golden_db)}
    expect = {P1: (5, 1, 4, 2, 2, 0.2), P2: (4, 2, 2, 1, 1, 0.5), P3: (3, 1, 2, 2, 0, 1 / 3)}
    assert set(got) == set(expect)
    for name, (t, c, o, ov, ono, rate) in expect.items():
        r = got[name]
        assert (r["total_actions"], r["completed_actions"], r["open_actions"],
                r["overdue_actions"], r["open_not_overdue_actions"]) == (t, c, o, ov, ono)
        assert r["completion_rate"] == pytest.approx(rate)
    # portfolio rate is NOT the mean of project rates
    assert metrics.portfolio(db_path=golden_db)["completion_rate"] != pytest.approx(
        sum(r["completion_rate"] for r in got.values()) / 3)


def test_m09_by_owner(golden_db):
    rows = metrics.by_owner(db_path=golden_db)
    assert rows == [
        {"owner": "Owner-001", "overdue_actions": 2},
        {"owner": "Owner-003", "overdue_actions": 2},
        {"owner": "Owner-002", "overdue_actions": 1},
    ]


def test_m10_project_filter_restricts_rows(golden_db):
    p = metrics.portfolio(P2, db_path=golden_db)
    assert (p["total_actions"], p["completed_actions"], p["open_actions"], p["overdue_actions"],
            p["open_not_overdue_actions"], p["owners_with_overdue_actions"]) == (4, 2, 2, 1, 1, 1)
    assert p["completion_rate"] == pytest.approx(0.5)
    bp = metrics.by_project(P2, db_path=golden_db)
    assert len(bp) == 1 and bp[0]["project_name"] == P2 and bp[0]["total_actions"] == 4
    assert [r["action_id"] for r in metrics.overdue_detail(P2, db_path=golden_db)] == ["B002"]
    assert metrics.by_owner(P2, db_path=golden_db) == [{"owner": "Owner-003", "overdue_actions": 1}]
    # None and the UI label both mean "all"
    assert metrics.portfolio("All Projects", db_path=golden_db) == metrics.portfolio(
        None, db_path=golden_db)
    assert len(metrics.by_project("All Projects", db_path=golden_db)) == 3


def test_m11_invariants(golden_db):
    p = metrics.portfolio(db_path=golden_db)
    rows = metrics.by_project(db_path=golden_db)
    for k in ("total_actions", "completed_actions", "open_actions", "overdue_actions",
              "open_not_overdue_actions"):
        assert sum(r[k] for r in rows) == p[k]
    assert p["open_actions"] == p["total_actions"] - p["completed_actions"]
    assert p["overdue_actions"] <= p["open_actions"]
    assert p["open_not_overdue_actions"] == p["open_actions"] - p["overdue_actions"]
    owners = [metrics.portfolio(n, db_path=golden_db)["owners_with_overdue_actions"]
              for n in (P1, P2, P3)]
    assert owners == [2, 1, 2] and sum(owners) > p["owners_with_overdue_actions"]  # not additive


def test_m12_empty_scope_and_no_run(golden_db, tmp_path):
    for name in ("Nope", "", "x'; DROP TABLE stg_actions; --"):
        p = metrics.portfolio(name, db_path=golden_db)
        assert p["total_actions"] == 0 and p["completion_rate"] == 0
        assert p["owners_with_overdue_actions"] == 0 and p["open_not_overdue_actions"] == 0
        assert metrics.by_project(name, db_path=golden_db) == []
        assert metrics.overdue_detail(name, db_path=golden_db) == []
        assert metrics.by_owner(name, db_path=golden_db) == []
    assert metrics.portfolio(db_path=golden_db)["total_actions"] == 12  # table intact
    missing = tmp_path / "none.duckdb"  # no DB file at all
    assert metrics.get_run_info(db_path=missing) is None
    assert metrics.list_projects(db_path=missing) == []
    assert metrics.portfolio(db_path=missing)["total_actions"] == 0
    assert metrics.by_project(db_path=missing) == []
    assert metrics.overdue_detail(db_path=missing) == []
    assert metrics.by_owner(db_path=missing) == []
    dq = metrics.data_quality_summary(db_path=missing)
    assert dq["run"] is None and dq["findings"] == []


def test_m12b_db_without_succeeded_run(tmp_path):
    bad = tmp_path / "bad.duckdb"
    from tests.conftest import FIXTURES

    ingest.run_ingest(FIXTURES / "invalid_mixed_rows.csv", TEST_REFERENCE_DATE, bad)
    assert metrics.get_run_info(db_path=bad) is None
    assert metrics.portfolio(db_path=bad)["total_actions"] == 0
    dq = metrics.data_quality_summary(db_path=bad)
    assert dq["run"] is None and dq["latest_attempt"]["status"] == "failed"


def test_m12c_bad_project_type(golden_db):
    with pytest.raises(TypeError):
        metrics.portfolio(123, db_path=golden_db)  # type: ignore[arg-type]


def test_m13_owners_with_overdue(golden_db, tmp_path):
    assert [metrics.portfolio(n, db_path=golden_db)["owners_with_overdue_actions"]
            for n in (None, P1, P2, P3)] == [3, 2, 1, 2]
    other = tmp_path / "o.duckdb"
    ingest.run_ingest(GOLDEN_CSV, date(2026, 7, 1), other)
    assert metrics.portfolio(db_path=other)["owners_with_overdue_actions"] == 0


def test_m14_open_not_overdue(golden_db):
    assert [metrics.portfolio(n, db_path=golden_db)["open_not_overdue_actions"]
            for n in (None, P1, P2, P3)] == [3, 2, 1, 0]


def test_m15_portfolio_completion_rate(golden_db):
    assert metrics.portfolio(db_path=golden_db)["completion_rate"] == pytest.approx(1 / 3)
    assert metrics.portfolio(P1, db_path=golden_db)["completion_rate"] == pytest.approx(0.2)
    assert metrics.portfolio("Nope", db_path=golden_db)["completion_rate"] == 0


def test_run_info_projects_and_dq_summary(golden_db):
    info = metrics.get_run_info(db_path=golden_db)
    assert info["reference_date"] == "2026-09-15" and info["status"] == "succeeded"
    assert info["source_row_count"] == 12
    assert metrics.list_projects(db_path=golden_db) == [P1, P2, P3]
    dq = metrics.data_quality_summary(db_path=golden_db)
    assert dq["run"]["run_id"] == info["run_id"] and dq["findings"] == []


def test_f01_formula_consistency_fixed_and_seeded(tmp_path):
    """Independent pure-Python calculator vs SQL, golden + seeded random data."""
    rng = random.Random(20260915)
    rows = []
    for i in range(300):
        rows.append([f"R{i:04d}", f"P{rng.randint(1, 4):02d} - Proj", f"Synthetic {i}",
                     f"Owner-{rng.randint(1, 15):03d}",
                     date.fromordinal(date(2026, 8, 1).toordinal() + rng.randint(0, 100)).isoformat(),
                     rng.choice(["done", "todo", "in_progress"])])
    rand_csv = write_csv(tmp_path / "rand.csv", rows)
    for csv_path in (GOLDEN_CSV, rand_csv):
        data = reference_calc.load(csv_path)
        for ref in (date(2026, 7, 1), date(2026, 9, 14), TEST_REFERENCE_DATE, date(2027, 1, 1)):
            db = tmp_path / f"{csv_path.stem}_{ref}.duckdb"
            ingest.run_ingest(csv_path, ref, db)
            for project in [None, *sorted({r["project_name"] for r in data})]:
                exp = reference_calc.portfolio(data, ref, project)
                got = metrics.portfolio(project, db_path=db)
                for k, v in got.items():
                    assert v == pytest.approx(exp[k]), (csv_path.name, ref, project, k)
                detail = metrics.overdue_detail(project, db_path=db)
                assert len(detail) == exp["overdue_actions"]
                assert max((r["days_overdue"] for r in detail), default=0) == exp["max_days_overdue"]
