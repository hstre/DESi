"""Aufgaben 4 + 5 — consistency classifier."""
from __future__ import annotations

from desi.frame_tension import FrameConsistency, evaluate_consistency


def test_confirmed_when_inner_and_outer_match() -> None:
    v = evaluate_consistency(
        claim_id="c1",
        claim_text="Heat flow in joules per second.",
        inherited_context_text="Frame: thermodynamic",
    )
    assert v.consistency is FrameConsistency.CONFIRMED


def test_tension_when_pair_is_conflict_capable() -> None:
    v = evaluate_consistency(
        claim_id="c1",
        claim_text="Channel capacity in bits per use.",
        inherited_context_text="Frame: thermodynamic",
    )
    assert v.consistency is FrameConsistency.TENSION


def test_conflict_when_pair_is_not_conflict_capable() -> None:
    v = evaluate_consistency(
        claim_id="c1",
        claim_text="By modus ponens the syllogism is valid.",
        inherited_context_text="Frame: tool computable",
    )
    assert v.consistency is FrameConsistency.CONFLICT


def test_undecidable_when_no_signal_on_either_side() -> None:
    v = evaluate_consistency(
        claim_id="c1",
        claim_text="A neutral sentence.",
        inherited_context_text="Another neutral sentence.",
    )
    assert v.consistency is FrameConsistency.UNDECIDABLE


def test_undecidable_when_inner_internally_conflicted() -> None:
    # "entropy" alone fires both thermo and info buckets; no
    # explicit marker → inner side cannot resolve to one frame.
    v = evaluate_consistency(
        claim_id="c1",
        claim_text="Entropy increases over time.",
        inherited_context_text="Frame: information-theoretic",
    )
    assert v.consistency is FrameConsistency.UNDECIDABLE


def test_undecidable_when_only_one_side_has_signal() -> None:
    v = evaluate_consistency(
        claim_id="c1",
        claim_text="Heat flow in joules per second.",
        inherited_context_text="A bland sentence.",
    )
    assert v.consistency is FrameConsistency.UNDECIDABLE


def test_verdict_carries_buckets() -> None:
    v = evaluate_consistency(
        claim_id="c1",
        claim_text="Heat flow in joules per second.",
        inherited_context_text="Frame: information-theoretic",
    )
    d = v.to_dict()
    assert "inner" in d and "outer" in d and "consistency" in d
    assert "buckets" in d["inner"]
    assert "buckets" in d["outer"]
