"""Append-only audit for the wrong-slice ablation.

Pre-registration §5 requires that insufficiently matched candidate slices are
**discarded and audited** — never silently dropped and never patched to pass.
This module is the audit sink: every admit/reject decision is appended as one
JSON line with the full matcher report, slice hashes, and caller context, so the
set of admitted slices (and everything rejected) is reconstructable later.

Stdlib only. The sink is an append-only JSONL file; pass a path or a file-like
object. Nothing here runs the experiment or calls a model.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

from slice_matcher import MatchReport, Slice, content_hash, match


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def audit_entry(
    correct: Slice,
    candidate: Slice,
    report: MatchReport,
    *,
    context: dict | None = None,
) -> dict:
    """Build one audit record for a match decision (admitted or rejected)."""
    return {
        "ts": _now(),
        "decision": "admitted" if report.ok else "rejected",
        "correct_hash": content_hash(correct),
        "candidate_hash": content_hash(candidate),
        "candidate_pass_id": candidate.pass_id,
        "failed_criteria": [c.name for c in report.failed()],
        "report": [asdict(c) for c in report.criteria],
        "context": context or {},
    }


def write_entry(sink: str | os.PathLike | IO[str], entry: dict) -> None:
    """Append one entry as a JSON line to a path or open file handle."""
    line = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    if hasattr(sink, "write"):
        sink.write(line + "\n")  # type: ignore[union-attr]
    else:
        path = Path(sink)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def admit_or_audit(
    correct: Slice,
    candidate: Slice,
    sink: str | os.PathLike | IO[str],
    *,
    context: dict | None = None,
    audit_admitted: bool = True,
    **match_kwargs,
) -> tuple[bool, MatchReport]:
    """Match ``candidate`` against ``correct``, audit the decision, return it.

    Returns ``(admitted, report)``. Rejected candidates are ALWAYS audited;
    admitted ones are audited too when ``audit_admitted`` (default) so the full
    decision trail is recorded. The caller discards the candidate iff
    ``admitted`` is False — this function never mutates a slice to make it pass.
    """
    report = match(correct, candidate, **match_kwargs)
    if (not report.ok) or audit_admitted:
        write_entry(sink, audit_entry(correct, candidate, report, context=context))
    return report.ok, report
