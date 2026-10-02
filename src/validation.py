"""ST-04 validation: DQ-01..DQ-09 (DATA_QUALITY.md).

The normative assertions are the SQL blocks in sql/30_quality/quality_checks.sql; this module
loads the raw CSV text (all VARCHAR, nothing converted) into temp tables `input_rows` /
`input_columns` and runs those blocks. Nothing is dropped silently: every offending row yields a
finding. Messages never contain owner / action_name values (PDPA, AGENTS.md).
"""

from __future__ import annotations

import csv
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from . import settings
from .db import load_sql

BLOCKING = "blocking"
WARNING = "warning"
INVESTIGATION = "investigation"

# Row-level blocking rules: check name -> (source column, message).
_ROW_RULES = {
    "DQ-02": ("action_id", "action_id is empty"),
    "DQ-04": ("project_name", "project_name is empty"),
    "DQ-05": ("action_name", "action_name is empty"),
    "DQ-06": ("owner", "owner is empty"),
    "DQ-07": ("due_date", "due_date is empty or not a real ISO YYYY-MM-DD date"),
    "DQ-08": ("status", "status is empty"),
}

_INPUT_COLS = ("action_id", "project_name", "action_name", "owner", "due_date_raw", "status")


@dataclass(frozen=True)
class Finding:
    check_name: str
    record_key: str | None
    severity: str
    message: str


@dataclass
class ValidationResult:
    findings: list[Finding] = field(default_factory=list)
    source_row_count: int = 0
    valid_row_count: int | None = None
    invalid_row_count: int | None = None

    @property
    def has_blocking(self) -> bool:
        return any(f.severity == BLOCKING for f in self.findings)


def read_csv(path: str | Path) -> tuple[list[str], list[tuple]]:
    """Read the CSV as text. Returns (header, rows); each row = (source_row_number, 6 values).

    UTF-8 with optional BOM. Raises OSError / UnicodeDecodeError / csv.Error / ValueError when
    the file cannot be used at all (CLI exit 2, no DB write). The 8th element of each row is the
    number of fields the source record actually had (checked by DQ-11).
    """
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("file is empty (no header)") from None
        index = {name: i for i, name in enumerate(header)}
        rows: list[tuple] = []
        for n, rec in enumerate(reader, start=1):
            vals = []
            for col in settings.REQUIRED_COLUMNS:
                i = index.get(col)
                vals.append(rec[i] if i is not None and i < len(rec) else None)
            rows.append((n, *vals, len(rec)))
    return header, rows


def _load_blocks() -> dict[str, str]:
    """Split quality_checks.sql into {name: sql} using the '-- name:' markers."""
    blocks: dict[str, str] = {}
    name = None
    buf: list[str] = []
    for line in load_sql("30_quality/quality_checks.sql").splitlines():
        m = re.match(r"--\s*name:\s*(\S+)", line)
        if m:
            if name:
                blocks[name] = "\n".join(buf).strip().rstrip(";")
            name, buf = m.group(1), []
        elif name:
            buf.append(line)
    if name:
        blocks[name] = "\n".join(buf).strip().rstrip(";")
    return blocks


def quality_sql(name: str) -> str:
    return _load_blocks()[name]


def _load_input_tables(con: duckdb.DuckDBPyConnection, header: list[str], rows: list[tuple]):
    con.execute("DROP TABLE IF EXISTS input_columns")
    con.execute("DROP TABLE IF EXISTS input_rows")
    con.execute("CREATE TEMP TABLE input_columns (column_name VARCHAR)")
    con.execute(
        "CREATE TEMP TABLE input_rows (source_row_number INTEGER, action_id VARCHAR, "
        "project_name VARCHAR, action_name VARCHAR, owner VARCHAR, due_date_raw VARCHAR, "
        "status VARCHAR, field_count INTEGER)"
    )
    if header:
        con.executemany("INSERT INTO input_columns VALUES (?)", [(h,) for h in header])
    if not rows:
        return
    # Bulk-load through a temp CSV: binding ~100k Python parameters is very slow in DuckDB.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_csv = Path(tmp) / "input_rows.csv"
        with open(tmp_csv, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh, lineterminator="\n").writerows(rows)
        # Explicit dialect (auto_detect=false): the sniffer fails on fields containing newlines.
        con.execute(
            "INSERT INTO input_rows SELECT CAST(n AS INTEGER), a, p, an, o, d, s,"
            " CAST(fc AS INTEGER) FROM read_csv(?, header = false, all_varchar = true,"
            " auto_detect = false, delim = ',', quote = '\"', escape = '\"', new_line = '\\n',"
            " columns = {'n': 'VARCHAR', 'a': 'VARCHAR', 'p': 'VARCHAR', 'an': 'VARCHAR',"
            " 'o': 'VARCHAR', 'd': 'VARCHAR', 's': 'VARCHAR', 'fc': 'VARCHAR'}, nullstr = '')",
            [str(tmp_csv)],
        )


def validate(
    con: duckdb.DuckDBPyConnection, header: list[str], rows: list[tuple]
) -> ValidationResult:
    """Run DQ-01..DQ-09 over the in-memory input and return all findings and row counts."""
    blocks = _load_blocks()
    _load_input_tables(con, header, rows)
    res = ValidationResult(source_row_count=len(rows))

    # DQ-01: schema. Missing column = blocking and row-level checks are impossible (counts NULL).
    missing = [r[0] for r in con.execute(blocks["DQ-01-missing"]).fetchall()]
    for col in missing:
        res.findings.append(
            Finding("DQ-01", col, BLOCKING, f"required column '{col}' is missing from the header")
        )
    for (col,) in con.execute(blocks["DQ-01-extra"]).fetchall():
        res.findings.append(
            Finding("DQ-01", col, WARNING, f"unexpected extra column '{col}' (not loaded)")
        )
    for (col,) in con.execute(blocks["DQ-01-duplicate"]).fetchall():
        res.findings.append(
            Finding("DQ-01", col, BLOCKING, f"column '{col}' appears more than once in the header")
        )
        missing.append(col)  # ambiguous binding: row-level checks are impossible
    if missing:
        return res

    invalid_rows: set[int] = set()

    for check, (_col, message) in _ROW_RULES.items():
        for (n,) in con.execute(blocks[check]).fetchall():
            invalid_rows.add(n)
            res.findings.append(
                Finding(check, str(n), BLOCKING, f"{message} at source row {n}")
            )

    for (n,) in con.execute(blocks["DQ-11"]).fetchall():
        invalid_rows.add(n)
        res.findings.append(
            Finding("DQ-11", str(n), BLOCKING,
                    f"record has a different number of fields than the header at source row {n}")
        )

    for (n,) in con.execute(blocks["DQ-12"]).fetchall():
        res.findings.append(
            Finding("DQ-12", str(n), WARNING,
                    f"control character (e.g. NUL) in a field at source row {n}; kept as-is")
        )

    for key, count, row_numbers in con.execute(blocks["DQ-03"]).fetchall():
        invalid_rows.update(row_numbers)
        shown = ", ".join(str(r) for r in row_numbers[:20])
        res.findings.append(
            Finding(
                "DQ-03",
                key,
                BLOCKING,
                f"action_id is duplicated {count} times (source rows {shown})",
            )
        )

    for (value,) in con.execute(
        blocks["DQ-09"], {"action_status_values": list(settings.ACTION_STATUS_VALUES)}
    ).fetchall():
        res.findings.append(
            Finding(
                "DQ-09",
                value,
                INVESTIGATION,
                "status value is not in enum action_status; kept as-is and counted as open",
            )
        )

    res.invalid_row_count = len(invalid_rows)
    res.valid_row_count = res.source_row_count - res.invalid_row_count
    return res
