"""Independent pure-Python DQ evaluator (T-V15): DATA_QUALITY rules re-implemented without SQL.

Reads the CSV text directly (csv module) and returns the findings the pipeline must produce:
a sorted list of (check_name, record_key, severity) plus (source, valid, invalid) row counts.
Deliberately does NOT import src.validation (an independent second implementation).
"""

from __future__ import annotations

import csv
import re
import unicodedata
from datetime import datetime

REQUIRED = ["action_id", "project_name", "action_name", "owner", "due_date", "status"]
STATUSES = {"todo", "in_progress", "done"}  # DATA_MODEL_SPEC enum action_status
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _blank(v: str | None) -> bool:
    """Empty / whitespace-only incl. Unicode separators, ZWSP and BOM (DATA_QUALITY)."""
    return v is None or all(
        c.isspace() or unicodedata.category(c).startswith("Z") or c in "\u200b\ufeff" for c in v
    )


def _real_iso_date(v: str | None) -> bool:
    if _blank(v) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", v):
        return False
    try:
        datetime.strptime(v, "%Y-%m-%d")  # noqa: DTZ007 - date-only validity check
    except ValueError:
        return False
    return True


def evaluate(path) -> tuple[list[tuple], tuple[int, int | None, int | None]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        recs = list(reader)
    findings: list[tuple] = []
    missing = [c for c in REQUIRED if c not in header]
    extra = [c for c in dict.fromkeys(header) if c not in REQUIRED]
    dups = [c for c in dict.fromkeys(header) if header.count(c) > 1]
    findings += [("DQ-01", c, "blocking") for c in missing]
    findings += [("DQ-01", c, "warning") for c in extra]
    findings += [("DQ-01", c, "blocking") for c in dups]
    if missing or dups:
        return sorted(findings), (len(recs), None, None)

    idx = {c: header.index(c) for c in REQUIRED}
    rows = []
    for n, rec in enumerate(recs, start=1):
        vals = {c: (rec[i] if i < len(rec) else None) for c, i in idx.items()}
        # the CSV reader hands '' for empty fields; the pipeline treats '' as NULL: both blank
        rows.append((n, vals, len(rec)))

    bad: set[int] = set()
    rules = [("DQ-02", "action_id"), ("DQ-04", "project_name"), ("DQ-05", "action_name"),
             ("DQ-06", "owner")]
    for check, col in rules:
        for n, v, _ in rows:
            if _blank(v[col]):
                bad.add(n)
                findings.append((check, str(n), "blocking"))
    for n, v, _ in rows:
        if not _real_iso_date(v["due_date"]):
            bad.add(n)
            findings.append(("DQ-07", str(n), "blocking"))
    for n, v, _ in rows:
        if _blank(v["status"]):
            bad.add(n)
            findings.append(("DQ-08", str(n), "blocking"))
    for n, _, fc in rows:
        if fc != len(header):
            bad.add(n)
            findings.append(("DQ-11", str(n), "blocking"))
    for n, v, _ in rows:
        if _CTRL.search("".join(x or "" for x in v.values())):
            findings.append(("DQ-12", str(n), "warning"))
    by_id: dict[str, list[int]] = {}
    for n, v, _ in rows:
        if not _blank(v["action_id"]):
            by_id.setdefault(v["action_id"], []).append(n)
    for key, ns in by_id.items():
        if len(ns) > 1:
            bad.update(ns)
            findings.append(("DQ-03", key, "blocking"))
    for s in sorted({v["status"] for _, v, _ in rows if not _blank(v["status"])} - STATUSES):
        findings.append(("DQ-09", s, "investigation"))
    return sorted(findings), (len(recs), len(recs) - len(bad), len(bad))
