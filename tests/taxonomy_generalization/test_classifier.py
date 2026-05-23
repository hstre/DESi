"""v5.2 — classifier behaviour."""
from __future__ import annotations

from collections import Counter

from desi.taxonomy_generalization.classifier import (
    classify_all, classify_chain,
)
from desi.taxonomy_generalization.corpus import all_chains


def _CANONICAL():
    return {
        "MT_AMBIGUITY_DECISIVENESS",
        "MT_AUDIT_OVER_BLOCK",
        "MT_AUDIT_OVER_SUPPORT",
        "MT_MODAL_ASYMMETRY",
        "MT_NEGATION_ASYMMETRY",
        "MT_NOVEL_ENTITY",
        "MT_OVERLAP_LOOP",
        "MT_UNIVERSAL_LEAP",
        "UNKNOWN",
    }


def test_every_chain_gets_a_class_or_unknown() -> None:
    allowed = _CANONICAL()
    for r in classify_all(all_chains()):
        assert r.assigned_class in allowed


def test_classification_is_deterministic() -> None:
    a = classify_all(all_chains())
    b = classify_all(all_chains())
    assert tuple(
        (r.chain_id, r.assigned_class, r.confidence)
        for r in a
    ) == tuple(
        (r.chain_id, r.assigned_class, r.confidence)
        for r in b
    )


def test_no_new_taxonomy_class_emitted() -> None:
    results = classify_all(all_chains())
    classes = {r.assigned_class for r in results}
    new = classes - _CANONICAL()
    assert new == set(), new


def test_every_invalid_chain_classified_into_mt_or_unknown() -> None:
    """Aufgabe 5 directive: every INVALID chain must map
    to one of the 8 MT_* classes or UNKNOWN."""
    invalid = [
        r for r in classify_all(all_chains())
        if r.ground_truth == "INVALID"
    ]
    allowed = _CANONICAL()
    for r in invalid:
        assert r.assigned_class in allowed


def test_confidence_in_unit_interval() -> None:
    for r in classify_all(all_chains()):
        assert 0.0 <= r.confidence <= 1.0


def test_classifier_preserves_chain_metadata() -> None:
    chains = all_chains()
    by_id = {c.chain_id: c for c in chains}
    for r in classify_all(chains):
        c = by_id[r.chain_id]
        assert r.domain == c.domain
        assert r.ground_truth == c.ground_truth
