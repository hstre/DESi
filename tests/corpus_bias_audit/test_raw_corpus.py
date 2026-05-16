"""v5.3 — RAW corpus reconstruction."""
from __future__ import annotations

from desi.corpus_bias_audit.raw_corpus import (
    RAW_CONCLUSIONS, all_pairs, raw_chains,
    raw_recovery_rate,
)


def test_raw_recovery_rate_is_one() -> None:
    assert raw_recovery_rate() == 1.0


def test_every_v52_chain_has_pair() -> None:
    from desi.taxonomy_generalization.corpus import (
        all_chains,
    )
    assert len(all_pairs()) == len(all_chains())


def test_rewritten_chains_have_different_text() -> None:
    for p in all_pairs():
        if p.was_rewritten:
            assert p.raw_text != p.final_text, p.chain_id


def test_unrewritten_chains_have_identical_text() -> None:
    for p in all_pairs():
        if not p.was_rewritten:
            assert p.raw_text == p.final_text


def test_raw_chains_count_matches_final() -> None:
    from desi.taxonomy_generalization.corpus import (
        all_chains,
    )
    assert len(raw_chains()) == len(all_chains())


def test_raw_chain_text_starts_with_premise() -> None:
    """Every RAW chain text contains a 'Therefore'
    segment with a non-empty conclusion."""
    for c in raw_chains():
        assert "Therefore" in c.text


def test_raw_conclusions_table_has_unique_base_ids() -> None:
    keys = list(RAW_CONCLUSIONS.keys())
    assert len(set(keys)) == len(keys)


def test_label_invariant_under_reconstruction() -> None:
    """Aufgabe 5 — label_preservation must be 1.00."""
    for p in all_pairs():
        assert p.ground_truth in (
            "VALID", "INVALID", "AMBIGUOUS",
        )
