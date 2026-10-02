"""PL-01 csv_ingest (PIPELINE_SPEC.md): CSV -> validate -> raw_actions -> stg_actions.

CLI:  python -m src.ingest --input <csv> --reference-date YYYY-MM-DD [--db PATH]
Exit codes: 0 success or idempotent no-op; 1 file rejected (blocking finding / reconcile
failure); 2 bad arguments or unreadable file (no DB write); 3 database / system error.

The reference date is always supplied by the caller and stored in ingestion_runs; there is no
default and the system clock is never used for metric logic (CON-06, F1). The clock is read only
for audit timestamps (started_at / completed_at / loaded_at / created_at).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb

from . import settings, validation
from .db import connect_writer, load_sql

EXIT_OK, EXIT_REJECTED, EXIT_BAD_INPUT, EXIT_SYSTEM = 0, 1, 2, 3


@dataclass
class IngestResult:
    exit_code: int
    status: str  # succeeded | failed | noop | error
    run_id: int | None = None
    message: str = ""
    source_row_count: int | None = None
    valid_row_count: int | None = None
    invalid_row_count: int | None = None
    findings_by_severity: dict[str, int] = field(default_factory=dict)


def _now() -> datetime:
    # Audit timestamp only (UTC, naive; timezone convention is an open DDD question).
    return datetime.now(UTC).replace(tzinfo=None)


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# --- pipeline stages (module-level so tests can inject faults) -----------------------------


def st05_load_raw(con, run_id: int, loaded_at: datetime) -> None:
    con.execute(load_sql("10_staging/load_raw.sql"), {"run_id": run_id, "loaded_at": loaded_at})


def st06_build_stg(con, run_id: int) -> None:
    con.execute(load_sql("10_staging/stg_actions.sql"), {"run_id": run_id})


def st07_reconcile(con, run_id: int) -> list[str]:
    """DQ-10 plus the Q-BY-PROJECT-sums-to-Q-PORTFOLIO invariant. Returns problem messages."""
    problems: list[str] = []
    if con.execute(validation.quality_sql("DQ-10"), {"run_id": run_id}).fetchall():
        problems.append("row counts do not reconcile (source/valid/raw/stg)")
    params = {"run_id": run_id, "project_name": None}
    portfolio = con.execute(load_sql("20_metrics/q_portfolio.sql"), params).fetchone()
    by_project = con.execute(load_sql("20_metrics/q_by_project.sql"), params).fetchall()
    # portfolio columns 0..4 = total, completed, open, overdue, open_not_overdue;
    # by-project columns 1..5 = same five (completion_rate / MET-07 are not additive).
    for i in range(5):
        if (portfolio[i] or 0) != sum(r[i + 1] for r in by_project):
            problems.append("sum of Q-BY-PROJECT differs from Q-PORTFOLIO")
            break
    return problems


# --- helpers ---------------------------------------------------------------------------------


def _write_findings(con, run_id: int, findings, created_at: datetime) -> None:
    for f in findings:
        con.execute(
            "INSERT INTO data_quality_results (run_id, check_name, record_key, severity_class,"
            " message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [run_id, f.check_name, f.record_key, f.severity, f.message, created_at],
        )


def _severity_counts(con, run_id: int) -> dict[str, int]:
    rows = con.execute(
        "SELECT severity_class, count(*) FROM data_quality_results WHERE run_id = ? "
        "GROUP BY 1 ORDER BY 1",
        [run_id],
    ).fetchall()
    return {sev: n for sev, n in rows}


def _finalize(con, run_id: int, status: str) -> None:
    con.execute(
        "UPDATE ingestion_runs SET status = ?, completed_at = ? WHERE run_id = ?",
        [status, _now(), run_id],
    )


def _mark_failed(con, run_id: int) -> None:
    try:
        _finalize(con, run_id, "failed")
    except duckdb.Error:
        pass


# --- main entry ------------------------------------------------------------------------------


def run_ingest(
    input_path: str | Path, reference_date: date, db_path: str | Path | None = None
) -> IngestResult:
    """Run PL-01 once. Never raises for expected failures; see exit codes in the module doc."""
    path = Path(input_path)

    # ST-02 (file part): read + hash before anything is written.
    try:
        size = path.stat().st_size
        if size > settings.MAX_INPUT_BYTES:
            return IngestResult(
                EXIT_BAD_INPUT, "error",
                message=f"input is {size} bytes; exceeds INGEST_MAX_BYTES={settings.MAX_INPUT_BYTES}",
            )
        source_hash = _file_hash(path)
        header, rows = validation.read_csv(path)
    except (OSError, UnicodeDecodeError, csv.Error, ValueError) as exc:
        return IngestResult(EXIT_BAD_INPUT, "error", message=f"cannot read input: {exc}")
    if not rows:
        # Header-only file: behaviour undecided in DDD (TESTING_STRATEGY OQ2); refuse safely.
        return IngestResult(EXIT_BAD_INPUT, "error", message="input has a header but no data rows")

    try:
        con = connect_writer(db_path)
    except duckdb.Error as exc:
        return IngestResult(EXIT_SYSTEM, "error", message=f"cannot open database: {exc}")

    run_id: int | None = None
    try:
        # ST-01 init_schema
        con.execute(load_sql("00_schema/create_tables.sql"))

        # ST-02 idempotency: same file + same reference date already succeeded -> no-op.
        prior = con.execute(
            "SELECT max(run_id) FROM ingestion_runs WHERE status = 'succeeded' "
            "AND source_hash = ? AND reference_date = ?",
            [source_hash, reference_date],
        ).fetchone()[0]
        if prior is not None:
            return IngestResult(
                EXIT_OK, "noop", run_id=prior,
                message="same file and reference date already loaded; nothing written",
            )

        # ST-03 register_run
        run_id = con.execute(
            "INSERT INTO ingestion_runs (source_file, source_hash, reference_date, started_at,"
            " status) VALUES (?, ?, ?, ?, 'running') RETURNING run_id",
            [path.name, source_hash, reference_date, _now()],
        ).fetchone()[0]

        # ST-04 validate (in memory); every finding is persisted.
        result = validation.validate(con, header, rows)
        _write_findings(con, run_id, result.findings, _now())
        con.execute(
            "UPDATE ingestion_runs SET source_row_count = ?, valid_row_count = ?, "
            "invalid_row_count = ? WHERE run_id = ?",
            [result.source_row_count, result.valid_row_count, result.invalid_row_count, run_id],
        )
        out = IngestResult(
            EXIT_OK, "succeeded", run_id=run_id,
            source_row_count=result.source_row_count,
            valid_row_count=result.valid_row_count,
            invalid_row_count=result.invalid_row_count,
        )
        if result.has_blocking:
            _finalize(con, run_id, "failed")
            out.exit_code, out.status = EXIT_REJECTED, "failed"
            out.message = "file rejected: blocking data-quality findings (nothing loaded)"
            out.findings_by_severity = _severity_counts(con, run_id)
            return out

        # ST-05..ST-07 (+ success finalize) in one transaction.
        try:
            con.begin()
            st05_load_raw(con, run_id, _now())
            st06_build_stg(con, run_id)
            problems = st07_reconcile(con, run_id)
            if problems:
                con.rollback()
                _mark_failed(con, run_id)
                _write_findings(
                    con, run_id,
                    [validation.Finding("DQ-10", str(run_id), validation.BLOCKING, p)
                     for p in problems],
                    _now(),
                )
                out.exit_code, out.status = EXIT_REJECTED, "failed"
                out.message = "reconciliation failed (DQ-10); transaction rolled back"
            else:
                _finalize(con, run_id, "succeeded")
                con.execute(
                    "INSERT OR REPLACE INTO app_config VALUES ('reference_date', ?, ?)",
                    [reference_date.isoformat(), _now()],
                )
                con.commit()
                out.message = "ingest succeeded"
        except Exception as exc:  # noqa: BLE001 - any failure inside the load transaction
            try:
                con.rollback()
            except duckdb.Error:
                pass
            _mark_failed(con, run_id)
            _write_findings(
                con, run_id,
                [validation.Finding(
                    "DQ-10", str(run_id), validation.BLOCKING,
                    f"pipeline error during load ({type(exc).__name__}); rolled back",
                )],
                _now(),
            )
            out.exit_code, out.status = EXIT_SYSTEM, "failed"
            out.message = f"pipeline error: {type(exc).__name__}; transaction rolled back"
        out.findings_by_severity = _severity_counts(con, run_id)
        return out
    except duckdb.Error as exc:
        if run_id is not None:
            _mark_failed(con, run_id)
        return IngestResult(
            EXIT_SYSTEM, "error", run_id=run_id, message=f"database error: {type(exc).__name__}"
        )
    finally:
        con.close()


def _parse_args(argv):
    p = argparse.ArgumentParser(prog="python -m src.ingest", description="Load a weekly CSV.")
    p.add_argument("--input", required=True, help="path to the weekly action CSV (UTF-8)")
    p.add_argument(
        "--reference-date", required=True,
        help="YYYY-MM-DD used for overdue calculation (no default; never today's date)",
    )
    p.add_argument("--db", default=str(settings.DB_PATH), help="DuckDB file (default: %(default)s)")
    args = p.parse_args(argv)  # argparse exits with code 2 on usage errors
    try:
        ref = date.fromisoformat(args.reference_date)
        if ref.isoformat() != args.reference_date:
            raise ValueError
    except ValueError:
        p.error("--reference-date must be a real date in YYYY-MM-DD format")
    return args, ref


def main(argv: list[str] | None = None) -> int:
    args, ref = _parse_args(argv)
    r = run_ingest(args.input, ref, args.db)
    stream = sys.stdout if r.exit_code in (EXIT_OK, EXIT_REJECTED) else sys.stderr
    lines = [f"status: {r.status}", f"message: {r.message}"]
    if r.run_id is not None:
        lines.insert(0, f"run_id: {r.run_id}")
    if r.source_row_count is not None:
        lines.append(
            f"rows: source={r.source_row_count} valid={r.valid_row_count} "
            f"invalid={r.invalid_row_count}"
        )
    if r.findings_by_severity:
        lines.append(
            "findings: " + ", ".join(f"{k}={v}" for k, v in r.findings_by_severity.items())
        )
    lines.append(f"exit_code: {r.exit_code}")
    print("\n".join(lines), file=stream)
    return r.exit_code


if __name__ == "__main__":
    sys.exit(main())
