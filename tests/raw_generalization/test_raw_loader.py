"""v5.4 — RAW corpus loader."""
from __future__ import annotations

from collections import Counter

from desi.raw_generalization.raw_corpus_loader import (
    load_raw_chains, raw_chain_count,
)


def test_raw_corpus_size_matches_artifact() -> None:
    assert len(load_raw_chains()) == raw_chain_count()


def test_raw_corpus_is_540_chains() -> None:
    assert len(load_raw_chains()) == 540


def test_raw_corpus_balanced_labels() -> None:
    counts = Counter(c.ground_truth for c in load_raw_chains())
    assert counts["VALID"] == 180
    assert counts["INVALID"] == 180
    assert counts["AMBIGUOUS"] == 180


def test_raw_corpus_five_domains() -> None:
    domains = {c.domain for c in load_raw_chains()}
    assert len(domains) == 5


def test_raw_corpus_chain_ids_unique() -> None:
    ids = [c.chain_id for c in load_raw_chains()]
    assert len(set(ids)) == len(ids)


def test_raw_corpus_differs_from_v52_for_rewritten_chains() -> None:
    """The RAW corpus must contain the *pre-edit*
    conclusions: at least one chain's text differs from
    its v5.2 final form."""
    from desi.taxonomy_generalization.corpus import (
        all_chains as v52_chains,
    )
    raw = {c.chain_id: c.text for c in load_raw_chains()}
    diff = sum(
        1 for c in v52_chains() if raw[c.chain_id] != c.text
    )
    assert diff > 0
