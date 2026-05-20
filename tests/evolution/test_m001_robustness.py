"""v0.8 robustness check on M-001 — was the v0.7 improvement seed-luck?

This file is the operational test the v0.8 directive asks for: run the
*same* M-001 mutation across the five mandatory seeds and require that
the SignificanceGate verdict reads ``improved`` — not ``inconclusive``.

The branch evidence function in v0.7 is deterministic on the trajectory
structure (independent of the random seed), so v0.8 expects every seed
to produce the same per-scenario verdict. Documenting this explicitly
is the point: if a later version introduces seed-driven variation, this
test will surface the drift instead of letting it pass silently.
"""
from __future__ import annotations

from desi.evolution import (
    CloneSandbox,
    DEFAULT_SEEDS,
    MultiSeedMutationEvaluation,
    SignificanceGate,
    m_001,
)
from desi.evolution.sandbox import default_stable


def _run_multi_seed():
    clone = CloneSandbox(default_stable())
    p = m_001()
    clone.apply(p)
    return MultiSeedMutationEvaluation().run(clone, p.mutation_id)


# ---------------------------------------------------------------------------
# Per-seed verdict on the load-bearing scenario must be improved on
# every seed — otherwise the v0.7 result was seed-luck.
# ---------------------------------------------------------------------------


def test_m001_is_improved_on_explosion_for_every_seed() -> None:
    report = _run_multi_seed()
    explosion = report.aggregates["ADV_BRANCH_EXPLOSION"]
    assert explosion.improved_seed_count == 5, (
        f"M-001 only improved on {explosion.improved_seed_count}/5 seeds "
        f"of ADV_BRANCH_EXPLOSION; the v0.7 promotion was seed-luck."
    )
    assert explosion.regressed_seed_count == 0


def test_m001_does_not_regress_S2_on_any_seed() -> None:
    report = _run_multi_seed()
    s2 = report.aggregates["S2"]
    assert s2.regressed_seed_count == 0


def test_m001_does_not_regress_S6_on_any_seed() -> None:
    report = _run_multi_seed()
    s6 = report.aggregates["S6"]
    assert s6.regressed_seed_count == 0


# ---------------------------------------------------------------------------
# Aggregate per-seed deltas: the mean must remain negative on the
# adversarial scenario (branches reduced), and the standard deviation
# must be zero (the v0.7 mechanism is deterministic on this surface).
# ---------------------------------------------------------------------------


def test_m001_mean_branch_delta_is_negative_on_explosion() -> None:
    report = _run_multi_seed()
    assert report.aggregates["ADV_BRANCH_EXPLOSION"].mean_branch_delta < 0.0


def test_m001_branch_delta_std_is_zero_on_explosion_v08() -> None:
    """v0.7 mechanism is seed-deterministic on this scenario surface;
    std must read 0.0. If a later release introduces seed-driven noise,
    this test will fail and force a re-think of the gate threshold."""
    report = _run_multi_seed()
    assert report.aggregates["ADV_BRANCH_EXPLOSION"].std_branch_delta == 0.0


# ---------------------------------------------------------------------------
# SignificanceGate verdict for M-001 — the v0.8 deliverable.
# ---------------------------------------------------------------------------


def test_m001_significance_gate_verdict_is_improved() -> None:
    report = _run_multi_seed()
    decision = SignificanceGate().decide(report)
    assert decision.verdict == "improved"
    assert decision.supporting_seeds == DEFAULT_SEEDS
    assert decision.failing_seeds == ()


def test_m001_seed_list_in_report_matches_directive() -> None:
    report = _run_multi_seed()
    assert report.seeds == (42, 43, 44, 45, 46)


# ---------------------------------------------------------------------------
# Stress seed: ADV_BRANCH_EXPLOSION must also improve on seed=999 —
# logged but not promotion-relevant.
# ---------------------------------------------------------------------------


def test_m001_optional_stress_seed_also_shows_improvement() -> None:
    clone = CloneSandbox(default_stable())
    p = m_001()
    clone.apply(p)
    report = MultiSeedMutationEvaluation(include_stress=True).run(
        clone, p.mutation_id,
    )
    assert report.stress_outcome is not None
    assert report.stress_outcome.delta.verdict == "improved"
