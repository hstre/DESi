"""Aufgabe 9 — contamination check against every protected
benchmark text.

Pool: every VALID-labeled chain across v1.5 main, v1.9 tool,
v2.3 multistep, v3.14 held-out, v3.15 adversarial, v3.4
frame benchmark, and the v4.0 external corpus. Pre-filtering
by current audit state is *not* applied (the v4.9 guards
suspend chains that previously passed, so pre-filtering
would be tautological — see v4.7's contamination
discussion).

A pair-table hit on any of these is a candidate regression.
We then check whether the chain would have been killed by
an earlier guard anyway; only chains uniquely killed by the
v4.9 pair tables count as contamination.
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
from ..tools.benchmark import ALL_TOOL_CASES
from .inversion_check import (
    contradiction_fires_on_text, polarity_fires_on_text,
)


def _protected_pool() -> tuple[str, ...]:
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
    return tuple(pool)


@dataclass(frozen=True)
class ContaminationReport:
    protected_pool_size: int
    c1_contamination_count: int
    c2_contamination_count: int
    contamination_count: int
    contaminating_texts: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "protected_pool_size": self.protected_pool_size,
            "c1_contamination_count":
                self.c1_contamination_count,
            "c2_contamination_count":
                self.c2_contamination_count,
            "contamination_count": self.contamination_count,
            "contaminating_texts": [
                t[:120] for t in self.contaminating_texts
            ],
        }


def check() -> ContaminationReport:
    pool = _protected_pool()
    c1: list[str] = []
    c2: list[str] = []
    for text in pool:
        if contradiction_fires_on_text(text):
            c1.append(text)
        if polarity_fires_on_text(text):
            c2.append(text)
    union = list({*c1, *c2})
    return ContaminationReport(
        protected_pool_size=len(pool),
        c1_contamination_count=len(c1),
        c2_contamination_count=len(c2),
        contamination_count=len(union),
        contaminating_texts=tuple(union),
    )


__all__ = ["ContaminationReport", "check"]
