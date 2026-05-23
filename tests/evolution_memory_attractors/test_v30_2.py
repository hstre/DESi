"""v30.2 - Evolutionary Attractor Analysis tests."""
from __future__ import annotations

import json
import pathlib

from desi.evolution_memory_attractors import (
    attractor_visibility, attractors, branches_targeting_main,
    build_attractors_artifact, build_report, clusters_by_area,
    drift_visibility, evolution_diversity,
    mutation_cluster_visibility, optimization_traps,
    productive_areas, replay_stability, trap_visibility,
)
from desi.evolution_memory_attractors.report import (
    REPORT_VERDICTS, VERDICT_STABLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "evolution_memory"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- attractors & clusters ----------------------
def test_attractor_visibility_full() -> None:
    assert attractor_visibility() == 1.0


def test_attractors_attract_multiple() -> None:
    for area, ms in attractors().items():
        assert len(ms) >= 2


def test_mutation_cluster_visibility_full() -> None:
    assert mutation_cluster_visibility() == 1.0
    assert len(clusters_by_area()) >= 1


# --- optimization traps = all-rejected areas ----
def test_trap_visibility_full() -> None:
    assert trap_visibility() == 1.0


def test_traps_are_forbidden_core_areas() -> None:
    traps = set(optimization_traps())
    # the protected-core areas are stagnant traps (always rejected)
    for core in ("replay_kernel", "determinism_scanner",
                 "concept_gates", "regression_integrity"):
        assert core in traps
    # productive (accepted) areas are not traps
    assert traps.isdisjoint(set(productive_areas()))


# --- branch drift -------------------------------
def test_drift_visibility_full() -> None:
    assert drift_visibility() == 1.0


def test_no_branch_targets_main() -> None:
    assert branches_targeting_main() == ()


# --- evolution diversity (not collapsed) --------
def test_evolution_diversity_not_collapsed() -> None:
    assert evolution_diversity() >= 0.50


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        attractor_visibility(), mutation_cluster_visibility(),
        drift_visibility(), evolution_diversity(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_stable() -> None:
    assert build_report().recommendation == VERDICT_STABLE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v30_2_attractors.json")
    assert art["schema_version"] == (
        "v30_2_evolutionary_attractors"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v30_2_attractors.json")
    disc = art["disclaimer"].lower()
    assert "descriptive only" in disc
    assert "no policy learning" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v30_2_attractors.json")
    required = {
        "attractor_visibility", "mutation_cluster_visibility",
        "drift_visibility", "evolution_diversity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v30_2_attractors.json")
    live = build_attractors_artifact()
    assert art == live
