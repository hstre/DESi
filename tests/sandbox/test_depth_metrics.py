"""Tests for v2.2 fitness, impact metrics, overreasoning, plateau."""
from __future__ import annotations

import math

from desi.sandbox import (
    DepthImpactMetrics,
    DepthStressSuite,
    compute_fitness,
    compute_impact_metrics,
    detect_plateau,
    overreasoning_check,
)


# ---------------------------------------------------------------------------
# Impact metrics (Aufgabe 5)
# ---------------------------------------------------------------------------


def test_impact_metrics_carry_six_observables() -> None:
    run = DepthStressSuite().run(max_depth=3)
    m = compute_impact_metrics(run)
    for f in (
        "mean_resolution_depth", "max_resolution_depth",
        "cycle_detection_rate", "blocked_propagation_rate",
        "depth_exceeded_rate", "resolution_complete_rate",
    ):
        assert hasattr(m, f)


def test_impact_metrics_are_deterministic() -> None:
    a = compute_impact_metrics(DepthStressSuite().run(max_depth=3))
    b = compute_impact_metrics(DepthStressSuite().run(max_depth=3))
    assert a == b


def test_resolution_complete_rate_is_unit_interval() -> None:
    m = compute_impact_metrics(DepthStressSuite().run(max_depth=3))
    assert 0.0 <= m.resolution_complete_rate <= 1.0


# ---------------------------------------------------------------------------
# Fitness (Aufgabe 4)
# ---------------------------------------------------------------------------


def _clean_gate_args():
    return dict(
        main_false_positives=0, main_recall=1.0, main_precision=1.0,
        main_hash_mismatches=0, main_authority_blocks=10,
        tool_precision=1.0,
    )


def test_fitness_is_nonnegative_on_clean_gate() -> None:
    run = DepthStressSuite().run(max_depth=3)
    fb = compute_fitness(run, **_clean_gate_args())
    assert fb.killed is False
    assert fb.fitness >= 0.0


def test_fitness_killed_on_false_positive() -> None:
    run = DepthStressSuite().run(max_depth=3)
    fb = compute_fitness(run, **{**_clean_gate_args(),
                                  "main_false_positives": 1})
    assert fb.killed is True
    assert fb.fitness == -math.inf
    assert "false_positives" in fb.kill_reason


def test_fitness_killed_on_hash_mismatch() -> None:
    run = DepthStressSuite().run(max_depth=3)
    fb = compute_fitness(run, **{**_clean_gate_args(),
                                  "main_hash_mismatches": 1})
    assert fb.killed is True


def test_fitness_killed_on_authority_failure() -> None:
    run = DepthStressSuite().run(max_depth=3)
    fb = compute_fitness(run, **{**_clean_gate_args(),
                                  "main_authority_blocks": 9})
    assert fb.killed is True
    assert "authority_blocks" in fb.kill_reason


def test_fitness_killed_on_precision_loss() -> None:
    run = DepthStressSuite().run(max_depth=3)
    fb = compute_fitness(run, **{**_clean_gate_args(),
                                  "main_precision": 0.98})
    assert fb.killed is True


def test_fitness_breakdown_carries_three_reward_components() -> None:
    run = DepthStressSuite().run(max_depth=3)
    fb = compute_fitness(run, **_clean_gate_args())
    assert (fb.resolved_depth_cases
            + fb.cycle_detection_correct
            + fb.blocked_propagation_correct) == fb.fitness


# ---------------------------------------------------------------------------
# Overreasoning guard (Aufgabe 6)
# ---------------------------------------------------------------------------


def _m(cycle=1.0, blocked=1.0):
    return DepthImpactMetrics(
        mean_resolution_depth=0.0, max_resolution_depth=0,
        cycle_detection_rate=cycle,
        blocked_propagation_rate=blocked,
        depth_exceeded_rate=0.0, resolution_complete_rate=0.0,
    )


def test_overreasoning_silent_when_no_prior_metrics() -> None:
    v = overreasoning_check(
        prev_metrics=None, new_metrics=_m(),
        prev_fitness=None, new_fitness=5.0,
        hash_mismatches=0,
    )
    assert v.rejected is False


def test_overreasoning_silent_when_fitness_did_not_grow() -> None:
    v = overreasoning_check(
        prev_metrics=_m(cycle=1.0), new_metrics=_m(cycle=0.0),
        prev_fitness=5.0, new_fitness=5.0,
        hash_mismatches=0,
    )
    assert v.rejected is False


def test_overreasoning_rejects_when_cycle_rate_decreases_for_more_fitness() -> None:
    v = overreasoning_check(
        prev_metrics=_m(cycle=1.0), new_metrics=_m(cycle=0.5),
        prev_fitness=5.0, new_fitness=6.0,
        hash_mismatches=0,
    )
    assert v.rejected is True
    assert "cycle" in v.reason


def test_overreasoning_rejects_when_blocked_rate_decreases() -> None:
    v = overreasoning_check(
        prev_metrics=_m(blocked=1.0), new_metrics=_m(blocked=0.5),
        prev_fitness=5.0, new_fitness=6.0,
        hash_mismatches=0,
    )
    assert v.rejected is True
    assert "blocked" in v.reason


def test_overreasoning_rejects_on_replay_mismatch() -> None:
    v = overreasoning_check(
        prev_metrics=_m(), new_metrics=_m(),
        prev_fitness=5.0, new_fitness=5.0,
        hash_mismatches=1,
    )
    assert v.rejected is True
    assert "replay" in v.reason


# ---------------------------------------------------------------------------
# Plateau detection (Aufgabe 8)
# ---------------------------------------------------------------------------


def test_plateau_detected_after_five_zero_deltas() -> None:
    history = [3.0, 5.0, 5.0, 5.0, 5.0, 5.0]
    assert detect_plateau(history, window=5) is True


def test_no_plateau_when_fitness_moves() -> None:
    history = [3.0, 4.0, 5.0, 6.0, 7.0]
    assert detect_plateau(history, window=5) is False


def test_no_plateau_with_short_history() -> None:
    assert detect_plateau([5.0, 5.0, 5.0], window=5) is False
    assert detect_plateau([], window=5) is False
