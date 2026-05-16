"""Aufgabe 7 — adversarial manipulation set."""
from __future__ import annotations

from desi.frame_consistency_probe.enums import FrameConsistency
from desi.frame_consistency_probe.manipulation import (
    MANIPULATIONS,
    manipulation_detection_rate,
    run_manipulation_suite,
)


def test_at_least_twenty_manipulation_cases() -> None:
    assert len(MANIPULATIONS) >= 20


def test_manipulation_ids_are_unique() -> None:
    ids = [m.case_id for m in MANIPULATIONS]
    assert len(ids) == len(set(ids))


def test_misleading_outer_differs_from_true_inner() -> None:
    for m in MANIPULATIONS:
        assert m.misleading_outer is not m.true_inner, m.case_id


def test_outcomes_one_per_case() -> None:
    outcomes = run_manipulation_suite()
    assert len(outcomes) == len(MANIPULATIONS)


def test_no_outcome_silently_confirms() -> None:
    # The whole point: every adversarial case must produce a
    # non-CONFIRMED classification. Silent confirmation = the
    # manipulation succeeded.
    for o in run_manipulation_suite():
        assert o.classification is not FrameConsistency.FRAME_CONFIRMED, (
            f"{o.case_id} silently confirmed the misleading outer"
        )


def test_detection_rate_meets_threshold() -> None:
    outs = run_manipulation_suite()
    assert manipulation_detection_rate(outs) >= 0.80
