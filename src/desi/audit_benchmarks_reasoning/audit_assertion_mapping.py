"""v37.2 - audit assertion mapping (network-free loader + mapper).

Loads the audit-reasoning tasks and maps each to a recognised audit
assertion. Mapping is intact iff every task's assertion is one of the
canonical assertion types and points at a claim id.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import content_hash

ASSERTION_TYPES: tuple[str, ...] = (
    "existence",
    "completeness",
    "valuation",
    "rights_and_obligations",
    "presentation",
)

_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "audit_reasoning_ref.json"
)


@dataclass(frozen=True)
class AuditTask:
    task_id: str
    assertion: str
    claim_id: str
    evidence_required: tuple[str, ...]
    evidence_available: tuple[str, ...]
    amount: float
    materiality_threshold: float


@lru_cache(maxsize=1)
def _payload() -> dict:
    return json.loads(_DATASET.read_text(encoding="utf-8"))


def dataset_hash() -> str:
    return content_hash(_payload())


def provenance() -> str:
    return _payload()["provenance"]


@lru_cache(maxsize=1)
def audit_tasks() -> tuple[AuditTask, ...]:
    return tuple(
        AuditTask(
            task_id=t["task_id"],
            assertion=t["assertion"],
            claim_id=t["claim_id"],
            evidence_required=tuple(t["evidence_required"]),
            evidence_available=tuple(t["evidence_available"]),
            amount=float(t["amount"]),
            materiality_threshold=float(t["materiality_threshold"]),
        )
        for t in _payload()["tasks"]
    )


def assertion_mapped(task: AuditTask) -> bool:
    return task.assertion in set(ASSERTION_TYPES) and bool(
        task.claim_id
    )


def assertion_mapping_integrity() -> float:
    tasks = audit_tasks()
    if not tasks:
        return 0.0
    ok = sum(1 for t in tasks if assertion_mapped(t))
    return round(ok / len(tasks), 6)


__all__ = [
    "ASSERTION_TYPES",
    "AuditTask",
    "assertion_mapped",
    "assertion_mapping_integrity",
    "audit_tasks",
    "dataset_hash",
    "provenance",
]
