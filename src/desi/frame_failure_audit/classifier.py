"""Project each :class:`FrameFailureRecord` onto exactly one
:class:`FrameFailureClass` — Aufgabe 2.

Deterministic decision tree. The classifier does **not** propose
patches; it just labels.
"""
from __future__ import annotations

from ..frame_invariance import FrameInvarianceFailure
from ..frames import FrameDetector
from ..frames.detector import _EXPLICIT_MARKERS  # type: ignore[attr-defined]
from .classes import FrameFailureClass
from .extractor import FrameFailureRecord


# Polysemous tokens: appear in two or more rule buckets simultaneously.
_POLYSEMOUS_TOKENS: frozenset[str] = frozenset({
    "entropy",
})


def _has_polysemous_token(text: str) -> bool:
    low = text.lower()
    return any(t in low for t in _POLYSEMOUS_TOKENS)


def _has_explicit_marker(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in (
        "frame: thermodynamic", "frame: information",
        "frame: ontological", "frame: metaphorical",
        "frame: formal logic", "frame: empirical causal",
        "frame: authority", "frame: tool computable",
        "frame: undeclared",
    ))


def _canonical_carries_marker(canonical: str) -> bool:
    return _has_explicit_marker(canonical)


def classify(failure: FrameFailureRecord) -> FrameFailureClass:
    ftype = failure.failure_type

    # v3.5's FrameInvarianceFailure.PIPELINE_MISMATCH maps to
    # v3.6's FrameFailureClass.PIPELINE_ROUTING_MISMATCH.
    if ftype is FrameInvarianceFailure.PIPELINE_MISMATCH:
        return FrameFailureClass.PIPELINE_ROUTING_MISMATCH

    if ftype is FrameInvarianceFailure.FORBIDDEN_FRAME_HIT:
        return FrameFailureClass.TRUE_FRAME_SHIFT

    # Conflict-unexpected splits between polysemy and multi-signal.
    if ftype is FrameInvarianceFailure.FRAME_CONFLICT_UNEXPECTED:
        if _has_polysemous_token(failure.text):
            return FrameFailureClass.POLYSEMY_COLLISION
        return FrameFailureClass.MULTI_SIGNAL_CONFLICT

    # Undeclared splits between marker-dropout and synonym-gap.
    if ftype is FrameInvarianceFailure.FRAME_UNDECLARED:
        if (
            _canonical_carries_marker(failure.canonical_text)
            and not _has_explicit_marker(failure.text)
        ):
            return FrameFailureClass.MARKER_DROPOUT
        return FrameFailureClass.SYNONYM_GAP

    # FRAME_DRIFT: a different detected frame from a different
    # rule bucket → likely a real semantic shift the paraphrase
    # introduced. Classify conservatively as TRUE_FRAME_SHIFT.
    if ftype is FrameInvarianceFailure.FRAME_DRIFT:
        return FrameFailureClass.TRUE_FRAME_SHIFT

    return FrameFailureClass.UNKNOWN


def classify_all(
    failures: tuple[FrameFailureRecord, ...],
) -> dict[str, FrameFailureClass]:
    return {f.case_id: classify(f) for f in failures}


__all__ = ["classify", "classify_all"]
