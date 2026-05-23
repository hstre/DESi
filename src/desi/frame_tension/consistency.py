"""Aufgaben 3 + 4 + 5 — FrameConsistency closed enum + classifier.

Runs the v3.4 ``FrameDetector`` twice — once on the claim text
(inner) and once on the inherited context text (outer) — and
reduces the two results to a closed-enum verdict. **No new
regex, no new rules, no LLM.**
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..frames import FrameDetector, FrameKind


class FrameConsistency(str, Enum):
    """Closed taxonomy — Aufgabe 3."""

    CONFIRMED   = "confirmed"
    TENSION     = "tension"
    CONFLICT    = "conflict"
    UNDECIDABLE = "undecidable"


# Frame pairs that are conflict-capable (semantic overlap exists,
# so a mismatch is a soft tension rather than a hard contradiction).
# These mirror the v3.9 audit's `_CONFLICT_CAPABLE_PAIRS` so the
# runtime layer agrees with the diagnostic that licensed it.
_CONFLICT_CAPABLE_PAIRS: frozenset[frozenset[FrameKind]] = frozenset({
    frozenset({FrameKind.THERMODYNAMIC,
               FrameKind.INFORMATION_THEORETIC}),
    frozenset({FrameKind.INFORMATION_THEORETIC,
               FrameKind.TOOL_COMPUTABLE}),
    frozenset({FrameKind.FORMAL_LOGIC,
               FrameKind.EMPIRICAL_CAUSAL}),
    frozenset({FrameKind.AUTHORITY_SPEECH,
               FrameKind.EMPIRICAL_CAUSAL}),
    frozenset({FrameKind.METAPHORICAL,
               FrameKind.INFORMATION_THEORETIC}),
    frozenset({FrameKind.METAPHORICAL,
               FrameKind.THERMODYNAMIC}),
})


@dataclass(frozen=True)
class FrameSide:
    """Inner or outer side of a consistency evaluation."""

    buckets: tuple[FrameKind, ...]   # buckets the detector fired
    declared: FrameKind | None       # single resolved frame, or None

    @property
    def has_signal(self) -> bool:
        return self.declared is not None or len(self.buckets) > 0

    @property
    def is_conflicted(self) -> bool:
        # The detector fired ≥ 2 distinct buckets and no explicit
        # marker chose between them — the side itself is internally
        # ambiguous.
        return self.declared is None and len(self.buckets) >= 2

    def to_dict(self) -> dict[str, object]:
        return {
            "buckets": [b.value for b in self.buckets],
            "declared": (
                self.declared.value if self.declared else None
            ),
        }


def _classify_side(
    detector: FrameDetector,
    *,
    claim_id: str,
    text: str,
) -> FrameSide:
    """Run the v3.4 detector and split the result into
    ``(buckets, declared)``.

    * If an explicit ``Frame:`` marker fired, the detector returns
      exactly one bucket; ``declared`` = that bucket.
    * If a single rule bucket fired, ``declared`` = that bucket.
    * If multiple rule buckets fired with no explicit marker,
      ``buckets`` carries them all and ``declared`` is ``None``.
    * If nothing fired, both are empty.
    """
    buckets = detector.detect_conflicting_buckets(text)
    if not buckets:
        return FrameSide(buckets=(), declared=None)
    decl = detector.detect(claim_id=claim_id, source_text=text)
    if decl.frame_kind is FrameKind.FRAME_UNDECLARED and len(buckets) > 1:
        # Internal conflict — keep buckets, no single resolved frame.
        return FrameSide(buckets=tuple(buckets), declared=None)
    return FrameSide(buckets=tuple(buckets), declared=decl.frame_kind)


@dataclass(frozen=True)
class ConsistencyVerdict:
    inner: FrameSide
    outer: FrameSide
    consistency: FrameConsistency

    def to_dict(self) -> dict[str, object]:
        return {
            "inner": self.inner.to_dict(),
            "outer": self.outer.to_dict(),
            "consistency": self.consistency.value,
        }


def _reduce(inner: FrameSide, outer: FrameSide) -> FrameConsistency:
    # Undecidable: no signal on at least one side.
    if not inner.has_signal or not outer.has_signal:
        return FrameConsistency.UNDECIDABLE

    # Either side is internally conflicted with no explicit marker
    # → UNDECIDABLE (we cannot ground a comparison).
    if inner.is_conflicted or outer.is_conflicted:
        return FrameConsistency.UNDECIDABLE

    # Both sides have a single declared frame.
    assert inner.declared is not None and outer.declared is not None
    if inner.declared is outer.declared:
        return FrameConsistency.CONFIRMED
    pair = frozenset({inner.declared, outer.declared})
    if pair in _CONFLICT_CAPABLE_PAIRS:
        return FrameConsistency.TENSION
    return FrameConsistency.CONFLICT


def evaluate_consistency(
    *,
    claim_id: str,
    claim_text: str,
    inherited_context_text: str,
    detector: FrameDetector | None = None,
) -> ConsistencyVerdict:
    """Aufgaben 4 + 5 — extract both sides and reduce."""
    det = detector if detector is not None else FrameDetector()
    inner = _classify_side(det, claim_id=claim_id, text=claim_text)
    outer = _classify_side(
        det, claim_id=claim_id, text=inherited_context_text,
    )
    return ConsistencyVerdict(
        inner=inner, outer=outer, consistency=_reduce(inner, outer),
    )


__all__ = [
    "ConsistencyVerdict",
    "FrameConsistency",
    "FrameSide",
    "evaluate_consistency",
]
