"""v37.2 - audit procedure generator.

For each evidence gap, proposes a deterministic, traceable audit
procedure to obtain the missing evidence. Procedures are suggestions
to close a gap - they never assert a conclusion.
"""
from __future__ import annotations

from .audit_assertion_mapping import AuditTask
from .evidence_gap_detection import missing_evidence

_PROCEDURE_FOR: dict[str, str] = {
    "confirmation": "send external confirmation request",
    "appraisal": "obtain independent appraisal",
    "market_data": "corroborate with independent market data",
    "cutoff_test": "perform cut-off testing around period end",
    "title_deed": "inspect title/ownership documentation",
    "disclosure_review": "review disclosure against the standard",
}


def procedures_for(task: AuditTask) -> tuple[tuple[str, str], ...]:
    return tuple(
        (ev, _PROCEDURE_FOR.get(ev, "obtain corroborating evidence"))
        for ev in missing_evidence(task)
    )


def all_procedures() -> dict[str, list[list[str]]]:
    from .audit_assertion_mapping import audit_tasks
    out: dict[str, list[list[str]]] = {}
    for t in audit_tasks():
        procs = procedures_for(t)
        if procs:
            out[t.task_id] = [list(p) for p in procs]
    return out


__all__ = ["all_procedures", "procedures_for"]
