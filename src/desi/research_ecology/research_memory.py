"""v27.3 - research memory: forgetting and rediscovery.

Tracks ideas going dormant (forgotten) and returning (rediscovered)
over the long horizon. Forgetting is soft: a dormant method stays
present at low strength and is never removed, so its lineage,
fragility marks and open questions are preserved.
"""
from __future__ import annotations

from desi.research_harvester import all_claims
from desi.research_harvester.taxonomy import ClaimClass as K

from .ecology import run


def forgotten_events() -> int:
    return run().forgotten_events


def rediscovery_events() -> int:
    return run().rediscovery_events


def lineage_preserved() -> bool:
    """No research line is ever deleted (the worst step still
    has every line present)."""
    r = run()
    return r.min_present_lines == r.method_count


def fragility_visibility() -> float:
    """Fraction of the run's sampled steps at which every fragile
    (speculative) claim remains marked, in [0, 1]."""
    r = run()
    expected = sum(
        1 for c in all_claims()
        if c.claim_class == K.SPECULATIVE.value
    )
    if not r.sample:
        return 0.0
    ok = sum(
        1 for s in r.sample if s.fragile_visible == expected
    )
    return round(ok / len(r.sample), 6)


def open_question_preservation() -> float:
    """Fraction of sampled steps at which every open question
    remains visible, in [0, 1]."""
    r = run()
    expected = sum(
        1 for c in all_claims()
        if c.claim_class == K.OPEN_QUESTION.value
    )
    if not r.sample:
        return 0.0
    ok = sum(
        1 for s in r.sample
        if s.open_question_visible == expected
    )
    return round(ok / len(r.sample), 6)


def conflict_preservation() -> float:
    """Fraction of sampled steps at which the declared conflicts
    remain present, in [0, 1]."""
    r = run()
    if not r.sample:
        return 0.0
    ok = sum(
        1 for s in r.sample
        if s.conflict_count == r.conflict_count
    )
    return round(ok / len(r.sample), 6)


__all__ = [
    "conflict_preservation",
    "forgotten_events",
    "fragility_visibility",
    "lineage_preserved",
    "open_question_preservation",
    "rediscovery_events",
]
