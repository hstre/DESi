"""Closed enums for v3.9 — exhaustive."""
from __future__ import annotations

from desi.frame_consistency_probe.enums import CorpusGroup, FrameConsistency


def test_frame_consistency_has_four_values() -> None:
    assert len(list(FrameConsistency)) == 4


def test_frame_consistency_values() -> None:
    assert {f.value for f in FrameConsistency} == {
        "frame_confirmed",
        "frame_tension",
        "frame_conflict",
        "frame_undecidable",
    }


def test_corpus_group_has_three_partitions() -> None:
    assert len(list(CorpusGroup)) == 3


def test_corpus_group_values() -> None:
    assert {g.value for g in CorpusGroup} == {
        "outer_eq_inner",
        "outer_neq_inner",
        "outer_ambiguous",
    }
