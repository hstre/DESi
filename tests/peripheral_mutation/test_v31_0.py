"""v31.0 - Mutation Boundary Enforcement tests."""
from __future__ import annotations

import json
import pathlib

from desi.peripheral_mutation import (
    ALLOWED_EVOLUTION_SPACE, PROTECTED_CORE, accepted,
    boundary_enforcement, build_boundaries_artifact, build_report,
    classify, core_fingerprint, core_identity, core_protection,
    core_targeting, governance_preservation, is_allowed,
    is_protected_core, mutation_traceability, proposed_mutations,
    rejected, replay_stability,
)
from desi.peripheral_mutation.protected_core import (
    DECISION_REJECTED, STATUS_FORBIDDEN_CORE,
)
from desi.peripheral_mutation.report import (
    REPORT_VERDICTS, VERDICT_BOUNDED,
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


# --- protected core -----------------------------
def test_seven_protected_core_areas() -> None:
    assert len(PROTECTED_CORE) == 7
    for area in PROTECTED_CORE:
        assert is_protected_core(area)
        assert not is_allowed(area)


def test_allowed_space_disjoint_from_core() -> None:
    assert set(ALLOWED_EVOLUTION_SPACE).isdisjoint(
        set(PROTECTED_CORE)
    )
    for area in ALLOWED_EVOLUTION_SPACE:
        assert is_allowed(area)


# --- forbidden-core detection -------------------
def test_core_targeting_mutations_rejected() -> None:
    for area in PROTECTED_CORE:
        c = classify(area, "X")
        assert c.status == STATUS_FORBIDDEN_CORE
        assert c.decision == DECISION_REJECTED


def test_core_protection_full() -> None:
    assert core_protection() == 1.0
    rejected_ids = {m.mutation_id for m in rejected()}
    for m in core_targeting():
        assert m.mutation_id in rejected_ids


def test_boundary_enforcement_full() -> None:
    assert boundary_enforcement() == 1.0


def test_peripheral_mutations_accepted() -> None:
    for m in accepted():
        assert not is_protected_core(m.target_area)


def test_proposed_split() -> None:
    assert len(proposed_mutations()) == (
        len(ALLOWED_EVOLUTION_SPACE) + len(PROTECTED_CORE)
    )
    assert len(core_targeting()) == len(PROTECTED_CORE)


# --- core identity / governance -----------------
def test_core_identity_full() -> None:
    assert core_identity() == 1.0
    assert core_fingerprint() == core_fingerprint()


def test_governance_preservation_full() -> None:
    assert governance_preservation() == 1.0


def test_mutation_traceability_full() -> None:
    assert mutation_traceability() == 1.0


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        core_protection(), boundary_enforcement(),
        governance_preservation(), mutation_traceability(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_bounded() -> None:
    assert build_report().recommendation == VERDICT_BOUNDED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v31_0_boundaries.json")
    assert art["schema_version"] == "v31_0_mutation_boundaries"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v31_0_boundaries.json")
    disc = art["disclaimer"].lower()
    assert "completely-immutable protected core" in disc
    assert "forbidden_core_mutation" in disc
    assert "nothing is mutated here" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v31_0_boundaries.json")
    required = {
        "core_protection", "boundary_enforcement",
        "governance_preservation", "mutation_traceability",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v31_0_boundaries.json")
    live = build_boundaries_artifact()
    assert art == live
