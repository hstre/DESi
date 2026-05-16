"""Aufgabe 1 — corpus partitioning and required fields."""
from __future__ import annotations

from desi.frame_consistency_probe.corpus import build_corpus, corpus_counts
from desi.frame_consistency_probe.enums import CorpusGroup


def test_corpus_total_meets_minimum() -> None:
    assert len(build_corpus()) >= 60


def test_each_group_has_at_least_twenty() -> None:
    counts = corpus_counts()
    for g in CorpusGroup:
        assert counts[g.value] >= 20, (
            f"group {g.value} has {counts[g.value]} cases, need >= 20"
        )


def test_corpus_case_ids_are_unique() -> None:
    ids = [c.case_id for c in build_corpus()]
    assert len(ids) == len(set(ids))


def test_required_fields_present() -> None:
    for c in build_corpus():
        for attr in (
            "case_id", "text", "outer_frame", "inner_frame",
            "ground_truth_relation",
        ):
            assert hasattr(c, attr), attr
        d = c.to_dict()
        for key in (
            "case_id", "text", "outer_frame", "inner_frame",
            "ground_truth_relation",
        ):
            assert key in d


def test_group_a_outer_equals_inner_by_construction() -> None:
    for c in build_corpus():
        if c.group is CorpusGroup.GROUP_A:
            assert c.outer_frame is c.inner_frame, c.case_id


def test_group_b_outer_differs_from_inner() -> None:
    for c in build_corpus():
        if c.group is CorpusGroup.GROUP_B:
            assert c.outer_frame is not c.inner_frame, c.case_id


def test_group_c_inner_is_none_by_design() -> None:
    # GROUP_C is the polysemy bucket; the inner is intentionally
    # ambiguous, encoded as ``None`` in the corpus annotations.
    for c in build_corpus():
        if c.group is CorpusGroup.GROUP_C:
            assert c.inner_frame is None, c.case_id


def test_corpus_is_deterministic() -> None:
    a = [c.to_dict() for c in build_corpus()]
    b = [c.to_dict() for c in build_corpus()]
    assert a == b
