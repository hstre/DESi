"""v3.99 - counterfactual divergence tests."""
from __future__ import annotations

import json
import pathlib

from desi.counterfactual_divergence.counterfactual import (
    NO_CHAOS_SENTINEL,
    SEPARATION_THRESHOLD,
    all_perturbation_outcomes,
    baseline_auc,
    chaos_threshold,
    coupling_stability,
    perturbation_divergence,
    separation_rate,
)
from desi.counterfactual_divergence.perturb import (
    MAGNITUDE_GRID, PERTURBATION_KINDS,
    PerturbationKind,
    baseline_vectors,
    perturbed_vectors,
)
from desi.counterfactual_divergence.report import (
    SEPARATION_RATE_THRESHOLD,
    build_counterfactual_divergence_artifact,
    build_report,
)


def test_five_perturbation_kinds() -> None:
    """Directive § v3.99 enumerates five
    perturbation kinds."""
    assert len(PERTURBATION_KINDS) == 5


def test_perturbation_kinds_in_enum() -> None:
    enum_values = {p.value for p in PerturbationKind}
    assert enum_values == set(PERTURBATION_KINDS)


def test_magnitude_grid_includes_zero() -> None:
    """Zero magnitude is the baseline (no
    perturbation)."""
    assert 0.0 in MAGNITUDE_GRID


def test_magnitude_grid_is_monotone_increasing() -> None:
    assert list(MAGNITUDE_GRID) == sorted(
        MAGNITUDE_GRID,
    )


def test_baseline_vectors_count_is_nineteen() -> None:
    assert len(baseline_vectors()) == 19


def test_perturbed_vectors_at_zero_match_baseline() -> None:
    """Zero magnitude must produce a no-op
    perturbation."""
    base = baseline_vectors()
    for kind in PERTURBATION_KINDS:
        perturbed = perturbed_vectors(kind, 0.0)
        assert perturbed == base


def test_perturbed_vectors_at_one_differ_from_baseline() -> None:
    """Magnitude 1.0 must produce a measurable
    change in at least one anchor."""
    base = baseline_vectors()
    for kind in PERTURBATION_KINDS:
        perturbed = perturbed_vectors(kind, 1.0)
        diff = sum(
            1 for tid in base
            if perturbed[tid] != base[tid]
        )
        assert diff > 0


def test_cell_count_matches_grid_size() -> None:
    expected = (
        len(PERTURBATION_KINDS)
        * len(MAGNITUDE_GRID)
    )
    assert len(all_perturbation_outcomes()) == expected


def test_baseline_auc_in_unit_interval() -> None:
    assert 0.0 <= baseline_auc() <= 1.0


def test_separation_rate_passes_concept_gate() -> None:
    """Concept Gate condition #3: separation_rate
    < 0.20."""
    assert separation_rate() < (
        SEPARATION_RATE_THRESHOLD
    )


def test_separation_rate_is_zero() -> None:
    """Killerfrage: sind es stabile Doppelganger?
    Yes - no perturbation/magnitude combination
    crosses the AUC=0.70 threshold."""
    assert separation_rate() == 0.0


def test_coupling_stability_is_one() -> None:
    assert coupling_stability() == 1.0


def test_chaos_threshold_is_sentinel() -> None:
    assert chaos_threshold() == NO_CHAOS_SENTINEL


def test_perturbation_divergence_small() -> None:
    """The AUC barely moves under any
    perturbation - mean shift below 0.05."""
    assert perturbation_divergence() < 0.05


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_stable() -> None:
    assert build_report().recommendation == (
        "DOPPELGAENGER_STABLE"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DOPPELGAENGER_STABLE",
        "DOPPELGAENGER_FRAGILE",
        "DOPPELGAENGER_INCONCLUSIVE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_lists_all_cells() -> None:
    art = build_counterfactual_divergence_artifact()
    expected = (
        len(PERTURBATION_KINDS)
        * len(MAGNITUDE_GRID)
    )
    assert len(art["perturbation_outcomes"]) == expected


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_99" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable
