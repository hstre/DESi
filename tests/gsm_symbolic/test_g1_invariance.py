"""GSM-Symbolic G1 - layered invariance metric tests.

Each fixture in ``desi.gsm_symbolic.predictions`` drives a specific
metric to a known value; these tests pin those values so the metric
definitions stay deterministic and replay-stable.
"""
from __future__ import annotations

from desi.gsm_symbolic import (
    all_correct_predictions,
    build_groups,
    constant_wrong_predictions,
    drifting_wrong_predictions,
    first_only_correct_predictions,
    noop_fragile_predictions,
    noop_gap,
    score_predictions,
    template_stability_gain,
)

# 3 templates x 3 families (main / p1 / p2) = 9 groups; 9+12+12 = 33 tasks.
_GROUPS = 9
_TASKS = 33


def test_group_and_task_counts() -> None:
    assert len(build_groups()) == _GROUPS
    assert sum(g.size() for g in build_groups()) == _TASKS


# --- all correct --------------------------------
def test_all_correct_is_perfect() -> None:
    m = score_predictions(all_correct_predictions())
    assert m.total_groups == _GROUPS
    assert m.total_tasks == _TASKS
    assert m.frame_accuracy == 1.0
    assert m.strict_group_correctness == 1.0
    assert m.answer_consistency == 1.0
    # No error groups -> errors are vacuously stable.
    assert m.error_stability == 1.0


# --- first-only correct: mixed groups, stable error ---
def test_first_only_correct_metrics() -> None:
    m = score_predictions(first_only_correct_predictions())
    assert m.strict_group_correctness == 0.0
    # Each group mixes one correct + wrong -> not consistent.
    assert m.answer_consistency == 0.0
    # All wrong instances share one wrong answer -> stable.
    assert m.error_stability == 1.0
    # One correct task per group.
    assert m.frame_accuracy == round(_GROUPS / _TASKS, 6)


# --- constant wrong: all-wrong, stable error ----
def test_constant_wrong_is_consistent_and_stable() -> None:
    m = score_predictions(constant_wrong_predictions())
    assert m.frame_accuracy == 0.0
    assert m.strict_group_correctness == 0.0
    # All-wrong groups still share one correctness status.
    assert m.answer_consistency == 1.0
    assert m.error_stability == 1.0


# --- drifting wrong: all-wrong, UNSTABLE error --
def test_drifting_wrong_is_consistent_but_unstable() -> None:
    m = score_predictions(drifting_wrong_predictions())
    assert m.strict_group_correctness == 0.0
    assert m.answer_consistency == 1.0
    # Distinct wrong answer per instance -> drift.
    assert m.error_stability == 0.0


# --- consistency vs error-stability are distinct -
def test_consistency_and_error_stability_decoupled() -> None:
    """constant_wrong and drifting_wrong are both fully consistent
    (all-wrong) yet differ on error-stability - the two diagnostics
    measure different things."""
    c = score_predictions(constant_wrong_predictions())
    d = score_predictions(drifting_wrong_predictions())
    assert c.answer_consistency == d.answer_consistency == 1.0
    assert c.error_stability == 1.0
    assert d.error_stability == 0.0


# --- template stability gain --------------------
def test_stability_gain_is_difference_of_strict() -> None:
    gain = template_stability_gain(
        baseline=first_only_correct_predictions(),
        desi=all_correct_predictions(),
    )
    assert gain == 1.0


def test_stability_gain_zero_when_arms_equal() -> None:
    p = all_correct_predictions()
    assert template_stability_gain(baseline=p, desi=p) == 0.0


# --- noop gap -----------------------------------
def test_noop_gap_zero_when_all_correct() -> None:
    assert noop_gap(all_correct_predictions()) == 0.0


def test_noop_gap_positive_when_noop_fragile() -> None:
    # Every P2 noop instance wrong, bases correct -> full gap.
    assert noop_gap(noop_fragile_predictions()) == 1.0


# --- determinism --------------------------------
def test_metrics_replay_stable() -> None:
    a = score_predictions(first_only_correct_predictions()).to_dict()
    b = score_predictions(first_only_correct_predictions()).to_dict()
    assert a == b
