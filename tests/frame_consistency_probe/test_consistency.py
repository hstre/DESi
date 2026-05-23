"""Aufgaben 4 + 5 — score mapping and classifier."""
from __future__ import annotations

from desi.frame_consistency_probe.consistency import (
    classify,
    consistency_score,
    evaluate,
)
from desi.frame_consistency_probe.enums import FrameConsistency
from desi.frames import FrameKind


def test_score_one_on_exact_match() -> None:
    assert consistency_score(
        FrameKind.THERMODYNAMIC, FrameKind.THERMODYNAMIC,
    ) == 1.0


def test_score_half_on_conflict_capable_pair() -> None:
    # Thermo/info is the canonical entropy polysemy pair — half.
    assert consistency_score(
        FrameKind.THERMODYNAMIC, FrameKind.INFORMATION_THEORETIC,
    ) == 0.5


def test_score_zero_on_contradiction() -> None:
    # Tool computable vs ontological distinguishability — no overlap.
    assert consistency_score(
        FrameKind.TOOL_COMPUTABLE,
        FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
    ) == 0.0


def test_classify_confirmed_on_match() -> None:
    assert classify(
        FrameKind.METAPHORICAL, FrameKind.METAPHORICAL,
    ) is FrameConsistency.FRAME_CONFIRMED


def test_classify_tension_on_conflict_capable_pair() -> None:
    assert classify(
        FrameKind.INFORMATION_THEORETIC, FrameKind.THERMODYNAMIC,
    ) is FrameConsistency.FRAME_TENSION


def test_classify_conflict_on_contradiction() -> None:
    assert classify(
        FrameKind.FORMAL_LOGIC, FrameKind.TOOL_COMPUTABLE,
    ) is FrameConsistency.FRAME_CONFLICT


def test_classify_undecidable_when_inner_missing() -> None:
    assert classify(
        None, FrameKind.METAPHORICAL,
    ) is FrameConsistency.FRAME_UNDECIDABLE


def test_classify_undecidable_when_outer_missing() -> None:
    assert classify(
        FrameKind.METAPHORICAL, None,
    ) is FrameConsistency.FRAME_UNDECIDABLE


def test_classify_undecidable_when_both_missing() -> None:
    assert classify(None, None) is FrameConsistency.FRAME_UNDECIDABLE


def test_evaluate_returns_bundle() -> None:
    v = evaluate(
        FrameKind.THERMODYNAMIC, FrameKind.INFORMATION_THEORETIC,
    )
    assert v.inner_frame is FrameKind.THERMODYNAMIC
    assert v.outer_frame is FrameKind.INFORMATION_THEORETIC
    assert v.score == 0.5
    assert v.classification is FrameConsistency.FRAME_TENSION
    assert v.to_dict()["classification"] == "frame_tension"
