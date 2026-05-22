"""v36.1 - deterministic evidence -> label mapping.

DESi derives a SciFact label purely from the stance of the mapped
evidence: any refuting evidence -> REFUTED; otherwise any supporting
evidence -> SUPPORTED; otherwise NOT_ENOUGH_INFO. No claim is asserted
without supporting evidence, and evidence gaps surface as
NOT_ENOUGH_INFO rather than being hidden.
"""
from __future__ import annotations

from .scifact_loader import SciFactTask

LABEL_SUPPORTED = "SUPPORTED"
LABEL_REFUTED = "REFUTED"
LABEL_NEI = "NOT_ENOUGH_INFO"


def derive_label(task: SciFactTask) -> str:
    stances = [s for _, s in task.evidence]
    if "refute" in stances:
        return LABEL_REFUTED
    if "support" in stances:
        return LABEL_SUPPORTED
    return LABEL_NEI


def is_aligned(task: SciFactTask) -> bool:
    return derive_label(task) == task.label


def cited_evidence_present(task: SciFactTask) -> bool:
    """Every cited evidence id must exist in the task's evidence set
    (no phantom evidence)."""
    ids = {eid for eid, _ in task.evidence}
    return all(c in ids for c in task.cited_evidence)


def is_unsupported(task: SciFactTask) -> bool:
    return derive_label(task) == LABEL_NEI


__all__ = [
    "LABEL_NEI",
    "LABEL_REFUTED",
    "LABEL_SUPPORTED",
    "cited_evidence_present",
    "derive_label",
    "is_aligned",
    "is_unsupported",
]
