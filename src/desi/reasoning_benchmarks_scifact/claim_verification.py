"""v36.1 - claim verification + QASper answer grounding metrics.

Aggregates the SciFact evidence alignment and unsupported-claim
rejection, the citation integrity (no phantom evidence, plus the v25
citation governance anchor), and the QASper answer grounding
(answerable questions are answered from evidence, unanswerable ones
are flagged rather than fabricated).
"""
from __future__ import annotations

from desi.output_ports_citation import phantom_citation_detection

from .evidence_mapping import (
    cited_evidence_present, is_aligned, is_unsupported,
)
from .qasper_loader import qasper_tasks
from .scifact_loader import scifact_tasks


def evidence_alignment() -> float:
    tasks = scifact_tasks()
    if not tasks:
        return 0.0
    ok = sum(1 for t in tasks if is_aligned(t))
    return round(ok / len(tasks), 6)


def unsupported_claim_rejection() -> float:
    """Of the claims whose evidence does not support a verdict, how
    many are correctly held at NOT_ENOUGH_INFO (rejected, not
    answered)."""
    nei = [t for t in scifact_tasks() if t.label == "NOT_ENOUGH_INFO"]
    if not nei:
        return 0.0
    ok = sum(1 for t in nei if is_unsupported(t))
    return round(ok / len(nei), 6)


def citation_integrity() -> float:
    """No phantom evidence (every cited id exists) and the v25
    citation governance anchor detects phantoms."""
    tasks = scifact_tasks()
    if not tasks:
        return 0.0
    clean = all(cited_evidence_present(t) for t in tasks)
    if not clean:
        return 0.0
    return round(phantom_citation_detection(), 6)


def _grounded(task) -> bool:
    if task.answerable:
        return len(task.evidence) > 0
    # unanswerable -> must be flagged (no fabricated evidence)
    return len(task.evidence) == 0


def answer_grounding() -> float:
    tasks = qasper_tasks()
    if not tasks:
        return 0.0
    ok = sum(1 for t in tasks if _grounded(t))
    return round(ok / len(tasks), 6)


def unanswerable_flagged() -> bool:
    return all(
        len(t.evidence) == 0
        for t in qasper_tasks() if not t.answerable
    )


__all__ = [
    "answer_grounding",
    "citation_integrity",
    "evidence_alignment",
    "unanswerable_flagged",
    "unsupported_claim_rejection",
]
