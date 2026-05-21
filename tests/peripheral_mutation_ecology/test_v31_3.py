"""v31.3 - Long-Horizon Peripheral Mutation Ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.peripheral_mutation import core_fingerprint
from desi.peripheral_mutation_ecology import (
    build_ecology_artifact, build_report, core_drift,
    core_preservation, ecology_recompute_reduction,
    generation_count, generation_stability, generations,
    governance_preservation, is_acyclic, lineage_integrity,
    orphans, replay_stability, succeeded_generations, targets_main,
    total_baseline_recomputes, total_mutated_recomputes,
)
from desi.peripheral_mutation_ecology.branch_ecology import (
    all_branch_isolated, core_drift_count,
)
from desi.peripheral_mutation_ecology.report import (
    REPORT_VERDICTS, VERDICT_STABLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "peripheral_mutation"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- 25 real mutation generations ---------------
def test_twenty_five_generations() -> None:
    assert generation_count() == 25
    assert len(generations()) == 25


def test_one_mutation_per_generation() -> None:
    for g in generations():
        assert g.baseline_recomputes == 3
        assert g.mutated_recomputes == 1


def test_every_generation_succeeded() -> None:
    assert generation_stability() == 1.0
    assert len(succeeded_generations()) == generation_count()
    for g in generations():
        assert g.succeeded


def test_every_generation_output_identical() -> None:
    for g in generations():
        assert g.output_identical
        assert g.recompute_reduced
        assert g.output_signature != "MISMATCH"


def test_ecology_recompute_reduction_real() -> None:
    assert total_mutated_recomputes() < total_baseline_recomputes()
    assert ecology_recompute_reduction() > 0.0


# --- core invariance over the whole ecology -----
def test_core_preservation_full() -> None:
    assert core_preservation() == 1.0
    assert core_drift() is False
    assert core_drift_count() == 0


def test_every_generation_keeps_core_fingerprint() -> None:
    root = core_fingerprint()
    for g in generations():
        assert g.core_fingerprint == root
        assert g.core_preserved


def test_governance_preservation_full() -> None:
    assert governance_preservation() == 1.0
    for g in generations():
        assert g.governance_preserved
        assert g.human_approval_required is True


# --- lineage / branch isolation -----------------
def test_lineage_integrity_full() -> None:
    assert lineage_integrity() == 1.0
    assert orphans() == ()
    assert is_acyclic() is True


def test_branch_isolated_not_main() -> None:
    assert all_branch_isolated() is True
    assert targets_main() is False
    for g in generations():
        assert g.branch_id.startswith(
            "proposal/peripheral_mutation_v1/"
        )
        assert g.targets_main is False


def test_lineage_chain_descends() -> None:
    recs = generations()
    assert recs[0].parent_branch == "proposal/peripheral_mutation_v1"
    for prev, cur in zip(recs, recs[1:]):
        assert cur.parent_branch == prev.branch_id


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        generation_stability(), core_preservation(),
        governance_preservation(), lineage_integrity(),
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


def test_report_not_halt() -> None:
    assert build_report().halt is False


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v31_3_ecology.json")
    assert art["schema_version"] == (
        "v31_3_peripheral_mutation_ecology"
    )


def test_artifact_is_branch_isolated() -> None:
    art = _load("v31_3_ecology.json")
    assert art["branch"] == "proposal/peripheral_mutation_v1"
    assert art["targets_main"] is False


def test_artifact_carries_disclaimer() -> None:
    art = _load("v31_3_ecology.json")
    disc = art["disclaimer"].lower()
    assert "25 real" in disc
    assert "byte-identical" in disc
    assert "no core module is touched" in disc
    assert "nothing is merged" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v31_3_ecology.json")
    required = {
        "generation_stability", "core_preservation",
        "governance_preservation", "lineage_integrity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v31_3_ecology.json")
    live = build_ecology_artifact()
    assert art == live
