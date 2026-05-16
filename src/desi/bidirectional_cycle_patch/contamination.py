"""Aufgabe 9 — contamination check.

The patched ``_bidirectional_cycle`` predicate is run against
every currently-audit-supported chain in the protected pool
(v1.5 / v1.9 / v2.3 / v3.14 / v3.15 / v3.16 / v4.0-VALID).
A hit on any of these is a false-negative regression.

Pool construction mirrors v4.3's
``external_audit_patch.contamination`` — the only changed
ingredient is the predicate used.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..external_probe.corpus import all_chains
from ..external_probe.enums import GroundTruth
from ..frame_benchmark import ALL_FRAME_CASES
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from ..tools.benchmark import ALL_TOOL_CASES
from .structural_check import fires_on_text


def _protected_audit_supported_texts() -> tuple[str, ...]:
    auditor = LogicalAuditor()
    pool: list[str] = []
    for case in MAIN_CASES:
        pool.append(case.text)
    for case in ALL_MULTISTEP_CASES:
        pool.append(case.text)
    for case in ALL_HELDOUT_CASES:
        pool.append(case.text)
    for case in ALL_ADVERSARIAL_CASES:
        pool.append(case.text)
    for case in ALL_FRAME_CASES:
        pool.append(case.text)
    for case in ALL_TOOL_CASES:
        pool.append(case.text)
    for case in all_chains():
        if case.ground_truth is GroundTruth.VALID:
            pool.append(case.text)
    out: list[str] = []
    for text in pool:
        if auditor.audit(text).state is (
            LogicalState.LOGICALLY_SUPPORTED
        ):
            out.append(text)
    return tuple(out)


@dataclass(frozen=True)
class ContaminationReport:
    protected_pool_size: int
    contamination_count: int
    contaminating_texts: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "protected_pool_size": self.protected_pool_size,
            "contamination_count": self.contamination_count,
            "contaminating_texts": [
                t[:120] for t in self.contaminating_texts
            ],
        }


def check() -> ContaminationReport:
    pool = _protected_audit_supported_texts()
    hits: list[str] = []
    for text in pool:
        if fires_on_text(text):
            hits.append(text)
    return ContaminationReport(
        protected_pool_size=len(pool),
        contamination_count=len(hits),
        contaminating_texts=tuple(hits),
    )


__all__ = ["ContaminationReport", "check"]
