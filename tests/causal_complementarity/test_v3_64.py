"""v3.64 — causal complementarity tests."""
from __future__ import annotations

import json
import pathlib

from desi.causal_complementarity.ablation import (
    MIN_SUBSET_FOR_INFERENCE,
    NECESSARY_IMPORTANCE_FLOOR, PROBE_RADIUS,
    all_pair_factors, baseline_pair_count,
    baseline_resonance, necessary_factors,
    run_ablations, sufficient_factors,
)
from desi.causal_complementarity.causal import (
    aggregate, rank_by_importance,
)
from desi.causal_complementarity.report import (
    build_causal_complementarity_artifact,
    build_report,
)


def test_probe_radius_matches_v350() -> None:
    assert PROBE_RADIUS == 3.5


def test_baseline_resonant_count_is_64() -> None:
    assert baseline_resonance() == 64


def test_baseline_pair_count_is_190() -> None:
    assert baseline_pair_count() == 190


def test_pair_factors_count() -> None:
    assert len(all_pair_factors()) == 190


def test_run_ablations_count() -> None:
    """Four factors: A, B, C, D."""
    results = run_ablations()
    assert len(results) == 4
    factors = {r.factor for r in results}
    assert factors == {
        "A_distance", "B_heterogeneity",
        "C_diversity", "D_coverage_gain",
    }


def test_d_coverage_gain_is_necessary() -> None:
    """D's ablation reduces resonance to 0 on a
    high-power subset (126 pairs)."""
    results = run_ablations()
    d = next(
        r for r in results
        if r.factor == "D_coverage_gain"
    )
    assert d.subset_size >= MIN_SUBSET_FOR_INFERENCE
    assert d.resonant_after == 0
    assert d.causal_importance == 1.0
    assert d.low_power is False


def test_a_distance_is_important() -> None:
    """A's ablation reduces resonance to 0.12 rate
    (12 of 102 pairs); importance 0.65."""
    results = run_ablations()
    a = next(
        r for r in results
        if r.factor == "A_distance"
    )
    assert a.subset_size == 102
    assert a.resonant_after == 12
    assert a.causal_importance > (
        NECESSARY_IMPORTANCE_FLOOR
    )
    assert a.low_power is False


def test_b_heterogeneity_has_low_importance() -> None:
    """B's ablation drops rate from 0.34 to 0.30 -
    a small effect."""
    results = run_ablations()
    b = next(
        r for r in results
        if r.factor == "B_heterogeneity"
    )
    assert b.causal_importance < (
        NECESSARY_IMPORTANCE_FLOOR
    )


def test_c_diversity_is_low_power() -> None:
    """Only 6 pairs have diversity_score == 0 in
    this corpus. C is excluded from necessary_factors
    despite its 100% importance score."""
    results = run_ablations()
    c = next(
        r for r in results
        if r.factor == "C_diversity"
    )
    assert c.low_power is True
    assert c.subset_size < MIN_SUBSET_FOR_INFERENCE


def test_necessary_factors_identified() -> None:
    """Paper-11 v3 gate #5."""
    results = run_ablations()
    nf = necessary_factors(results)
    assert len(nf) >= 1
    assert "A_distance" in nf
    assert "D_coverage_gain" in nf


def test_sufficient_factors_empty() -> None:
    """No single factor's presence alone produces
    resonance with all others ablated; the relevant
    subsets are empty given the entanglement."""
    results = run_ablations()
    assert sufficient_factors(results) == ()


def test_rank_by_importance_orders_descending() -> None:
    ranked = rank_by_importance(run_ablations())
    imps = [r.causal_importance for r in ranked]
    assert imps == sorted(imps, reverse=True)


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_necessary_factor_identified() -> None:
    assert build_report().recommendation == (
        "NECESSARY_FACTOR_IDENTIFIED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "NECESSARY_FACTOR_IDENTIFIED",
        "NO_NECESSARY_FACTOR",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_pair_factors_count() -> None:
    art = build_causal_complementarity_artifact()
    assert len(art["pair_factors"]) == 190
    assert len(art["ablations"]) == 4


def test_paper11_v3_concept_gate_summary() -> None:
    """All five Paper-11 v3 Concept Gates evaluated
    end-to-end."""
    from desi.blind_spot_mapping.report import (
        build_report as v362,
    )
    from desi.complementarity.report import (
        build_report as v361,
    )
    from desi.failure_diversity.report import (
        build_report as v363,
    )
    r61 = v361()
    r62 = v362()
    r63 = v363()
    r64 = build_report()
    # Gate 1
    assert r61.replay_stability == 1.0
    assert r62.replay_stability == 1.0
    assert r63.replay_stability == 1.0
    assert r64.replay_stability == 1.0
    # Gate 2
    assert (
        r61.distance_only_activation
        < r61.combined_activation
    )
    # Gate 3
    assert r62.coverage_gain > 0
    # Gate 4
    assert r63.diversity_activation_correlation > 0
    # Gate 5
    assert len(r64.necessary_factors) >= 1


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_64" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
