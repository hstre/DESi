"""v31.1 - Real Peripheral Mutation tests."""
from __future__ import annotations

import json
import pathlib

from desi.peripheral_mutation import is_protected_core
from desi.peripheral_mutation_real import (
    BRANCH, artifact_identity, build_mutations_artifact,
    build_report, core_identity, governance_identity, patches,
    real_mutations, rejected_targets, replay_stability,
    runtime_reduction, successful_mutation_rate,
    successful_mutations, targets_main,
)
from desi.peripheral_mutation_real.report import (
    REPORT_VERDICTS, VERDICT_MUTATED,
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


# --- real mutations succeed ---------------------
def test_successful_mutation_rate_full() -> None:
    assert successful_mutation_rate() == 1.0


def test_mutations_reduce_recompute_with_identical_output() -> None:
    for m in real_mutations():
        assert m.output_identical()
        assert m.recompute_reduced()
        assert m.succeeded()


def test_runtime_reduction_real() -> None:
    assert runtime_reduction() > 0.0


# --- core invariance ----------------------------
def test_core_identity_full() -> None:
    assert core_identity() == 1.0


def test_governance_identity_full() -> None:
    assert governance_identity() == 1.0


def test_artifact_identity_full() -> None:
    assert artifact_identity() == 1.0


def test_no_mutation_targets_core() -> None:
    for m in real_mutations():
        assert not is_protected_core(m.target_area)
        assert m.is_allowed_target


# --- branch isolation ---------------------------
def test_branch_isolated_not_main() -> None:
    assert BRANCH == "proposal/peripheral_mutation_v1"
    assert BRANCH != "main"
    assert targets_main() is False
    for p in patches():
        assert p.branch == BRANCH


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        successful_mutation_rate(), artifact_identity(),
        core_identity(), governance_identity(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_mutated() -> None:
    assert build_report().recommendation == VERDICT_MUTATED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v31_1_mutations.json")
    assert art["schema_version"] == "v31_1_peripheral_mutations"


def test_artifact_is_branch_isolated() -> None:
    art = _load("v31_1_mutations.json")
    assert art["branch"] == "proposal/peripheral_mutation_v1"
    assert art["targets_main"] is False


def test_artifact_carries_disclaimer() -> None:
    art = _load("v31_1_mutations.json")
    disc = art["disclaimer"].lower()
    assert "byte-identical" in disc
    assert "no core modules are touched" in disc
    assert "nothing is merged" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v31_1_mutations.json")
    required = {
        "successful_mutation_rate", "artifact_identity",
        "core_identity", "governance_identity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v31_1_mutations.json")
    live = build_mutations_artifact()
    assert art == live
