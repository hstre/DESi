"""v23.4 - Final Follow-Up Verdict tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.scientific_rendering import FORBIDDEN_TERMS, forbidden_hits
from desi.icrl_followup_verdict import (
    FOLLOWUP_CLASSES, GATE_PASS_STATEMENT, FollowupClass,
    aggregate, build_followup_verdict_artifact, build_go_no_go,
    build_paper_v2, build_report, class_meaning, class_rank,
    classify_corpus, followup_forbidden_hits, gate_conditions,
    gate_failing_conditions, gate_passes_all, is_acceptable,
    technical_grounding,
)
from desi.icrl_followup_verdict.report import (
    REPORT_VERDICTS, VERDICT_GROUNDED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "icrl_followup"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert FOLLOWUP_CLASSES == tuple(
        c.value for c in FollowupClass
    )
    assert len(FOLLOWUP_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in FOLLOWUP_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(FollowupClass.A_DIRECTLY_RELEVANT.value) > (
        class_rank(FollowupClass.E_HYPE_INFLATED.value)
    )


def test_acceptable_classes() -> None:
    assert is_acceptable(
        FollowupClass.A_DIRECTLY_RELEVANT.value
    )
    assert is_acceptable(
        FollowupClass.C_EXPLORATORY_BUT_GROUNDED.value
    )
    assert not is_acceptable(
        FollowupClass.D_DISCONNECTED.value
    )
    assert not is_acceptable(
        FollowupClass.E_HYPE_INFLATED.value
    )


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["paper_alignment"].value >= 0.90
    assert by["result_traceability"].value >= 0.90
    assert by["technical_grounding"].value >= 0.90
    assert by["claim_conservatism"].value >= 0.90
    assert by["author_relevance"].value >= 0.90
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "ohne Hype oder" in r.gate_statement


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.paper_alignment, m.result_traceability,
        m.technical_grounding, m.claim_conservatism,
        m.author_relevance, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


def test_technical_grounding_full() -> None:
    assert technical_grounding() >= 0.90


# --- classification -----------------------------
def test_corpus_class_directly_relevant() -> None:
    assert classify_corpus() == (
        FollowupClass.A_DIRECTLY_RELEVANT.value
    )


def test_corpus_not_disconnected_or_inflated() -> None:
    bad = {
        FollowupClass.D_DISCONNECTED.value,
        FollowupClass.E_HYPE_INFLATED.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in FOLLOWUP_CLASSES:
        assert class_meaning(c).strip()


# --- the hard governance rule -------------------
def test_followup_has_no_forbidden_terms() -> None:
    assert followup_forbidden_hits() == ()


def test_paper_v2_has_no_forbidden_terms() -> None:
    paper = build_paper_v2()
    assert forbidden_hits(paper) == ()
    low = paper.lower()
    for term in FORBIDDEN_TERMS:
        t = term.lower()
        if " " in t or "-" in t:
            assert t not in low
        else:
            assert not re.search(rf"\b{re.escape(t)}\b", low)


# Note: the go/no-go meta-document deliberately names the
# forbidden terms when stating the governance rule (e.g.
# "Kein AGI-Manifest"), so it is exempt from the hard rule -
# the rule applies to the deliverable paper, checked above.


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_grounded() -> None:
    assert build_report().recommendation == VERDICT_GROUNDED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v23_4_followup_verdict.json")
    assert art["schema_version"] == (
        "v23_4_final_followup_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v23_4_followup_verdict.json")
    disc = art["disclaimer"].lower()
    assert "complementary" in disc
    assert "not a replacement" in disc
    assert "sandbox" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v23_4_followup_verdict.json")
    metrics = art["metrics"]
    required = {
        "paper_alignment", "result_traceability",
        "technical_grounding", "claim_conservatism",
        "author_relevance", "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v23_4_followup_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "FOLLOWUP_DIRECTLY_RELEVANT_GROUNDED"
    )
    assert art["classification"] == "directly_relevant"


def test_artifact_full_matches_live_build() -> None:
    art = _load("v23_4_followup_verdict.json")
    live = build_followup_verdict_artifact()
    assert art == live


# --- deliverable documents ----------------------
def test_go_no_go_document_present() -> None:
    doc = _read("desi_followup_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert "Section 4.6" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_refuses_manifesto() -> None:
    doc = _read("desi_followup_go_no_go.md")
    assert "Kein AGI-Manifest" in doc
    assert "Keine Superintelligenz" in doc


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_followup_go_no_go.md")
    assert doc == build_go_no_go()


def test_paper_v2_present_and_anchored() -> None:
    paper = _read("draft_exploration_governance_paper_v2.md")
    assert "Section 4.6" in paper
    assert "complementary" in paper.lower()
    assert "synthetic" in paper.lower()
    assert paper == build_paper_v2()
