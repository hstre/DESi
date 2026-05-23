"""v27.0 - Claim Harvester Topology tests."""
from __future__ import annotations

import json
import pathlib

from desi.research_harvester import (
    CLAIM_CLASSES, SOURCES, TOPIC_AREAS, Claim, ClaimClass,
    all_claims, build_report, build_topology_artifact, by_id,
    claim_extraction_consistency, claims_by_class, claims_of,
    is_claim_class, limitation_visibility,
    open_question_visibility, paper_ids, papers,
    provenance_integrity, replay_stability,
)
from desi.research_harvester.report import (
    REPORT_VERDICTS, VERDICT_STRUCTURED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "research_harvester"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- closed taxonomy ----------------------------
def test_claim_classes_closed() -> None:
    assert CLAIM_CLASSES == tuple(c.value for c in ClaimClass)
    assert len(CLAIM_CLASSES) == 8


def test_all_eight_classes_present_in_corpus() -> None:
    for k in CLAIM_CLASSES:
        assert claims_by_class(k), f"no claims of class {k}"


def test_claim_rejects_unknown_class() -> None:
    try:
        Claim("X", "P", "NOT_A_CLASS", "text")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


# --- corpus integrity ---------------------------
def test_one_real_anchor_rest_synthetic() -> None:
    reals = [p for p in papers() if not p.metadata.is_synthetic]
    assert len(reals) == 1
    assert reals[0].paper_id == "arXiv:2501.14176"
    # every synthetic paper is clearly labelled
    for p in papers():
        if p.metadata.is_synthetic:
            assert "synthetic" in p.metadata.title.lower()


def test_categories_within_topic_areas() -> None:
    for p in papers():
        for c in p.metadata.categories:
            assert c in TOPIC_AREAS
        assert p.metadata.source in SOURCES


# --- claim extraction ---------------------------
def test_claim_extraction_consistency_full() -> None:
    assert claim_extraction_consistency() == 1.0


def test_every_claim_well_formed_and_anchored() -> None:
    ids = set(paper_ids())
    for c in all_claims():
        assert c.is_well_formed()
        assert c.paper_id in ids
        assert is_claim_class(c.claim_class)


def test_claims_of_resolves() -> None:
    for pid in paper_ids():
        assert claims_of(pid) == by_id(pid).claims


# --- limitations / open questions ---------------
def test_limitation_visibility_full() -> None:
    assert limitation_visibility() == 1.0


def test_open_question_visibility_full() -> None:
    assert open_question_visibility() == 1.0


def test_every_paper_has_limitation_and_open_question() -> None:
    for p in papers():
        assert p.limitations()
        assert p.open_questions()


# --- provenance ---------------------------------
def test_provenance_integrity_full() -> None:
    assert provenance_integrity() == 1.0


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        claim_extraction_consistency(), limitation_visibility(),
        open_question_visibility(), provenance_integrity(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- no ranking / scoring (epistemic neutrality) -
def test_report_carries_no_ranking_fields() -> None:
    d = build_report().to_dict()
    forbidden_keys = {
        "score", "rank", "ranking", "impact", "best",
        "quality", "winner",
    }
    assert forbidden_keys.isdisjoint(set(d.keys()))


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_structured() -> None:
    assert build_report().recommendation == VERDICT_STRUCTURED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v27_0_topology.json")
    assert art["schema_version"] == (
        "v27_0_claim_harvester_topology"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v27_0_topology.json")
    disc = art["disclaimer"].lower()
    assert "temporary epistemic state" in disc
    assert "does not rank" in disc
    assert "fabricated real citation" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v27_0_topology.json")
    required = {
        "claim_extraction_consistency", "limitation_visibility",
        "open_question_visibility", "provenance_integrity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v27_0_topology.json")
    live = build_topology_artifact()
    assert art == live
