"""T-I01..T-I04, T-I07..T-I10 and structural checks T-S*.

Trace map: T-I01 test_i01 | T-I02 test_i02 | T-I03 test_i03/i03b | T-I04 test_i04 |
T-I07 test_i07 | T-I08 test_i08 | T-I09 test_i09 | T-I10 test_i10 |
T-S01..S05,S07 test_s_structure | T-S06 test_s06_* | T-S08 test_s_no_secret_columns |
T-S09 test_s09_* | T-S10 test_s10_* | T-S07 test_s_dq_check_names_and_severity_in_enum.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date

import duckdb
import pytest

from src import ingest, metrics, settings, validation
from tests import reference_calc
from tests.conftest import (
    FIXTURES,
    GOLDEN_CSV,
    REFERENCE_DATE,
    SAMPLE_CSV,
    TEST_REFERENCE_DATE,
    golden_rows,
    sql_rows,
    write_csv,
)

pytestmark = pytest.mark.integration

ROOT = settings.ROOT_DIR


def test_i01_end_to_end_golden(golden_db):
    run = sql_rows(golden_db, "SELECT status, reference_date, source_row_count FROM ingestion_runs")
    assert run == [("succeeded", TEST_REFERENCE_DATE, 12)]
    assert sql_rows(golden_db, "SELECT count(*) FROM raw_actions")[0][0] == 12
    flags = {
        r[0]: r[1:]
        for r in sql_rows(
            golden_db,
            "SELECT action_id, is_completed, is_open, is_overdue, days_overdue FROM stg_actions",
        )
    }
    ref = reference_calc.load(GOLDEN_CSV)
    for row in ref:
        f = reference_calc.flags(row, TEST_REFERENCE_DATE)
        assert flags[row["action_id"]] == (
            f["is_completed"], f["is_open"], f["is_overdue"], f["days_overdue"]
        )


@pytest.mark.sample
def test_i02_sample_csv_end_to_end(db_path):
    r = ingest.run_ingest(SAMPLE_CSV, REFERENCE_DATE, db_path)
    assert r.exit_code == 0
    rows = reference_calc.load(SAMPLE_CSV)
    assert r.source_row_count == r.valid_row_count == len(rows)
    assert metrics.portfolio(db_path=db_path)["total_actions"] == len(rows)


def test_i03_cli_args(tmp_path):
    db = tmp_path / "cli.duckdb"
    base = [sys.executable, "-m", "src.ingest", "--db", str(db)]

    def run(*args):
        return subprocess.run([*base, *args], cwd=ROOT, capture_output=True, text=True,
                              check=False)

    assert run("--input", str(GOLDEN_CSV)).returncode == 2  # no --reference-date, no fallback
    assert run("--input", str(GOLDEN_CSV), "--reference-date", "2026-13-40").returncode == 2
    assert run("--input", str(GOLDEN_CSV), "--reference-date", "2026-9-15").returncode == 2
    assert run("--input", str(tmp_path / "missing.csv"), "--reference-date", "2026-09-15"
               ).returncode == 2
    assert not db.exists()  # nothing written for any bad-argument case
    ok = run("--input", str(GOLDEN_CSV), "--reference-date", "2026-09-15")
    assert ok.returncode == 0 and "status: succeeded" in ok.stdout and db.exists()
    bad = run("--input", str(FIXTURES / "invalid_mixed_rows.csv"), "--reference-date", "2026-09-15")
    assert bad.returncode == 1 and "findings:" in bad.stdout
    assert "Owner-" not in bad.stdout


def test_i03b_unreadable_and_header_only(tmp_path, db_path):
    binary = tmp_path / "bin.csv"
    binary.write_bytes(b"\xff\xfe\x00bad")
    assert ingest.run_ingest(binary, TEST_REFERENCE_DATE, db_path).exit_code == 2
    header_only = write_csv(tmp_path / "h.csv", [])
    assert ingest.run_ingest(header_only, TEST_REFERENCE_DATE, db_path).exit_code == 2
    assert not db_path.exists()


def test_i04_failed_run_is_not_latest(golden_db):
    good = metrics.get_run_info(db_path=golden_db)["run_id"]
    r = ingest.run_ingest(FIXTURES / "invalid_mixed_rows.csv", TEST_REFERENCE_DATE, golden_db)
    assert r.exit_code == 1 and r.run_id > good
    assert metrics.get_run_info(db_path=golden_db)["run_id"] == good
    assert metrics.portfolio(db_path=golden_db)["total_actions"] == 12


def test_i07_rerun_after_failure_creates_new_run(tmp_path, db_path):
    rows = golden_rows()
    bad = [r[:] for r in rows]
    bad[0][4] = "not-a-date"
    p = tmp_path / "x.csv"
    assert ingest.run_ingest(write_csv(p, bad), TEST_REFERENCE_DATE, db_path).exit_code == 1
    fixed = ingest.run_ingest(write_csv(p, rows), TEST_REFERENCE_DATE, db_path)
    assert fixed.exit_code == 0 and fixed.status == "succeeded"
    assert sql_rows(db_path, "SELECT status FROM ingestion_runs ORDER BY run_id") == [
        ("failed",), ("succeeded",)]


def test_i08_atomicity_on_stg_error(monkeypatch, db_path):
    def boom(con, run_id):
        raise RuntimeError("injected")

    monkeypatch.setattr(ingest, "st06_build_stg", boom)
    r = ingest.run_ingest(GOLDEN_CSV, TEST_REFERENCE_DATE, db_path)
    assert r.exit_code == 3 and r.status == "failed"
    assert sql_rows(db_path, "SELECT count(*) FROM raw_actions")[0][0] == 0
    assert sql_rows(db_path, "SELECT count(*) FROM stg_actions")[0][0] == 0
    assert sql_rows(db_path, "SELECT status FROM ingestion_runs") == [("failed",)]
    assert metrics.get_run_info(db_path=db_path) is None


def test_i09_backfill_latest_is_max_run_id(tmp_path, db_path):
    """Characterization (METRIC_LOGIC OQ2): loading an older file later makes it the latest."""
    newer = write_csv(tmp_path / "new.csv", golden_rows()[:6])
    ingest.run_ingest(GOLDEN_CSV, date(2026, 9, 15), db_path)
    ingest.run_ingest(newer, date(2026, 9, 8), db_path)  # older reference date, loaded later
    assert metrics.get_run_info(db_path=db_path)["reference_date"] == "2026-09-08"


def test_i10_db_locked_by_other_process_exit_3(tmp_path):  # T-I10
    """Another process holds the DB file: exit 3 (not 0/1/2); no run left 'running'."""
    db = tmp_path / "locked.duckdb"
    assert ingest.run_ingest(GOLDEN_CSV, TEST_REFERENCE_DATE, db).exit_code == 0
    holder = subprocess.Popen(
        [sys.executable, "-c",
         ("import duckdb,sys,time;c=duckdb.connect(sys.argv[1]);print('ready',flush=True);"
          "time.sleep(30)"), str(db)], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "ready"
        r = ingest.run_ingest(GOLDEN_CSV, date(2026, 9, 14), db)
        cli = subprocess.run(
            [sys.executable, "-m", "src.ingest", "--db", str(db), "--input", str(GOLDEN_CSV),
             "--reference-date", "2026-09-14"], cwd=ROOT, capture_output=True, text=True,
            check=False)
    finally:
        holder.kill()
        holder.wait()
    assert r.exit_code == 3
    assert cli.returncode == 3
    assert sql_rows(db, "SELECT count(*) FROM ingestion_runs WHERE status = 'running'") == [(0,)]
    assert sql_rows(db, "SELECT count(*) FROM ingestion_runs") == [(1,)]  # nothing half-written


def test_s_structure(golden_db):  # T-S01..S07, S10
    q = lambda s: sql_rows(golden_db, s)
    assert q("SELECT count(*) FROM stg_actions WHERE is_open = is_completed")[0][0] == 0  # S01
    assert q("SELECT count(*) FROM stg_actions WHERE is_overdue AND NOT is_open")[0][0] == 0  # S02
    assert q("SELECT count(*) FROM stg_actions WHERE is_overdue <> (days_overdue > 0)")[0][0] == 0
    for name in ("RI-01", "RI-02", "RI-03", "RI-04", "RI-05"):  # S04/S05/S07
        assert q(validation.quality_sql(name)) == [], name
    run = q("SELECT status, completed_at FROM ingestion_runs")[0]  # S06
    assert run[0] == "succeeded" and run[1] is not None
    assert {c[0] for c in q("DESCRIBE stg_actions")} == {
        "run_id", "action_id", "project_name", "action_name", "owner", "due_date", "status",
        "is_completed", "is_open", "is_overdue", "days_overdue", "loaded_at"}
    assert {c[0] for c in q("DESCRIBE raw_actions")} == {
        "run_id", "action_id", "project_name", "action_name", "owner", "due_date_raw", "status",
        "source_row_number", "loaded_at"}
    assert {c[0] for c in q("DESCRIBE ingestion_runs")} == {
        "run_id", "source_file", "source_hash", "reference_date", "started_at", "completed_at",
        "source_row_count", "valid_row_count", "invalid_row_count", "status"}
    assert {c[0] for c in q("DESCRIBE executive_summaries")} == {
        "summary_id", "created_at", "reference_date", "project_filter", "source_run_id",
        "summary_text", "provider", "model_name", "prompt_version"}
    assert {c[0] for c in q("DESCRIBE data_quality_results")} == {
        "quality_result_id", "run_id", "check_name", "record_key", "severity_class", "message",
        "created_at"}


def test_s06_running_run_is_never_latest(golden_db):  # T-S06
    """Latest = last 'succeeded'; a newer 'running' row (completed_at NULL) must be ignored."""
    good = metrics.get_run_info(db_path=golden_db)["run_id"]
    con = duckdb.connect(str(golden_db))
    try:
        stuck = con.execute(
            "INSERT INTO ingestion_runs (source_file, source_hash, reference_date, started_at,"
            " status) VALUES ('x.csv', 'h', DATE '2026-10-02', now(), 'running') RETURNING run_id"
        ).fetchone()[0]
    finally:
        con.close()
    assert stuck > good
    assert sql_rows(golden_db, "SELECT completed_at FROM ingestion_runs WHERE status='running'"
                    ) == [(None,)]
    assert metrics.get_run_info(db_path=golden_db)["run_id"] == good
    assert metrics.portfolio(db_path=golden_db)["total_actions"] == 12
    assert sql_rows(golden_db, (ROOT / "sql/20_metrics/latest_run.sql").read_text()) == [(good,)]


def test_s06_run_transitions_and_completed_at(db_path):  # T-S06
    ok = ingest.run_ingest(GOLDEN_CSV, TEST_REFERENCE_DATE, db_path)
    bad = ingest.run_ingest(FIXTURES / "invalid_mixed_rows.csv", TEST_REFERENCE_DATE, db_path)
    rows = {r[0]: r[1:] for r in sql_rows(
        db_path, "SELECT run_id, status, completed_at, started_at FROM ingestion_runs")}
    assert rows[ok.run_id][0] == "succeeded" and rows[bad.run_id][0] == "failed"
    for _status, completed, started in rows.values():
        assert completed is not None and completed >= started  # never 'running' once finished
    assert "running" not in {v[0] for v in rows.values()}


def test_s09_ri04_on_populated_executive_summaries(golden_db):  # T-S09
    run_id = metrics.get_run_info(db_path=golden_db)["run_id"]
    con = duckdb.connect(str(golden_db))
    try:
        for pf in (None, "P01 - Alpha"):
            con.execute(
                "INSERT INTO executive_summaries (created_at, reference_date, project_filter,"
                " source_run_id, summary_text, provider, model_name, prompt_version) VALUES "
                "(now(), DATE '2026-09-15', ?, ?, 'draft', 'openrouter', 'm', 'v1')",
                [pf, run_id])
    finally:
        con.close()
    assert sql_rows(golden_db, "SELECT count(*) FROM executive_summaries") == [(2,)]
    assert sql_rows(golden_db, validation.quality_sql("RI-04")) == []  # populated, still 0 rows
    con = duckdb.connect(str(golden_db))  # sanity: the check really detects an orphan
    try:
        con.execute(
            "INSERT INTO executive_summaries (created_at, reference_date, source_run_id,"
            " summary_text, provider, model_name, prompt_version) VALUES "
            "(now(), DATE '2026-09-15', 999, 'x', 'openrouter', 'm', 'v1')")
    finally:
        con.close()
    assert len(sql_rows(golden_db, validation.quality_sql("RI-04"))) == 1


# DATA_MODEL_SPEC: table -> {column: (type, nullable)}
_SPEC = {
    "ingestion_runs": {
        "run_id": ("BIGINT", False), "source_file": ("VARCHAR", False),
        "source_hash": ("VARCHAR", False), "reference_date": ("DATE", False),
        "started_at": ("TIMESTAMP", False), "completed_at": ("TIMESTAMP", True),
        "source_row_count": ("INTEGER", True), "valid_row_count": ("INTEGER", True),
        "invalid_row_count": ("INTEGER", True), "status": ("VARCHAR", False)},
    "raw_actions": {
        "run_id": ("BIGINT", False), "action_id": ("VARCHAR", True),
        "project_name": ("VARCHAR", True), "action_name": ("VARCHAR", True),
        "owner": ("VARCHAR", True), "due_date_raw": ("VARCHAR", True),
        "status": ("VARCHAR", True), "source_row_number": ("INTEGER", False),
        "loaded_at": ("TIMESTAMP", False)},
    "stg_actions": {
        "run_id": ("BIGINT", False), "action_id": ("VARCHAR", False),
        "project_name": ("VARCHAR", False), "action_name": ("VARCHAR", False),
        "owner": ("VARCHAR", False), "due_date": ("DATE", False), "status": ("VARCHAR", False),
        "is_completed": ("BOOLEAN", False), "is_open": ("BOOLEAN", False),
        "is_overdue": ("BOOLEAN", False), "days_overdue": ("INTEGER", False),
        "loaded_at": ("TIMESTAMP", False)},
    "data_quality_results": {
        "quality_result_id": ("BIGINT", False), "run_id": ("BIGINT", False),
        "check_name": ("VARCHAR", False), "record_key": ("VARCHAR", True),
        "severity_class": ("VARCHAR", False), "message": ("VARCHAR", False),
        "created_at": ("TIMESTAMP", False)},
    "executive_summaries": {
        "summary_id": ("BIGINT", False), "created_at": ("TIMESTAMP", False),
        "reference_date": ("DATE", False), "project_filter": ("VARCHAR", True),
        "source_run_id": ("BIGINT", False), "summary_text": ("VARCHAR", False),
        "provider": ("VARCHAR", False), "model_name": ("VARCHAR", False),
        "prompt_version": ("VARCHAR", False)},
    "app_config": {
        "config_key": ("VARCHAR", False), "config_value": ("VARCHAR", False),
        "updated_at": ("TIMESTAMP", False)},
}


@pytest.mark.parametrize("table", sorted(_SPEC))
def test_s10_schema_names_types_nullability(golden_db, table):  # T-S10
    got = {c[0]: (c[1], c[2] == "YES")
           for c in sql_rows(golden_db, f"DESCRIBE {table}")}
    # PRIMARY KEY columns report null='NO'; compare name set first for a clear diff
    assert set(got) == set(_SPEC[table])
    assert got == _SPEC[table]


def test_s_no_secret_columns(golden_db):  # T-S08
    cols = {c[0].lower() for t in ("app_config", "ingestion_runs", "executive_summaries")
            for c in sql_rows(golden_db, f"DESCRIBE {t}")}
    assert not any("api_key" in c or "base_url" in c for c in cols)
    cfg = sql_rows(golden_db, "SELECT config_key FROM app_config")
    assert cfg == [("reference_date",)]


def test_s_dq_check_names_and_severity_in_enum(db_path):  # T-S07
    ingest.run_ingest(FIXTURES / "invalid_mixed_rows.csv", TEST_REFERENCE_DATE, db_path)
    ingest.run_ingest(FIXTURES / "new_status.csv", TEST_REFERENCE_DATE, db_path)
    valid_checks = {f"DQ-{i:02d}" for i in range(1, 11)}
    for check, sev in sql_rows(db_path, "SELECT check_name, severity_class FROM data_quality_results"):
        assert check in valid_checks
        assert sev in {"blocking", "warning", "investigation"}
