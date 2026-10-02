"""T-V*: every DQ rule has at least one test (TESTING_STRATEGY).

Trace map: T-V01 test_v01 | T-V02 test_v02 | T-V03..T-V09 test_v03_to_v09 (DQ-02/04/05/06/08) and
test_v08 (DQ-07) | T-V04 duplicate ids | T-V10 test_v10 | T-V11 test_v11 | T-V12 test_v12 |
T-V13 test_v13 | T-V14 test_v14 | T-V15 test_v15 (SQL vs tests/reference_validation.py) |
T-V16 test_v16.
"""

from __future__ import annotations

import pytest

from src import ingest, validation
from tests import reference_validation
from tests.conftest import FIXTURES, TEST_REFERENCE_DATE, golden_rows, sql_rows, write_csv

pytestmark = pytest.mark.unit


def _run(csv_path, db):
    return ingest.run_ingest(csv_path, TEST_REFERENCE_DATE, db)


def _findings(db, run_id):
    return sql_rows(
        db,
        "SELECT check_name, record_key, severity_class FROM data_quality_results "
        "WHERE run_id = ? ORDER BY check_name, record_key",
        [run_id],
    )


def _counts(db):
    return sql_rows(
        db, "SELECT (SELECT count(*) FROM raw_actions), (SELECT count(*) FROM stg_actions)"
    )[0]


def test_v01_missing_column_blocks(db_path):  # T-V01
    r = _run(FIXTURES / "invalid_missing_owner_column.csv", db_path)
    assert r.exit_code == 1 and r.status == "failed"
    assert ("DQ-01", "owner", "blocking") in _findings(db_path, r.run_id)
    assert _counts(db_path) == (0, 0)
    status, valid, invalid = sql_rows(
        db_path, "SELECT status, valid_row_count, invalid_row_count FROM ingestion_runs"
    )[0]
    assert status == "failed" and valid is None and invalid is None


def test_v02_extra_column_is_warning(db_path):  # T-V02
    r = _run(FIXTURES / "extra_column.csv", db_path)
    assert r.exit_code == 0 and r.status == "succeeded"
    assert ("DQ-01", "priority", "warning") in _findings(db_path, r.run_id)
    assert _counts(db_path) == (2, 2)
    cols = [c[0] for c in sql_rows(db_path, "DESCRIBE raw_actions")]
    assert "priority" not in cols


@pytest.mark.parametrize(
    ("check", "col_index", "bad_value"),
    [
        ("DQ-02", 0, ""),
        ("DQ-02", 0, "   "),
        ("DQ-04", 1, ""),
        ("DQ-05", 2, ""),
        ("DQ-06", 3, ""),
        ("DQ-08", 5, ""),
    ],
)
def test_v03_to_v09_empty_required_fields(tmp_path, db_path, check, col_index, bad_value):
    rows = golden_rows()
    rows[2][col_index] = bad_value  # source row 3
    r = _run(write_csv(tmp_path / "x.csv", rows), db_path)
    assert r.exit_code == 1
    assert (check, "3", "blocking") in _findings(db_path, r.run_id)
    assert (r.valid_row_count, r.invalid_row_count) == (11, 1)
    assert _counts(db_path) == (0, 0)


def test_v04_duplicate_ids_one_finding_two_invalid(tmp_path, db_path):  # T-V04
    rows = golden_rows()
    rows[1][0] = rows[0][0]
    r = _run(write_csv(tmp_path / "x.csv", rows), db_path)
    f = [x for x in _findings(db_path, r.run_id) if x[0] == "DQ-03"]
    assert f == [("DQ-03", "A001", "blocking")]
    assert r.invalid_row_count == 2


@pytest.mark.parametrize(
    "bad", ["", "2026/10/01", "2026-02-30", "2026-1-5", " 2026-09-14", "2026-09-14 ", "14-09-2026"]
)
def test_v08_due_date_invalid_formats(tmp_path, db_path, bad):  # T-V08 (DQ-07)
    rows = golden_rows()
    rows[4][4] = bad
    r = _run(write_csv(tmp_path / "x.csv", rows), db_path)
    assert r.exit_code == 1
    assert ("DQ-07", "5", "blocking") in _findings(db_path, r.run_id)


def test_v10_new_status_is_investigation_and_counted_open(db_path):  # T-V10 (DQ-09)
    r = _run(FIXTURES / "new_status.csv", db_path)
    assert r.exit_code == 0 and r.status == "succeeded"
    f = _findings(db_path, r.run_id)
    assert ("DQ-09", "blocked", "investigation") in f
    assert ("DQ-09", "Done", "investigation") in f
    assert len([x for x in f if x[0] == "DQ-09"]) == 2
    # not mapped: stored verbatim, counted as open
    got = dict(sql_rows(db_path, "SELECT action_id, status || '/' || is_open FROM stg_actions"))
    assert got["N001"] == "blocked/true" and got["N002"] == "Done/true"
    assert got["N003"] == "done/false"


def test_v11_reconcile_counts(golden_db):  # T-V11 (DQ-10)
    s, v, i, raw, stg = sql_rows(
        golden_db,
        "SELECT source_row_count, valid_row_count, invalid_row_count, "
        "(SELECT count(*) FROM raw_actions), (SELECT count(*) FROM stg_actions) "
        "FROM ingestion_runs",
    )[0]
    assert s == v + i == raw == stg == 12 and i == 0


def test_v12_reconcile_failure_rolls_back(monkeypatch, db_path):  # T-V12
    real = ingest.st06_build_stg

    def lossy(con, run_id):
        real(con, run_id)
        con.execute("DELETE FROM stg_actions WHERE action_id = 'A001'")

    monkeypatch.setattr(ingest, "st06_build_stg", lossy)
    r = ingest.run_ingest(FIXTURES / "actions_small.csv", TEST_REFERENCE_DATE, db_path)
    assert r.exit_code == 1 and r.status == "failed"
    assert _counts(db_path) == (0, 0)
    assert ("DQ-10", str(r.run_id), "blocking") in _findings(db_path, r.run_id)


def test_v13_multi_rule_row_counted_once(db_path):  # T-V13
    r = _run(FIXTURES / "invalid_mixed_rows.csv", db_path)
    checks_row8 = {f[0] for f in _findings(db_path, r.run_id) if f[1] == "8"}
    assert {"DQ-06", "DQ-08"} <= checks_row8


def test_v14_every_bad_row_reported_nothing_dropped(db_path):  # T-V14
    r = _run(FIXTURES / "invalid_mixed_rows.csv", db_path)
    assert r.exit_code == 1
    f = _findings(db_path, r.run_id)
    assert ("DQ-02", "1", "blocking") in f
    assert ("DQ-03", "X001", "blocking") in f
    assert ("DQ-04", "4", "blocking") in f
    assert ("DQ-07", "5", "blocking") in f
    assert ("DQ-06", "8", "blocking") in f and ("DQ-08", "8", "blocking") in f
    assert len(f) == 6
    # rows 1,2,3,4,5,8 invalid (dup counts both rows); rows 6,7 valid
    assert (r.source_row_count, r.valid_row_count, r.invalid_row_count) == (8, 2, 6)
    assert _counts(db_path) == (0, 0)  # whole file rejected, no partial load


def _v15_corpus(tmp_path):
    """Wrong-file corpus covering T-V01..T-V14: fixtures + one mutation per rule/column."""
    out = [(f.name, f) for f in sorted(FIXTURES.glob("*.csv"))]
    base = golden_rows()

    def mutate(label, fn, header=None):
        rows = [r[:] for r in base]
        fn(rows)
        out.append((label, write_csv(tmp_path / f"{label}.csv", rows, header)))

    for col, name in enumerate(HEADER_COLS):
        for bad in ("", "   ", "\u00a0", "\u200b", "\ufeff"):
            mutate(f"blank-{name}-{ord(bad[:1] or ' ')}", lambda r, c=col, b=bad: r[2].__setitem__(c, b))
    for d in ("2026/10/01", "2026-02-30", "2026-1-5", " 2026-09-14", "14-09-2026", "٢٠٢٦-٠٩-١٤"):
        mutate(f"date-{abs(hash(d))}", lambda r, d=d: r[4].__setitem__(4, d))
    mutate("dup-id", lambda r: r[1].__setitem__(0, r[0][0]))
    mutate("dup-id-triple", lambda r: (r[1].__setitem__(0, r[0][0]), r[2].__setitem__(0, r[0][0])))
    mutate("new-status", lambda r: r[3].__setitem__(5, "Blocked"))
    mutate("two-new-status", lambda r: (r[3].__setitem__(5, "blocked"), r[5].__setitem__(5, "DONE")))
    mutate("ctrl-char", lambda r: r[1].__setitem__(2, "x\x01y"))
    mutate("short-row", lambda r: r.__setitem__(4, r[4][:3]))
    mutate("long-row", lambda r: r.__setitem__(4, [*r[4], "extra"]))
    mutate("multi-rule-row", lambda r: (r[6].__setitem__(3, ""), r[6].__setitem__(5, ""),
                                         r[6].__setitem__(4, "nope")))
    mutate("extra-col", lambda r: [x.append("p") for x in r], [*HEADER_COLS, "priority"])
    mutate("missing-two", lambda r: [x.__delitem__(slice(3, 5)) for x in r],
           [*HEADER_COLS[:3], HEADER_COLS[5]])
    mutate("dup-header", lambda r: [x.append("o") for x in r], [*HEADER_COLS, "owner"])
    mutate("reordered", lambda r: [x.reverse() for x in r], list(reversed(HEADER_COLS)))
    return out


HEADER_COLS = ["action_id", "project_name", "action_name", "owner", "due_date", "status"]


def test_v15_sql_outcome_equals_independent_python(tmp_path):  # T-V15 (DQ-01..DQ-12)
    """Pipeline (SQL blocks) vs tests/reference_validation.py on every wrong-file case."""
    names = set(validation._load_blocks())
    for rule in ("DQ-01-missing", "DQ-01-extra", "DQ-02", "DQ-03", "DQ-04", "DQ-05", "DQ-06",
                 "DQ-07", "DQ-08", "DQ-09", "DQ-10", "RI-01", "RI-02", "RI-03", "RI-04", "RI-05"):
        assert rule in names
    corpus = _v15_corpus(tmp_path)
    assert len(corpus) > 40
    for label, path in corpus:
        db = tmp_path / f"{label}.duckdb"
        r = _run(path, db)
        want_findings, want_counts = reference_validation.evaluate(path)
        got = sorted(sql_rows(db, "SELECT check_name, record_key, severity_class "
                                  "FROM data_quality_results WHERE run_id = ?", [r.run_id]))
        assert got == want_findings, label
        assert (r.source_row_count, r.valid_row_count, r.invalid_row_count) == want_counts, label
        blocking = any(f[2] == "blocking" for f in want_findings)
        assert (r.exit_code, r.status) == ((1, "failed") if blocking else (0, "succeeded")), label


def test_v16_bom_and_thai_roundtrip(tmp_path, db_path):  # T-V16
    src = (FIXTURES / "actions_small.csv").read_bytes()
    bom = tmp_path / "bom.csv"
    bom.write_bytes(b"\xef\xbb\xbf" + src)
    r = _run(bom, db_path)
    assert r.exit_code == 0
    name = sql_rows(db_path, "SELECT action_name FROM stg_actions WHERE action_id='A001'")[0][0]
    assert name == "ทบทวนนโยบายความปลอดภัย / สาขา BR-001"
    assert not any(c[0].startswith("﻿") for c in sql_rows(db_path, "DESCRIBE raw_actions"))


def test_findings_do_not_leak_owner_or_action_name(db_path):  # PDPA rule in AGENTS.md
    r = _run(FIXTURES / "invalid_mixed_rows.csv", db_path)
    msgs = " ".join(m[0] for m in sql_rows(db_path, "SELECT message FROM data_quality_results"))
    assert "Owner-" not in msgs and "Synthetic" not in msgs
    assert r.exit_code == 1
