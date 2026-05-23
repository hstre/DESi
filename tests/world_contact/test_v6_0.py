"""v6.0 - scientific paper audit tests."""
from __future__ import annotations

import json
import pathlib

from desi.world_contact.audit import (
    blindness_pools_added,
    bridge_audit_coverage,
    claim_extraction_accuracy,
    frame_diversity,
    unsupported_leap_detection,
)
from desi.world_contact.claim_extractor import (
    ExtractedKind, all_scores,
    corpus_extractions, extract,
    hallucination_rate,
)
from desi.world_contact.paper_reader import (
    VENUES, Venue, corpus, venue_counts,
)
from desi.world_contact.report import (
    build_paper_audit_artifact, build_report,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "world_contact"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_venues_closed_set() -> None:
    assert VENUES == tuple(
        v.value for v in Venue
    )
    assert len(VENUES) == 5


def test_corpus_spans_all_venues() -> None:
    assert set(venue_counts().keys()) == set(
        VENUES,
    )


def test_corpus_count_at_least_five() -> None:
    assert len(corpus()) >= 5


def test_extract_is_deterministic() -> None:
    p = corpus()[0]
    a = tuple(
        u.to_dict() for u in extract(p)
    )
    b = tuple(
        u.to_dict() for u in extract(p)
    )
    assert a == b


def test_extract_kinds_are_closed() -> None:
    allowed = {k.value for k in ExtractedKind}
    for _, units in corpus_extractions():
        for u in units:
            assert u.kind in allowed


def test_hallucination_rate_is_zero() -> None:
    """Pflichtfrage 5: entstehen
    Halluzinationen? NEIN - by construction
    every extracted sentence is a slice of the
    abstract."""
    assert hallucination_rate() == 0.0


def test_extracted_sentences_in_abstract() -> None:
    """Verify the structural invariant the
    hallucination metric measures."""
    for p, units in corpus_extractions():
        haystack = (
            p.abstract.lower()
            .replace(" - ", " — ")
        )
        for u in units:
            assert (
                u.sentence.lower().rstrip(".")
                in haystack
            )


def test_claim_extraction_accuracy_high() -> (
    None
):
    """Pflichtfrage 1: kann DESi reale Papers
    zerlegen?"""
    assert (
        claim_extraction_accuracy() >= 0.50
    )


def test_unsupported_leap_detection_full() -> (
    None
):
    """Every ground-truth leap must be flagged."""
    assert unsupported_leap_detection() == 1.0


def test_bridge_audit_coverage_full() -> None:
    """Every ground-truth bridge sentence must
    be classified as BRIDGE."""
    assert bridge_audit_coverage() == 1.0


def test_frame_diversity_positive() -> None:
    """Pflichtfrage 2: entstehen neue Frames?
    Multiple frame types across the corpus."""
    assert frame_diversity() > 0.0


def test_blindness_pools_added_count() -> None:
    """Pflichtfrage 3: entstehen neue Blindness
    Pools? Mindestens eine (Paper 6 BUG_REPORT
    + leap)."""
    assert blindness_pools_added() >= 1


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: bleibt Replay stabil?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PAPER_AUDIT_TRACTABLE",
        "PAPER_AUDIT_WEAK",
        "PAPER_AUDIT_HALLUCINATING",
        "PAPER_AUDIT_BRIDGE_BLIND",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_tractable() -> None:
    """Killerfrage: kann DESi echte Wissenschaft
    lesen, ohne Dinge zu erfinden?"""
    assert build_report().recommendation == (
        "PAPER_AUDIT_TRACTABLE"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v6_0_paper_audit.json")
    assert art["schema_version"] == (
        "v6_0_scientific_paper_audit"
    )
    assert art["paper_count"] == len(corpus())


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v6_0_paper_audit.json")
    required = {
        "claim_extraction_accuracy",
        "unsupported_leap_detection",
        "hallucination_rate",
        "frame_diversity",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v6_0_report.json")
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


def test_artifact_full_matches_live_build() -> None:
    art = _load("v6_0_paper_audit.json")
    live = build_paper_audit_artifact()
    assert art == live


def test_no_live_internet_imports() -> None:
    """The world_contact package must not import
    any network library; the directive forbids
    live internet."""
    import importlib
    forbidden = {
        "requests", "urllib3", "httpx",
        "aiohttp", "urllib.request",
    }
    pkg = importlib.import_module(
        "desi.world_contact",
    )
    assert not (
        set(dir(pkg)) & forbidden
    )


def test_score_paper_recall_high() -> None:
    """Mean per-paper recall on stated_claims
    must be high."""
    scores = all_scores()
    recalls = []
    for s in scores:
        if s.stated_total > 0:
            recalls.append(
                s.stated_hit / s.stated_total,
            )
    assert recalls
    assert sum(recalls) / len(recalls) >= 0.80
