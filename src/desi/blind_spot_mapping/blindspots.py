"""v3.62 — blind spot accounting.

A "blind spot" is a leakage trajectory not covered by
any plateau anchor at the probe radius. The directive's
``uncovered_claims_before`` is the full leakage cohort
(no anchors active); ``uncovered_claims_after`` is the
set of leakages not covered by ANY anchor in the
plateau cohort.
"""
from __future__ import annotations

from .coverage import (
    all_anchor_coverages, all_leakage_vectors,
)


def uncovered_before() -> int:
    """Every leakage trajectory is uncovered before any
    anchor is activated."""
    return len(all_leakage_vectors())


def uncovered_after() -> int:
    coverages = all_anchor_coverages()
    covered: set[int] = set()
    for c in coverages:
        covered |= c.coverage
    return len(all_leakage_vectors()) - len(covered)


def fully_covered_after() -> int:
    return len(all_leakage_vectors()) - uncovered_after()


__all__ = [
    "fully_covered_after", "uncovered_after",
    "uncovered_before",
]
