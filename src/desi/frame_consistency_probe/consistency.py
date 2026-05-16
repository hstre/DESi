"""Aufgaben 4 + 5 — consistency score and FrameConsistency classifier."""
from __future__ import annotations

from dataclasses import dataclass

from ..frames import FrameKind
from .enums import FrameConsistency


# Pairs whose semantics overlap enough that an outer/inner mismatch
# is *tension* (worth flagging) rather than full *contradiction*.
# Stored canonically: each frozenset {A, B} appears once.
_CONFLICT_CAPABLE_PAIRS: frozenset[frozenset[FrameKind]] = frozenset({
    frozenset({FrameKind.THERMODYNAMIC,
               FrameKind.INFORMATION_THEORETIC}),  # entropy polysemy
    frozenset({FrameKind.INFORMATION_THEORETIC,
               FrameKind.TOOL_COMPUTABLE}),         # compute the entropy
    frozenset({FrameKind.FORMAL_LOGIC,
               FrameKind.EMPIRICAL_CAUSAL}),        # syllogism vs cause
    frozenset({FrameKind.AUTHORITY_SPEECH,
               FrameKind.EMPIRICAL_CAUSAL}),        # reported cause-claim
    frozenset({FrameKind.METAPHORICAL,
               FrameKind.INFORMATION_THEORETIC}),   # poetic info-tropes
    frozenset({FrameKind.METAPHORICAL,
               FrameKind.THERMODYNAMIC}),           # "heat" as metaphor
})


def consistency_score(
    inner: FrameKind | None, outer: FrameKind | None,
) -> float:
    """Aufgabe 4 — closed mapping. No learned weights.

    * 1.0 — inner == outer
    * 0.5 — inner ≠ outer and the pair is conflict-capable
    * 0.0 — inner ≠ outer and the pair is a hard contradiction
    """
    if inner is None or outer is None:
        # Undecidable cases sit outside the [0,1] mapping; the
        # classifier handles them separately.
        return 0.0
    if inner is outer:
        return 1.0
    pair = frozenset({inner, outer})
    if pair in _CONFLICT_CAPABLE_PAIRS:
        return 0.5
    return 0.0


def classify(
    inner: FrameKind | None, outer: FrameKind | None,
) -> FrameConsistency:
    """Aufgabe 5 — closed-enum classifier."""
    if inner is None and outer is None:
        return FrameConsistency.FRAME_UNDECIDABLE
    if inner is None or outer is None:
        return FrameConsistency.FRAME_UNDECIDABLE
    if inner is outer:
        return FrameConsistency.FRAME_CONFIRMED
    pair = frozenset({inner, outer})
    if pair in _CONFLICT_CAPABLE_PAIRS:
        return FrameConsistency.FRAME_TENSION
    return FrameConsistency.FRAME_CONFLICT


@dataclass(frozen=True)
class ConsistencyVerdict:
    inner_frame: FrameKind | None
    outer_frame: FrameKind | None
    score: float
    classification: FrameConsistency

    def to_dict(self) -> dict[str, object]:
        return {
            "inner_frame": (
                self.inner_frame.value if self.inner_frame else None
            ),
            "outer_frame": (
                self.outer_frame.value if self.outer_frame else None
            ),
            "score": self.score,
            "classification": self.classification.value,
        }


def evaluate(
    inner: FrameKind | None, outer: FrameKind | None,
) -> ConsistencyVerdict:
    return ConsistencyVerdict(
        inner_frame=inner,
        outer_frame=outer,
        score=consistency_score(inner, outer),
        classification=classify(inner, outer),
    )


__all__ = [
    "ConsistencyVerdict",
    "classify",
    "consistency_score",
    "evaluate",
]
