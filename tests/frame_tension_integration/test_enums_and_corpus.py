"""Aufgaben 2 + 3 — closed enums + corpus assembly."""
from __future__ import annotations

from desi.frame_tension_integration.corpus import (
    build_corpus,
    corpus_summary,
)
from desi.frame_tension_integration.enums import (
    CorpusOrigin,
    InsertionPoint,
)


def test_insertion_point_has_four_values() -> None:
    assert len(list(InsertionPoint)) == 4


def test_insertion_point_values() -> None:
    assert {p.value for p in InsertionPoint} == {
        "pre_spl",
        "post_spl_pre_frame",
        "post_frame_pre_routing",
        "post_routing",
    }


def test_corpus_origin_has_four_values() -> None:
    assert len(list(CorpusOrigin)) == 4


def test_corpus_total_meets_minimum() -> None:
    assert len(build_corpus()) >= 80


def test_corpus_has_at_least_twenty_adversarial() -> None:
    s = corpus_summary()
    assert s["adversarial"] >= 20


def test_corpus_pulls_from_all_four_origins() -> None:
    s = corpus_summary()
    assert set(s["by_origin"]) == {o.value for o in CorpusOrigin}
    for n in s["by_origin"].values():
        assert n > 0


def test_corpus_case_ids_unique() -> None:
    cs = build_corpus()
    ids = [c.case_id for c in cs]
    assert len(ids) == len(set(ids))


def test_corpus_is_deterministic() -> None:
    a = [c.to_dict() for c in build_corpus()]
    b = [c.to_dict() for c in build_corpus()]
    assert a == b
