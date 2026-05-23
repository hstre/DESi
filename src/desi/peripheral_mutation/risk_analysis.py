"""v31.0 - mutation risk analysis.

A core-targeting mutation is the highest risk and must be
rejected. Risk analysis is descriptive and traceable; it never
auto-adapts policy.
"""
from __future__ import annotations

from .mutation_classifier import (
    core_targeting, proposed_mutations, rejected,
)
from .protected_core import is_protected_core


def core_protection() -> float:
    """Fraction of core-targeting mutations that are rejected, in
    [0, 1]."""
    core = core_targeting()
    if not core:
        return 1.0
    rejected_ids = {m.mutation_id for m in rejected()}
    protected = sum(
        1 for m in core if m.mutation_id in rejected_ids
    )
    return round(protected / len(core), 6)


def boundary_enforcement() -> float:
    """Fraction of proposals classified consistently with the
    boundary (core -> rejected, peripheral -> accepted), in
    [0, 1]."""
    ms = proposed_mutations()
    if not ms:
        return 0.0
    ok = 0
    for m in ms:
        if is_protected_core(m.target_area):
            ok += int(m.is_rejected())
        else:
            ok += int(not m.is_rejected())
    return round(ok / len(ms), 6)


def mutation_traceability() -> float:
    """Fraction of proposals with a complete trace (target,
    status, decision), in [0, 1]."""
    ms = proposed_mutations()
    if not ms:
        return 0.0
    ok = sum(
        1 for m in ms
        if m.target_area and m.status and m.decision
    )
    return round(ok / len(ms), 6)


__all__ = [
    "boundary_enforcement",
    "core_protection",
    "mutation_traceability",
]
