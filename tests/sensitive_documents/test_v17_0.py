"""v17.0 - Provenance & Document Topology tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.sensitive_documents import (
    CLAIM_TYPES, DOCUMENT_CLASSES, ENTITIES,
    ClaimType, build_report,
    build_topology_artifact, claims, documents,
    duplicate_detection, duplicate_doc_ids,
    entities_remain_neutral, lineage_quality,
    no_involvement_vocabulary, provenance_gaps,
    provenance_integrity, provenance_visibility,
    redundancy, source_independence,
    status_histogram,
)
from desi.sensitive_documents.report import (
    REPORT_VERDICTS, VERDICT_STRUCTURED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "sensitive_documents"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- closed vocab / no-guilt safety -------------
def test_claim_types_closed_set() -> None:
    assert CLAIM_TYPES == tuple(
        c.value for c in ClaimType
    )
    assert len(CLAIM_TYPES) == 8


def test_document_classes_count() -> None:
    assert len(DOCUMENT_CLASSES) == 8


def test_no_involvement_vocabulary() -> None:
    assert no_involvement_vocabulary() is True


def test_no_guilt_terms_in_any_vocab() -> None:
    forbidden = {
        "involved", "guilty", "perpetrator",
        "participant", "suspect", "culprit",
        "offender",
    }
    tokens = set()
    for v in (
        list(CLAIM_TYPES) + list(DOCUMENT_CLASSES)
        + list(REPORT_VERDICTS)
    ):
        tokens.update(re.split(r"[^a-z]+", v.lower()))
    assert not (tokens & forbidden)


def test_strongest_claim_is_document_presence() -> None:
    """The strongest claim type asserts only document
    presence - never a person's conduct."""
    from desi.sensitive_documents import type_rank
    strongest = max(CLAIM_TYPES, key=type_rank)
    assert strongest == (
        ClaimType.VERIFIED_DOCUMENT_PRESENCE.value
    )


def test_entities_remain_neutral() -> None:
    assert entities_remain_neutral() is True


def test_no_adopted_claim_asserts_conduct() -> None:
    """Every claim DESi treats as a document fact is
    presence/reference/association - never conduct.
    Claims of higher implication stay non-adopted
    (CLAIMED/CONTESTED/UNSUPPORTED/SPECULATIVE/
    UNRESOLVED)."""
    document_facts = {
        ClaimType.VERIFIED_DOCUMENT_PRESENCE.value,
        ClaimType.REFERENCED.value,
        ClaimType.CONTEXTUAL_ASSOCIATION.value,
    }
    for c in claims():
        if c.is_document_fact():
            assert c.claim_type in document_facts


def test_report_has_no_entity_verdict_field() -> None:
    d = build_report().to_dict()
    for forbidden in (
        "suspect_list", "guilt", "involved_entities",
        "blacklist", "perpetrators",
    ):
        assert forbidden not in d


# --- metrics ------------------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        provenance_integrity(), provenance_visibility(),
        duplicate_detection(), lineage_quality(),
        source_independence(), redundancy(),
    ):
        assert 0.0 <= m <= 1.0


def test_provenance_visibility_full() -> None:
    """DESi can see and label provenance for every
    document, gaps included."""
    assert provenance_visibility() == 1.0


def test_provenance_gaps_surfaced() -> None:
    assert len(provenance_gaps()) >= 1


def test_duplicates_detected() -> None:
    assert duplicate_detection() == 1.0
    assert len(duplicate_doc_ids()) >= 1


def test_contaminated_space_has_moderate_integrity() -> None:
    """Honest finding: provenance integrity is not
    high in a contaminated space."""
    assert 0.0 < provenance_integrity() < 0.90


def test_all_claim_types_exercised() -> None:
    hist = status_histogram()
    for t in CLAIM_TYPES:
        assert hist[t] >= 1


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


def test_recommendation_never_reveals_or_accuses() -> None:
    rec = build_report().recommendation.lower()
    for w in ("reveal", "guilty", "suspect", "expose"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v17_0_topology.json")
    assert art["schema_version"] == (
        "v17_0_provenance_document_topology"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v17_0_topology.json")
    disc = art["disclaimer"].lower()
    assert "synthetic and anonymised" in disc
    assert "no per-entity verdict" in disc
    assert "mention != involvement" in disc
    assert "no real content" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v17_0_topology.json")
    required = {
        "provenance_integrity",
        "duplicate_detection",
        "lineage_quality",
        "source_independence",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v17_0_topology.json")
    live = build_topology_artifact()
    assert art == live
