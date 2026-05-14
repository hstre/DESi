"""Category A — everyday causality. Documents v1.4's observed behaviour.

Pinning is intentional: these tests document the v1.5 baseline so
any drift surfaces in CI. v1.6+ may improve the numbers, but it
must update the pinned counts and surface the improvement in the
benchmark report.
"""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    GroundTruth,
    cases_by_category,
    compute_metrics,
)
from desi.recursive import ResolutionState


def _cat_a_run():
    return BenchmarkRunner().run(
        cases_by_category(Category.A_EVERYDAY_CAUSALITY)
    )


def test_category_a_has_ten_cases() -> None:
    assert len(cases_by_category(Category.A_EVERYDAY_CAUSALITY)) == 10


def test_category_a_every_case_ground_truth_is_bridge() -> None:
    for c in cases_by_category(Category.A_EVERYDAY_CAUSALITY):
        assert c.ground_truth is GroundTruth.SHOULD_BRIDGE


def test_category_a_pinned_completion_count() -> None:
    """v1.5 baseline: 4 of 10 causal claims silently complete.

    Findings noted in docs/memory/v1_5.md: the parser produces
    clean particular structure for these cases, the consilium has
    no counter-evidence, and the bridge is silently accepted.
    """
    run = _cat_a_run()
    completed = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    assert completed == 4


def test_category_a_pinned_blocked_count() -> None:
    """v1.5 baseline: 6 of 10 causal claims block at depth=0.

    Findings: the v1.2 premise extractor cannot parse negative
    verbs ("will not start", "is not watered") into PARTICULAR
    propositions, so the conclusion falls through to UNREACHABLE
    → REJECTED → BLOCKED at the root.
    """
    run = _cat_a_run()
    blocked = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
    )
    assert blocked == 6


def test_category_a_false_positive_count_is_four() -> None:
    """v1.5 pin: 4 cases silently invent certainty (FP).

    The directive's research question — 'does DESi discover real
    gaps, or invent them?' — answers 4/10 for everyday causal
    cases: half of those the parser can read.
    """
    run = _cat_a_run()
    fps = sum(1 for r in run.results if r.false_positive)
    assert fps == 4
