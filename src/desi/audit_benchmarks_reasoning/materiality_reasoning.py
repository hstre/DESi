"""v37.2 - materiality reasoning.

A claim is material iff its amount meets or exceeds the materiality
threshold. The decision is fully traceable to the amount and the
threshold - no hidden judgement.
"""
from __future__ import annotations

from .audit_assertion_mapping import AuditTask, audit_tasks


def is_material(task: AuditTask) -> bool:
    return task.amount >= task.materiality_threshold


def materiality_trace(task: AuditTask) -> dict[str, object]:
    return {
        "task_id": task.task_id,
        "amount": task.amount,
        "threshold": task.materiality_threshold,
        "material": is_material(task),
    }


def materiality_traceability() -> float:
    """Every task yields a deterministic material/immaterial decision
    traceable to amount vs threshold."""
    tasks = audit_tasks()
    if not tasks:
        return 0.0
    ok = sum(
        1 for t in tasks
        if t.materiality_threshold > 0 and t.amount >= 0
    )
    return round(ok / len(tasks), 6)


__all__ = [
    "is_material",
    "materiality_trace",
    "materiality_traceability",
]
