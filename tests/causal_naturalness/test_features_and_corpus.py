"""Aufgaben 1 + 4 — feature extraction + NC bank shape."""
from __future__ import annotations

from desi.causal_link_typing.enums import CorpusSource
from desi.causal_naturalness import (
    ALL_NC_CHAINS,
    NCShape,
    NaturalnessVector,
    all_input_chains,
    compute_vector,
)
from desi.causal_link_typing.extractor import _sentences


def test_chain_count_meets_minimum() -> None:
    assert len(all_input_chains()) >= 300


def test_total_link_count_meets_minimum() -> None:
    total = sum(
        max(0, len(_sentences(c.text)) - 1)
        for c in all_input_chains()
    )
    assert total >= 1000


def test_negative_control_count_meets_minimum() -> None:
    assert len(ALL_NC_CHAINS) >= 50


def test_negative_controls_cover_every_shape() -> None:
    shapes = {c.shape.value for c in ALL_NC_CHAINS}
    assert shapes == {s.value for s in NCShape}


def test_feature_vector_has_eight_floats() -> None:
    for c in all_input_chains()[:5]:
        v = compute_vector(c.chain_id, c.text, c.corpus)
        assert isinstance(v, NaturalnessVector)
        assert len(v.feature_tuple()) == 8
        for x in v.feature_tuple():
            assert isinstance(x, float)


def test_feature_vector_is_deterministic() -> None:
    c = all_input_chains()[0]
    a = compute_vector(c.chain_id, c.text, c.corpus)
    b = compute_vector(c.chain_id, c.text, c.corpus)
    assert a.feature_tuple() == b.feature_tuple()


def test_corpus_includes_all_five_input_sources() -> None:
    seen = {c.corpus.value for c in all_input_chains()}
    assert CorpusSource.V23_MULTISTEP.value in seen
    assert CorpusSource.V314_HELDOUT.value in seen
    assert CorpusSource.V315_ADVERSARIAL.value in seen
    assert CorpusSource.V316_SUSPENDED.value in seen
