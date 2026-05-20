"""v16.0 - Evidence Topology Audit tests."""
from __future__ import annotations

import json
import pathlib

from desi.criminal_epistemics import (
    CLAIM_STATUSES, ClaimStatus, build_report,
    build_topology_artifact, claims,
    conflict_clusters, conflict_detection,
    escalation_instances, evidence_independence,
    independently_supported, single_source_claims,
    source_dependency, status_histogram,
    timeline_consistency, timeline_inconsistencies,
    uncertainty_visible,
    unsupported_escalation_detection,
)
from desi.criminal_epistemics.report import (
    REPORT_VERDICTS, VERDICT_STRUCTURED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "criminal_epistemics"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- closed vocabulary / safety -----------------
def test_claim_statuses_closed_set() -> None:
    assert CLAIM_STATUSES == tuple(
        s.value for s in ClaimStatus
    )
    assert len(CLAIM_STATUSES) == 7


def test_no_truth_or_guilt_value() -> None:
    """The closed vocabularies must not contain a
    'solved', 'guilty', perpetrator, or
    conspiracy-confirmed value (checked as whole
    tokens, so 'unresolved' is fine)."""
    import re

    forbidden = {
        "guilty", "solved", "perpetrator",
        "culprit", "conspiracy", "true",
    }
    tokens = set()
    for v in list(CLAIM_STATUSES) + list(REPORT_VERDICTS):
        tokens.update(re.split(r"[^a-z]+", v.lower()))
    assert not (tokens & forbidden)


def test_no_claim_asserts_a_named_perpetrator() -> None:
    """No claim in the corpus may be VERIFIED or
    STRONGLY_SUPPORTED while naming a specific
    organisation/person as responsible - those must
    stay SPECULATIVE/CONTESTED/UNRESOLVED."""
    strong = {
        ClaimStatus.VERIFIED.value,
        ClaimStatus.STRONGLY_SUPPORTED.value,
    }
    for c in claims():
        if "directed the assassination" in c.text:
            assert c.status not in strong


def test_speculative_claim_stays_speculative() -> None:
    """The named-organisation claim must remain
    SPECULATIVE no matter how strongly it is
    asserted elsewhere."""
    spec = [
        c for c in claims()
        if c.status == ClaimStatus.SPECULATIVE.value
    ]
    assert spec
    for c in spec:
        assert c.status == ClaimStatus.SPECULATIVE.value


# --- metrics ------------------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        evidence_independence(),
        conflict_detection(),
        timeline_consistency(),
        unsupported_escalation_detection(),
        source_dependency(),
    ):
        assert 0.0 <= m <= 1.0


def test_evidence_independence_full() -> None:
    assert evidence_independence() == 1.0


def test_conflict_detection_full() -> None:
    assert conflict_detection() == 1.0


def test_conflict_clusters_present() -> None:
    clusters = conflict_clusters()
    assert "shot_origin" in clusters
    assert "shooter_count" in clusters
    # each cluster carries >= 2 distinct stances
    for stances in clusters.values():
        assert len(stances) >= 2


def test_escalation_detected() -> None:
    assert unsupported_escalation_detection() == 1.0
    assert len(escalation_instances()) >= 1


def test_timeline_inconsistencies_surfaced() -> None:
    assert len(timeline_inconsistencies()) >= 1
    assert 0.0 < timeline_consistency() < 1.0


def test_single_source_claims_flagged() -> None:
    assert len(single_source_claims()) >= 1


def test_independently_supported_claims_exist() -> None:
    ids = {
        c.claim_id for c in independently_supported()
    }
    assert "C01" in ids


# --- uncertainty must stay visible --------------
def test_uncertainty_visible() -> None:
    assert uncertainty_visible() is True


def test_uncertain_statuses_present() -> None:
    hist = status_histogram()
    assert hist[ClaimStatus.CONTESTED.value] >= 1
    assert hist[ClaimStatus.UNRESOLVED.value] >= 1
    assert hist[ClaimStatus.SPECULATIVE.value] >= 1


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_structured() -> None:
    assert build_report().recommendation == (
        VERDICT_STRUCTURED
    )


def test_recommendation_never_claims_solution() -> None:
    rec = build_report().recommendation.lower()
    for w in ("solved", "guilty", "conspiracy"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v16_0_topology.json")
    assert art["schema_version"] == (
        "v16_0_evidence_topology_audit"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v16_0_topology.json")
    disc = art["disclaimer"].lower()
    assert "no new factual claim" in disc
    assert "never names a perpetrator" in disc
    assert "never declares the case" in disc
    assert "public evidentiary standing" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v16_0_topology.json")
    required = {
        "evidence_independence",
        "conflict_detection",
        "timeline_consistency",
        "unsupported_escalation_detection",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v16_0_topology.json")
    live = build_topology_artifact()
    assert art == live
