"""Aufgabe 3 + 9 — external corpus + contamination floor."""
from __future__ import annotations

from collections import Counter

from desi.external_probe import (
    Domain,
    GroundTruth,
    all_chains,
    check,
    transitions_per_chain,
)


def test_chain_count_meets_minimum() -> None:
    assert len(all_chains()) >= 800


def test_transition_count_meets_minimum() -> None:
    total = len(all_chains()) * transitions_per_chain()
    assert total >= 3200


def test_document_count_meets_minimum() -> None:
    # Each chain entry is a document in v4.0's accounting.
    assert len(all_chains()) >= 250


def test_five_required_domains_present() -> None:
    seen = {c.domain for c in all_chains()}
    for required in (
        Domain.D1_SCIENTIFIC_ABSTRACTS,
        Domain.D2_LEGAL_REASONING,
        Domain.D3_MEDICAL_CASE_REPORTS,
        Domain.D4_MATHEMATICAL_PROOFS,
        Domain.D5_ADVERSARIAL_REAL_WORLD,
    ):
        assert required in seen, required.value


def test_negative_controls_count_at_least_100() -> None:
    nc = sum(
        1 for c in all_chains()
        if c.domain is Domain.NEGATIVE_CONTROL
    )
    assert nc >= 100


def test_ground_truth_uses_only_closed_enum() -> None:
    for c in all_chains():
        assert c.ground_truth in (
            GroundTruth.VALID,
            GroundTruth.INVALID,
            GroundTruth.UNDECIDABLE,
        )


def test_contamination_zero_exact_overlap() -> None:
    r = check(all_chains())
    assert r.exact_overlap_count == 0


def test_contamination_zero_semantic_overlap() -> None:
    r = check(all_chains())
    assert r.semantic_overlap_count == 0


def test_chains_are_deterministic() -> None:
    a = [c.to_dict() for c in all_chains()]
    b = [c.to_dict() for c in all_chains()]
    assert a == b


def test_corpus_balance_per_real_domain() -> None:
    # Every real domain must contribute at least 100 chains so
    # per-domain metrics are statistically meaningful.
    counts = Counter(c.domain for c in all_chains())
    for d in (
        Domain.D1_SCIENTIFIC_ABSTRACTS,
        Domain.D2_LEGAL_REASONING,
        Domain.D3_MEDICAL_CASE_REPORTS,
        Domain.D4_MATHEMATICAL_PROOFS,
        Domain.D5_ADVERSARIAL_REAL_WORLD,
    ):
        assert counts[d] >= 100, (
            f"{d.value} has only {counts[d]} chains"
        )
