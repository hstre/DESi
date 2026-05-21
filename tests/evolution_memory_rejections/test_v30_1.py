"""v30.1 - Rejection Memory & Risk Ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.evolution_memory import rejected_mutations
from desi.evolution_memory_rejections import (
    auto_blocks_future_ideas, build_rejections_artifact,
    build_report, escalation_pattern, governance_neutrality,
    nothing_deleted, recurrent_risks, rejection_history,
    risk_clusters, risk_occurrences, risk_pattern_visibility,
    risk_traceability, replay_stability,
    unsafe_recurrence_visibility,
)
from desi.evolution_memory_rejections.report import (
    REPORT_VERDICTS, VERDICT_REMEMBERED,
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


# --- risk patterns surfaced ---------------------
def test_risk_pattern_visibility_full() -> None:
    assert risk_pattern_visibility() == 1.0


def test_unsafe_recurrence_visibility_full() -> None:
    assert unsafe_recurrence_visibility() == 1.0


def test_recurrent_risks_surfaced() -> None:
    clusters = risk_clusters()
    for rt, ms in clusters.items():
        if len(ms) >= 2:
            assert rt in set(recurrent_risks())


def test_escalation_pattern_detected() -> None:
    assert len(escalation_pattern()) >= 1


# --- governance neutrality (no policy learning) -
def test_governance_neutrality_full() -> None:
    assert governance_neutrality() == 1.0


def test_no_auto_blocking() -> None:
    assert auto_blocks_future_ideas() is False


def test_report_has_no_blocking_fields() -> None:
    d = build_report().to_dict()
    forbidden = {"blocklist", "blocked", "policy_update",
                 "learned_weights", "auto_reject"}
    assert forbidden.isdisjoint(set(d.keys()))


# --- traceability & preservation ----------------
def test_risk_traceability_full() -> None:
    assert risk_traceability() == 1.0


def test_nothing_deleted() -> None:
    assert nothing_deleted() is True
    assert len(rejection_history()) == len(rejected_mutations())


def test_every_occurrence_has_invariant() -> None:
    for o in risk_occurrences():
        assert o.risk_type
        assert o.invariant
        assert o.agent


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        risk_pattern_visibility(), unsafe_recurrence_visibility(),
        governance_neutrality(), risk_traceability(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_neutral() -> None:
    assert build_report().recommendation == VERDICT_REMEMBERED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v30_1_rejections.json")
    assert art["schema_version"] == "v30_1_rejection_risk_memory"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v30_1_rejections.json")
    disc = art["disclaimer"].lower()
    assert "never auto-blocks" in disc
    assert "no implicit policy-learning layer" in disc
    assert "never deleted" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v30_1_rejections.json")
    required = {
        "risk_pattern_visibility",
        "unsafe_recurrence_visibility", "governance_neutrality",
        "risk_traceability", "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v30_1_rejections.json")
    live = build_rejections_artifact()
    assert art == live
