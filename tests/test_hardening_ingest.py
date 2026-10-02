"""Phase 9 hardening probes for ingest/validation (temp DBs only; never data/).

Trace map: extends T-V (DQ rules, malformed CSV), T-I03 (CLI exit 2), T-I05/I06 (idempotency),
T-I10 (lock -> exit 3: test_lock_*, test_readonly_*), T-M12 (nasty project names).
"""

from __future__ import annotations

import csv
import resource
import subprocess
import sys
import time
from datetime import date

import pytest

from src import ingest, metrics, settings
from tests.conftest import GOLDEN_CSV, HEADER, sql_rows, write_csv

REF = date(2026, 9, 15)

pytestmark = pytest.mark.integration
GOOD = ["A-1", "Proj", "Do it", "alice", "2026-09-01", "todo"]


def _raw(path, text: str | bytes):
    data = text.encode("utf-8") if isinstance(text, str) else text
    path.write_bytes(data)
    return path


def _row(**kw):
    r = dict(zip(HEADER, GOOD, strict=True))
    r.update(kw)
    return [r[h] for h in HEADER]


def _run(tmp_path, rows, db=None, ref=REF, header=None, name="in.csv"):
    p = write_csv(tmp_path / name, rows, header)
    return ingest.run_ingest(p, ref, db or tmp_path / "t.duckdb"), p


def _findings(db, check=None):
    q = "SELECT check_name, record_key, severity_class, message FROM data_quality_results"
    if check:
        q += f" WHERE check_name = '{check}'"
    return sql_rows(db, q)


# --- encoding / line endings / quoting ------------------------------------------------------


def test_bom_header_accepted(tmp_path):
    text = ",".join(HEADER) + "\r\n" + ",".join(GOOD) + "\r\n"
    p = _raw(tmp_path / "bom.csv", b"\xef\xbb\xbf" + text.encode())
    r = ingest.run_ingest(p, REF, tmp_path / "t.duckdb")
    assert r.status == "succeeded" and r.source_row_count == 1


def test_crlf_and_lf_equivalent(tmp_path):
    body = ",".join(HEADER) + "\n" + ",".join(GOOD) + "\n"
    a = _raw(tmp_path / "lf.csv", body)
    b = _raw(tmp_path / "crlf.csv", body.replace("\n", "\r\n"))
    ra = ingest.run_ingest(a, REF, tmp_path / "a.duckdb")
    rb = ingest.run_ingest(b, REF, tmp_path / "b.duckdb")
    assert ra.status == rb.status == "succeeded"
    q = "SELECT action_id, status, due_date_raw FROM raw_actions"
    assert sql_rows(tmp_path / "a.duckdb", q) == sql_rows(tmp_path / "b.duckdb", q)


def test_no_trailing_newline_ok(tmp_path):
    p = _raw(tmp_path / "x.csv", ",".join(HEADER) + "\n" + ",".join(GOOD))
    assert ingest.run_ingest(p, REF, tmp_path / "t.duckdb").status == "succeeded"


def test_thai_commas_quotes_newlines_roundtrip(tmp_path):
    name = 'ตรวจสอบ "ไฟร์วอลล์", ข้อ 1\nบรรทัดสอง'
    proj = 'โครงการ, "ทดสอบ"'
    r, _ = _run(tmp_path, [_row(action_name=name, project_name=proj, owner="สมชาย")])
    assert r.status == "succeeded"
    got = sql_rows(tmp_path / "t.duckdb", "SELECT action_name, project_name, owner FROM raw_actions")
    assert got == [(name, proj, "สมชาย")]
    assert metrics.portfolio(proj, tmp_path / "t.duckdb")["total_actions"] == 1


def test_invalid_utf8_exit2_no_db(tmp_path):
    p = _raw(tmp_path / "bad.csv", ",".join(HEADER).encode() + b"\n\xff\xfe,x,y,z,2026-01-01,todo\n")
    r = ingest.run_ingest(p, REF, tmp_path / "t.duckdb")
    assert r.exit_code == 2 and not (tmp_path / "t.duckdb").exists()


def test_newline_in_quoted_field_loads(tmp_path):
    # Regression: the temp-CSV bulk load used to fail (sniffer) -> exit 3.
    r, _ = _run(tmp_path, [_row(action_name="line1\nline2"), _row(action_id="A-2", owner="a\r\nb")])
    assert r.status == "succeeded" and r.exit_code == 0
    got = sql_rows(tmp_path / "t.duckdb", "SELECT action_name, owner FROM raw_actions ORDER BY 1")
    assert got == [("Do it", "a\r\nb"), ("line1\nline2", "alice")]


def test_control_chars_warning_kept_as_is(tmp_path):
    r, _ = _run(tmp_path, [_row(action_name="na\x00me"), _row(action_id="A-2", owner="x\x07y"),
                           _row(action_id="A-3", action_name="tab\tok\nok")])
    assert r.status == "succeeded"
    db = tmp_path / "t.duckdb"
    f = _findings(db, "DQ-12")
    assert sorted((x[1], x[2]) for x in f) == [("1", "warning"), ("2", "warning")]
    assert all("na" not in x[3] and "alice" not in x[3] for x in f)
    assert sql_rows(db, "SELECT action_name FROM raw_actions WHERE action_id='A-1'") == [("na\x00me",)]


def test_stored_failure_messages_have_no_paths_or_content(tmp_path, monkeypatch):
    def boom(con, run_id):
        raise RuntimeError(f"secret-owner {tmp_path}")
    monkeypatch.setattr(ingest, "st06_build_stg", boom)
    r, _ = _run(tmp_path, [GOOD])
    assert r.exit_code == 3
    msgs = " ".join(m for (*_, m) in _findings(tmp_path / "t.duckdb"))
    assert "secret-owner" not in msgs and str(tmp_path) not in msgs and "RuntimeError" in msgs
    assert "secret-owner" not in r.message


def test_source_file_is_basename_only(tmp_path):
    sub = tmp_path / "private" / "dir"
    sub.mkdir(parents=True)
    p = write_csv(sub / "weekly.csv", [GOOD])
    ingest.run_ingest(p, REF, tmp_path / "t.duckdb")
    assert sql_rows(tmp_path / "t.duckdb", "SELECT source_file FROM ingestion_runs") == [("weekly.csv",)]


def test_oversized_input_refused_exit2_no_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MAX_INPUT_BYTES", 50)
    p = write_csv(tmp_path / "big.csv", [GOOD])
    r = ingest.run_ingest(p, REF, tmp_path / "t.duckdb")
    assert r.exit_code == 2 and "INGEST_MAX_BYTES" in r.message and not (tmp_path / "t.duckdb").exists()


# --- whitespace / case ----------------------------------------------------------------------


def test_whitespace_only_fields_blocking(tmp_path):
    r, _ = _run(tmp_path, [_row(project_name="   "), _row(action_id="A-2", owner="\t")])
    assert r.exit_code == 1
    assert {f[0] for f in _findings(tmp_path / "t.duckdb")} >= {"DQ-04", "DQ-06"}


def test_padded_values_kept_verbatim_status_is_investigation(tmp_path):
    # DATA_QUALITY OQ1: no normalisation. ' todo ' is an unknown status (investigation), kept
    # verbatim, counted open; padded project is a distinct project (doc gap, flagged).
    rows = [_row(status=" todo ", project_name="Proj "), _row(action_id="A-2")]
    r, _ = _run(tmp_path, rows)
    assert r.status == "succeeded"
    db = tmp_path / "t.duckdb"
    assert [f[:3] for f in _findings(db, "DQ-09")] == [("DQ-09", " todo ", "investigation")]
    assert sql_rows(db, "SELECT status, is_open, project_name FROM stg_actions ORDER BY action_id")[0] == (
        " todo ", True, "Proj ")
    assert sorted(metrics.list_projects(db)) == ["Proj", "Proj "]


@pytest.mark.parametrize("status", ["Done", "DONE", "In_Progress", "in progress", "done "])
def test_status_case_variants_never_mapped(tmp_path, status):
    r, _ = _run(tmp_path, [_row(status=status, due_date="2026-12-31")])
    assert r.status == "succeeded"
    db = tmp_path / "t.duckdb"
    assert [f[2] for f in _findings(db, "DQ-09")] == ["investigation"]
    # never silently treated as completed
    assert sql_rows(db, "SELECT is_completed, is_open FROM stg_actions") == [(False, True)]
    assert metrics.portfolio(None, db)["completed_actions"] == 0


def test_action_id_case_and_space_are_distinct_ids(tmp_path):
    # DQ-03 compares exactly (DATA_QUALITY): 'a-1' / 'A-1' / 'A-1 ' are three different ids.
    r, _ = _run(tmp_path, [_row(action_id="A-1"), _row(action_id="a-1"), _row(action_id="A-1 ")])
    assert r.status == "succeeded" and r.source_row_count == 3


# --- structure ------------------------------------------------------------------------------


def test_duplicate_action_id_rejects_both_rows(tmp_path):
    r, _ = _run(tmp_path, [_row(), _row(action_name="again"), _row(action_id="A-2")])
    assert r.exit_code == 1 and r.invalid_row_count == 2 and r.valid_row_count == 1
    db = tmp_path / "t.duckdb"
    assert sql_rows(db, "SELECT count(*) FROM raw_actions") == [(0,)]
    assert sql_rows(db, "SELECT count(*) FROM stg_actions") == [(0,)]
    f = _findings(db, "DQ-03")
    assert len(f) == 1 and "alice" not in f[0][3] and "again" not in f[0][3]


def test_empty_file_exit2_no_db(tmp_path):
    p = _raw(tmp_path / "e.csv", b"")
    r = ingest.run_ingest(p, REF, tmp_path / "t.duckdb")
    assert r.exit_code == 2 and not (tmp_path / "t.duckdb").exists()


def test_bom_only_file_exit2(tmp_path):
    p = _raw(tmp_path / "e.csv", b"\xef\xbb\xbf")
    assert ingest.run_ingest(p, REF, tmp_path / "t.duckdb").exit_code == 2


def test_header_only_exit2_no_db(tmp_path):
    p = _raw(tmp_path / "h.csv", ",".join(HEADER) + "\n")
    r = ingest.run_ingest(p, REF, tmp_path / "t.duckdb")
    assert r.exit_code == 2 and not (tmp_path / "t.duckdb").exists()


def test_reordered_columns_bound_by_name(tmp_path):
    hdr = ["status", "owner", "due_date", "action_name", "project_name", "action_id"]
    rows = [[d["status"], d["owner"], d["due_date"], d["action_name"], d["project_name"], d["action_id"]]
            for d in [dict(zip(HEADER, GOOD, strict=True))]]
    r, _ = _run(tmp_path, rows, header=hdr)
    assert r.status == "succeeded"
    assert sql_rows(tmp_path / "t.duckdb", "SELECT action_id, owner, status FROM raw_actions") == [
        ("A-1", "alice", "todo")]


def test_extra_column_warning_not_loaded(tmp_path):
    r, _ = _run(tmp_path, [GOOD + ["secret"]], header=HEADER + ["note"])
    assert r.status == "succeeded"
    db = tmp_path / "t.duckdb"
    assert [(f[0], f[1], f[2]) for f in _findings(db)] == [("DQ-01", "note", "warning")]
    assert "secret" not in repr(sql_rows(db, "SELECT * FROM raw_actions"))


def test_missing_column_blocking_one_finding_each(tmp_path):
    hdr = [h for h in HEADER if h not in ("owner", "status")]
    rows = [[v for h, v in zip(HEADER, GOOD, strict=True) if h in hdr]]
    r, _ = _run(tmp_path, rows, header=hdr)
    assert r.exit_code == 1
    db = tmp_path / "t.duckdb"
    assert sorted(f[1] for f in _findings(db, "DQ-01")) == ["owner", "status"]
    assert sql_rows(db, "SELECT count(*) FROM raw_actions") == [(0,)]
    assert sql_rows(db, "SELECT status, valid_row_count FROM ingestion_runs") == [("failed", None)]


def test_header_case_sensitive(tmp_path):
    hdr = ["Action_ID"] + HEADER[1:]
    r, _ = _run(tmp_path, [GOOD], header=hdr)
    assert r.exit_code == 1


def test_duplicate_header_column_blocking(tmp_path):
    r, _ = _run(tmp_path, [GOOD + ["bob"]], header=HEADER + ["owner"])
    assert r.exit_code == 1
    f = _findings(tmp_path / "t.duckdb", "DQ-01")
    assert [(x[1], x[2]) for x in f] == [("owner", "blocking")]


def test_short_row_blocking_not_dropped(tmp_path):
    r, _ = _run(tmp_path, [GOOD[:4]])
    assert r.exit_code == 1 and r.invalid_row_count == 1
    assert {f[0] for f in _findings(tmp_path / "t.duckdb")} >= {"DQ-07", "DQ-08"}


def test_blank_line_in_data_is_reported_not_dropped(tmp_path):
    p = _raw(tmp_path / "b.csv", ",".join(HEADER) + "\n" + ",".join(GOOD) + "\n\n")
    r = ingest.run_ingest(p, REF, tmp_path / "t.duckdb")
    assert r.source_row_count == 2 and r.exit_code == 1


def test_overlong_row_extra_fields_flagged(tmp_path):
    # A data row with MORE fields than the header is a malformed/shifted row (typically an unquoted
    # comma). It must not be loaded silently with the surplus dropped.
    r, _ = _run(tmp_path, [GOOD + ["spill"]])
    assert r.exit_code == 1


def test_long_field_values(tmp_path):
    big = "ก" * 100_000
    r, _ = _run(tmp_path, [_row(action_name=big, owner="o" * 50_000)])
    assert r.status == "succeeded"
    assert sql_rows(tmp_path / "t.duckdb", "SELECT length(action_name) FROM raw_actions") == [(100_000,)]


def test_field_over_csv_limit_clean_exit(tmp_path):
    # Python's csv module caps a field at 131072 chars: clean exit 2, nothing written.
    r, _ = _run(tmp_path, [_row(action_name="x" * 200_000)])
    assert r.exit_code == 2 and not (tmp_path / "t.duckdb").exists()


# --- due_date -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "due",
    ["2026-9-1", "01/10/2026", "2026/10/01", "2026-13-45", "2026-02-30", "", "NULL", "null",
     "2026-09-01 10:00:00", "2026-09-01T10:00:00", " 2026-09-01", "2026-09-01 ", "2026-09-01Z",
     "๒๐๒๖-๐๙-๐๑", "0000-00-00", "2026-09-1", "20260901"],
)
def test_bad_due_dates_blocking(tmp_path, due):
    r, _ = _run(tmp_path, [_row(due_date=due)])
    assert r.exit_code == 1
    db = tmp_path / "t.duckdb"
    assert [f[0] for f in _findings(db, "DQ-07")] == ["DQ-07"]
    assert sql_rows(db, "SELECT count(*) FROM raw_actions") == [(0,)]


@pytest.mark.parametrize("due", ["2026-02-28", "2028-02-29", "2026-12-31", "1999-01-01"])
def test_good_due_dates(tmp_path, due):
    r, _ = _run(tmp_path, [_row(due_date=due)])
    assert r.status == "succeeded"


def test_leap_day_non_leap_year_rejected(tmp_path):
    assert _run(tmp_path, [_row(due_date="2027-02-29")])[0].exit_code == 1


# --- idempotency / run semantics ------------------------------------------------------------


def test_same_file_twice_noop_same_run_id(tmp_path):
    p = write_csv(tmp_path / "a.csv", [GOOD])
    db = tmp_path / "t.duckdb"
    a = ingest.run_ingest(p, REF, db)
    b = ingest.run_ingest(p, REF, db)
    assert (b.status, b.exit_code, b.run_id) == ("noop", 0, a.run_id)
    assert sql_rows(db, "SELECT count(*) FROM ingestion_runs") == [(1,)]
    assert sql_rows(db, "SELECT count(*) FROM raw_actions") == [(1,)]


def test_same_content_renamed_file_noop(tmp_path):
    a = write_csv(tmp_path / "a.csv", [GOOD])
    b = write_csv(tmp_path / "b.csv", [GOOD])
    db = tmp_path / "t.duckdb"
    ra = ingest.run_ingest(a, REF, db)
    assert ingest.run_ingest(b, REF, db).run_id == ra.run_id


def test_same_content_new_reference_date_new_run(tmp_path):
    p = write_csv(tmp_path / "a.csv", [_row(due_date="2026-09-10")])
    db = tmp_path / "t.duckdb"
    a = ingest.run_ingest(p, date(2026, 9, 5), db)
    b = ingest.run_ingest(p, date(2026, 9, 20), db)
    assert b.status == "succeeded" and b.run_id != a.run_id
    assert metrics.portfolio(None, db)["overdue_actions"] == 1  # latest run drives
    assert sql_rows(db, "SELECT count(*) FROM ingestion_runs WHERE status='succeeded'") == [(2,)]
    # old run's rows remain with their own flags
    assert sql_rows(db, "SELECT run_id, is_overdue FROM stg_actions ORDER BY run_id") == [
        (a.run_id, False), (b.run_id, True)]


def test_failed_run_does_not_replace_latest_succeeded(tmp_path):
    db = tmp_path / "t.duckdb"
    good = write_csv(tmp_path / "g.csv", [GOOD, _row(action_id="A-2", status="done")])
    ok = ingest.run_ingest(good, REF, db)
    bad = write_csv(tmp_path / "b.csv", [_row(due_date="garbage")])
    assert ingest.run_ingest(bad, REF, db).exit_code == 1
    assert ingest.run_ingest(tmp_path / "missing.csv", REF, db).exit_code == 2
    assert metrics.get_run_info(db)["run_id"] == ok.run_id
    assert metrics.portfolio(None, db)["total_actions"] == 2
    dq = metrics.data_quality_summary(db)
    assert dq is not None


def test_rejected_file_can_be_rerun_after_fix_same_hash_not_noop(tmp_path):
    db = tmp_path / "t.duckdb"
    bad = write_csv(tmp_path / "b.csv", [_row(due_date="x")])
    r1 = ingest.run_ingest(bad, REF, db)
    r2 = ingest.run_ingest(bad, REF, db)  # failed runs never short-circuit
    assert r1.exit_code == r2.exit_code == 1 and r1.run_id != r2.run_id


def test_only_failed_runs_gives_empty_metrics(tmp_path):
    db = tmp_path / "t.duckdb"
    ingest.run_ingest(write_csv(tmp_path / "b.csv", [_row(due_date="x")]), REF, db)
    assert metrics.portfolio(None, db)["total_actions"] == 0
    assert metrics.get_run_info(db) is None


# --- CLI / arguments ------------------------------------------------------------------------


def _cli(*args):
    return subprocess.run([sys.executable, "-m", "src.ingest", *args], capture_output=True,
                          text=True, cwd=settings.ROOT_DIR, check=False)


@pytest.mark.parametrize(
    "bad", ["2026-02-30", "2026-9-1", "01/10/2026", "", "today", "2026-10-02T00:00", "20261002",
            " 2026-10-02", "2026-10-02 ", "0000-00-00", "๒๐๒๖-๐๑-๐๑", "2026-13-01"],
)
def test_invalid_reference_date_exit2_no_db(tmp_path, bad):
    db = tmp_path / "t.duckdb"
    p = _cli("--input", str(GOLDEN_CSV), "--reference-date", bad, "--db", str(db))
    assert p.returncode == 2 and not db.exists()


def test_missing_reference_date_exit2(tmp_path):
    assert _cli("--input", str(GOLDEN_CSV), "--db", str(tmp_path / "t.duckdb")).returncode == 2


def test_nonexistent_input_exit2_no_db(tmp_path):
    db = tmp_path / "t.duckdb"
    p = _cli("--input", str(tmp_path / "nope.csv"), "--reference-date", "2026-09-15", "--db", str(db))
    assert p.returncode == 2 and not db.exists()


def test_directory_input_exit2_no_db(tmp_path):
    db = tmp_path / "t.duckdb"
    p = _cli("--input", str(tmp_path), "--reference-date", "2026-09-15", "--db", str(db))
    assert p.returncode == 2 and not db.exists()


def test_cli_does_not_touch_default_db_when_db_given(tmp_path):
    before = settings.DB_PATH.stat().st_mtime if settings.DB_PATH.exists() else None
    p = _cli("--input", str(GOLDEN_CSV), "--reference-date", "2026-09-15",
             "--db", str(tmp_path / "t.duckdb"))
    assert p.returncode == 0
    after = settings.DB_PATH.stat().st_mtime if settings.DB_PATH.exists() else None
    assert before == after


def test_lock_held_by_other_process_exit3_no_corruption(tmp_path):
    db = tmp_path / "t.duckdb"
    ingest.run_ingest(GOLDEN_CSV, REF, db)
    holder = subprocess.Popen(
        [sys.executable, "-c",
         "import duckdb,sys,time;c=duckdb.connect(sys.argv[1]);print('ready',flush=True);time.sleep(30)",
         str(db)], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "ready"
        p = write_csv(tmp_path / "n.csv", [GOOD])
        r = ingest.run_ingest(p, REF, db)
        assert r.exit_code == 3 and r.status == "error"
    finally:
        holder.kill()
        holder.wait()
    assert sql_rows(db, "SELECT count(*) FROM ingestion_runs") == [(1,)]
    assert ingest.run_ingest(p, REF, db).status == "succeeded"  # recovers after lock release


def test_readonly_reader_open_blocks_writer_exit3(tmp_path):
    db = tmp_path / "t.duckdb"
    ingest.run_ingest(GOLDEN_CSV, REF, db)
    holder = subprocess.Popen(
        [sys.executable, "-c",
         "import duckdb,sys,time;c=duckdb.connect(sys.argv[1],read_only=True);print('ready',flush=True);time.sleep(30)",
         str(db)], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "ready"
        r = ingest.run_ingest(write_csv(tmp_path / "n.csv", [GOOD]), REF, db)
        assert r.exit_code == 3
    finally:
        holder.kill()
        holder.wait()
    assert sql_rows(db, "SELECT status FROM ingestion_runs") == [("succeeded",)]


# --- metrics parameterisation ---------------------------------------------------------------

_NASTY = ["O'Brien", "100%", "a_b", "'; DROP TABLE stg_actions; --", '"quoted"', "x' OR '1'='1",
          "%", "_", "\\", "ก'ข", "", "NULL", "All Projects "]


@pytest.mark.parametrize("name", _NASTY)
def test_metrics_nasty_project_names_safe(golden_db, name):
    assert metrics.portfolio(name, golden_db)["total_actions"] == 0
    assert metrics.by_project(name, golden_db) == []
    assert metrics.overdue_detail(name, golden_db) == []
    assert metrics.by_owner(name, golden_db) == []
    assert sql_rows(golden_db, "SELECT count(*) FROM stg_actions")[0][0] == 12


def test_metrics_nasty_project_that_exists_matches_exactly(tmp_path):
    db = tmp_path / "t.duckdb"
    rows = [_row(action_id="1", project_name="O'Brien 100%"), _row(action_id="2", project_name="O'Brien 1000")]
    ingest.run_ingest(write_csv(tmp_path / "n.csv", rows), REF, db)
    assert metrics.portfolio("O'Brien 100%", db)["total_actions"] == 1
    assert metrics.portfolio("O'Brien 1%", db)["total_actions"] == 0


# --- volume ---------------------------------------------------------------------------------


def test_140k_rows_time_and_memory(tmp_path):
    n = 140_000
    p = tmp_path / "big.csv"
    st = ["todo", "in_progress", "done"]
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        for i in range(n):
            w.writerow([f"ACT-{i:07d}", f"Project {i % 50}", f"Action เรื่อง, {i}", f"owner{i % 200}",
                        f"2026-{1 + i % 12:02d}-{1 + i % 28:02d}", st[i % 3]])
    db = tmp_path / "t.duckdb"
    t0 = time.perf_counter()
    r = ingest.run_ingest(p, REF, db)
    dt = time.perf_counter() - t0
    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f"\n140k ingest: {dt:.1f}s, peak RSS {peak_mb:.0f} MB")
    assert r.status == "succeeded" and r.source_row_count == n
    assert dt < 60 and peak_mb < 2000
    assert metrics.portfolio(None, db)["total_actions"] == n
    assert sql_rows(db, "SELECT count(*) FROM stg_actions") == [(n,)]


@pytest.mark.parametrize("blank", ["\t", "\n", " \t ", "\u00a0", "\u3000", "\u200b", "\ufeff"])
def test_any_unicode_whitespace_counts_as_empty(tmp_path, blank):
    # DATA_QUALITY: "empty / whitespace-only" is blocking, not only ASCII spaces (SQL trim()
    # strips spaces only, which let a TAB / NBSP-only owner through).
    r, _ = _run(tmp_path, [_row(owner=blank)])
    assert r.exit_code == 1 and [f[0] for f in _findings(tmp_path / "t.duckdb")] == ["DQ-06"]
