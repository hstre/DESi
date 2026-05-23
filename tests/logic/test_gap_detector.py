"""Tests for v1.2 gap detector — classifying why no rule applies."""
from __future__ import annotations

from desi.logic import (
    GapKind,
    InferenceRule,
    PremiseExtractor,
    detect_gap,
)


def _ext() -> PremiseExtractor:
    return PremiseExtractor()


# ---------------------------------------------------------------------------
# No explicit chain
# ---------------------------------------------------------------------------


def test_no_therefore_yields_no_explicit_chain_gap() -> None:
    gap = detect_gap(_ext().extract("Water boils at 100C."))
    assert gap.kind == GapKind.NO_EXPLICIT_CHAIN


# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------


def test_authority_only_premise_yields_authority_gap() -> None:
    gap = detect_gap(
        _ext().extract("Professor X says quantum gravity is solved.")
    )
    assert gap.kind == GapKind.AUTHORITY_CLAIM


def test_authority_with_conclusion_repeating_claim_is_authority_gap() -> None:
    gap = detect_gap(_ext().extract(
        "Professor X says quantum gravity is solved. "
        "Therefore quantum gravity is solved."
    ))
    assert gap.kind == GapKind.AUTHORITY_CLAIM


# ---------------------------------------------------------------------------
# Missing bridge
# ---------------------------------------------------------------------------


def test_rain_to_wet_street_is_missing_bridge_gap() -> None:
    gap = detect_gap(_ext().extract(
        "It is raining. Therefore the street is wet."
    ))
    assert gap.kind == GapKind.MISSING_BRIDGE


def test_missing_bridge_carries_subject_predicate_hints() -> None:
    gap = detect_gap(_ext().extract(
        "It is raining. Therefore the street is wet."
    ))
    assert gap.bridge_subject  # non-empty
    assert gap.bridge_predicate  # non-empty


# ---------------------------------------------------------------------------
# Unreachable conclusion (e.g. invalid transitivity)
# ---------------------------------------------------------------------------


def test_invalid_transitivity_yields_unreachable_gap() -> None:
    gap = detect_gap(_ext().extract("a -> b. b -> c. Therefore a -> d."))
    assert gap.kind == GapKind.UNREACHABLE
    assert gap.candidate_rule == InferenceRule.TRANSITIVITY


# ---------------------------------------------------------------------------
# Gap shape
# ---------------------------------------------------------------------------


def test_gap_to_dict_contains_required_fields() -> None:
    gap = detect_gap(_ext().extract("a -> b. b -> c. Therefore a -> d."))
    d = gap.to_dict()
    for k in ("kind", "rationale", "candidate_rule",
              "bridge_subject", "bridge_predicate"):
        assert k in d


def test_authority_gap_does_not_propose_a_bridge_subject() -> None:
    gap = detect_gap(
        _ext().extract("Professor X says quantum gravity is solved.")
    )
    assert gap.bridge_subject == ""
    assert gap.bridge_predicate == ""
