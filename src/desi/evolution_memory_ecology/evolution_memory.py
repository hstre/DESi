"""v30.3 - persistent generational memory.

Every generation is preserved in the run record; none is
forgotten. Generation traceability is the fraction of generations
that are fully recorded and hash-chained, and human approval is
enforced in every generation.
"""
from __future__ import annotations

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .generations import run


def memory_complete() -> bool:
    """Every generation index 0..N-1 is present exactly once."""
    r = run()
    idxs = sorted(g.index for g in r.records)
    return idxs == list(range(r.generations))


def generation_traceability() -> float:
    """Fraction of generations that are fully recorded (indexed,
    branch-anchored and hash-chained), in [0, 1]."""
    r = run()
    if not r.records:
        return 0.0
    ok = sum(
        1 for g in r.records
        if g.branch_id and g.parent_branch and g.gen_hash
    )
    return round(ok / len(r.records), 6)


def governance_preservation() -> float:
    """1.0 iff governance stayed intact in every generation."""
    return 1.0 if run().all_governance_intact else 0.0


def human_approval_enforcement() -> float:
    """1.0 iff human approval is required in every generation and
    mandatory globally."""
    r = run()
    if not HUMAN_APPROVAL_REQUIRED:
        return 0.0
    return 1.0 if r.all_human_approval else 0.0


__all__ = [
    "generation_traceability",
    "governance_preservation",
    "human_approval_enforcement",
    "memory_complete",
]
