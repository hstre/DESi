"""v37.2 - evidence gap detection and conclusion governance.

A task has an evidence gap when required evidence is not available.
DESi surfaces the gap and refuses to draw a supported conclusion
without it: the conclusion is 'insufficient_evidence', never an
unsupported 'supported'.
"""
from __future__ import annotations

from .audit_assertion_mapping import AuditTask, audit_tasks

CONCLUSION_SUPPORTED = "supported"
CONCLUSION_INSUFFICIENT = "insufficient_evidence"


def missing_evidence(task: AuditTask) -> tuple[str, ...]:
    have = set(task.evidence_available)
    return tuple(r for r in task.evidence_required if r not in have)


def has_gap(task: AuditTask) -> bool:
    return bool(missing_evidence(task))


def conclusion(task: AuditTask) -> str:
    if has_gap(task):
        return CONCLUSION_INSUFFICIENT
    return CONCLUSION_SUPPORTED


def gap_tasks() -> tuple[AuditTask, ...]:
    return tuple(t for t in audit_tasks() if has_gap(t))


def evidence_gap_visibility() -> float:
    gaps = gap_tasks()
    if not gaps:
        return 1.0
    ok = sum(1 for t in gaps if missing_evidence(t))
    return round(ok / len(gaps), 6)


def unsupported_conclusion_resistance() -> float:
    """Of the tasks with an evidence gap, the fraction that are NOT
    given a supported conclusion."""
    gaps = gap_tasks()
    if not gaps:
        return 1.0
    ok = sum(
        1 for t in gaps if conclusion(t) == CONCLUSION_INSUFFICIENT
    )
    return round(ok / len(gaps), 6)


__all__ = [
    "CONCLUSION_INSUFFICIENT",
    "CONCLUSION_SUPPORTED",
    "conclusion",
    "evidence_gap_visibility",
    "gap_tasks",
    "has_gap",
    "missing_evidence",
    "unsupported_conclusion_resistance",
]
