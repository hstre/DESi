"""v23.3 - Author-Relevance Stress Test tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.icrl_followup_relevance import (
    DISMISSAL_CLASSES, HYPE, SPAM, author_interests,
    author_relevance, build_relevance_artifact, build_report,
    connection_notes, corpus_forbidden_hits,
    disconnected_claims, failing_probes, hype_probability,
    interest_topics, paper_connection_visibility,
    relevance_section, review_probes, simulated_verdict,
    spam_probability, unmet_interests,
)
from desi.icrl_followup_relevance.report import (
    REPORT_VERDICTS, VERDICT_RELEVANT,
)
from desi.icrl_followup_relevance.review_simulation import (
    VERDICT_RELEVANT as PROBE_RELEVANT,
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
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- relevance ----------------------------------
def test_author_relevance_full() -> None:
    assert author_relevance() >= 0.90
    assert unmet_interests() == ()


def test_all_author_interests_addressed() -> None:
    for i in author_interests():
        assert i.addressed


def test_interest_topics_cover_paper() -> None:
    joined = " ".join(interest_topics()).lower()
    assert "collapse" in joined
    assert "sparse" in joined
    assert "action space" in joined


# --- connection ---------------------------------
def test_paper_connection_visibility_full() -> None:
    assert paper_connection_visibility() >= 0.90
    assert disconnected_claims() == ()


def test_every_claim_connected() -> None:
    for n in connection_notes():
        assert n.connected
        assert n.anchors
        assert n.sprint_source


# --- spam / hype --------------------------------
def test_spam_probability_low() -> None:
    assert spam_probability() <= 0.10


def test_hype_probability_low() -> None:
    assert hype_probability() <= 0.10


def test_no_failing_probes() -> None:
    assert failing_probes() == ()


def test_simulated_verdict_engages() -> None:
    assert simulated_verdict() == PROBE_RELEVANT


def test_probe_dismissal_classes_closed() -> None:
    assert DISMISSAL_CLASSES == (SPAM, HYPE)
    for p in review_probes():
        assert p.dismissal_class in DISMISSAL_CLASSES


def test_both_dismissal_classes_probed() -> None:
    classes = {p.dismissal_class for p in review_probes()}
    assert classes == {SPAM, HYPE}


# --- governance rule ----------------------------
def test_no_forbidden_terms_in_corpus() -> None:
    assert corpus_forbidden_hits() == ()


def test_no_forbidden_terms_in_section() -> None:
    assert forbidden_hits(relevance_section()) == ()


# --- metrics in range ---------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        author_relevance(), paper_connection_visibility(),
        spam_probability(), hype_probability(),
    ):
        assert 0.0 <= m <= 1.0


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_relevant() -> None:
    assert build_report().recommendation == VERDICT_RELEVANT


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v23_3_relevance.json")
    assert art["schema_version"] == "v23_3_author_relevance"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v23_3_relevance.json")
    disc = art["disclaimer"].lower()
    assert "stress test" in disc or "stress-test" in disc
    assert "section 4.6" in disc
    assert "not a claim about" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v23_3_relevance.json")
    required = {
        "author_relevance", "paper_connection_visibility",
        "spam_probability", "hype_probability",
    }
    assert required.issubset(art.keys())


def test_artifact_low_dismissal() -> None:
    art = _load("v23_3_relevance.json")
    assert art["spam_probability"] <= 0.10
    assert art["hype_probability"] <= 0.10
    assert art["recommendation"] == (
        "DIRECTLY_RELEVANT_TO_AUTHOR"
    )


def test_artifact_full_matches_live_build() -> None:
    art = _load("v23_3_relevance.json")
    live = build_relevance_artifact()
    assert art == live
