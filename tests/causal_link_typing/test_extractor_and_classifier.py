"""Aufgaben 1 + 2 — extraction + classification."""
from __future__ import annotations

from desi.causal_link_typing import (
    LinkType,
    classify_link,
    extract_all_links,
    per_corpus_links,
)
from desi.causal_link_typing.extractor import Link, _sentences


def test_link_type_has_eight_values() -> None:
    assert len(list(LinkType)) == 8


def test_total_link_count_meets_minimum() -> None:
    links = extract_all_links()
    assert len(links) >= 250


def test_every_corpus_contributes_links() -> None:
    per = per_corpus_links()
    for name, links in per.items():
        assert len(links) > 0, name


def test_sentence_splitter_drops_therefore() -> None:
    sents = _sentences("A. B. Therefore C.")
    assert sents == ("A", "B", "C")


def test_classify_link_always_returns_a_value() -> None:
    # Classification coverage = 1.0 — every link gets a class.
    for link in extract_all_links():
        t = classify_link(link)
        assert isinstance(t, LinkType)


def test_authority_marker_wins_over_others() -> None:
    link = Link(
        chain_id="t", corpus=tuple(per_corpus_links().values())[0][0].corpus,
        index=0,
        source_text="The minister stated the policy",
        target_text="The court ruled",
    )
    assert classify_link(link) is LinkType.AUTHORITY_ASSERTION


def test_metaphor_marker_recognised() -> None:
    link = Link(
        chain_id="t",
        corpus=tuple(per_corpus_links().values())[0][0].corpus,
        index=0,
        source_text="Time is a river",
        target_text="Hours drift past the window",
    )
    assert classify_link(link) is LinkType.METAPHORICAL_ASSOCIATION


def test_tool_dependency_needs_numbers_on_both_ends() -> None:
    src = Link(
        chain_id="t",
        corpus=tuple(per_corpus_links().values())[0][0].corpus,
        index=0,
        source_text="Twelve dancers entered",
        target_text="Seven more arrived",
    )
    assert classify_link(src) is LinkType.TOOL_DEPENDENCY


def test_extraction_is_deterministic() -> None:
    a = [l.to_dict() for l in extract_all_links()]
    b = [l.to_dict() for l in extract_all_links()]
    assert a == b
