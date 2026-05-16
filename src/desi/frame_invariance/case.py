"""Paraphrase-group schema for the v3.5 frame-invariance audit.

Each :class:`ParaphraseGroup` carries a canonical text plus four or
more hand-written paraphrases that *should* yield the same frame.
``forbidden_frames`` is the closed set of frames the detector must
**not** pick on any paraphrase; ``expected_conflict_allowed`` is
True for groups where the v3.4 detector legitimately surfaces a
``FRAME_CONFLICT`` (e.g. bare 'entropy').
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..frames import FrameKind


class FrameInvarianceFailure(str, Enum):
    """Closed taxonomy of failure modes — Aufgabe 5."""

    NONE = "none"
    FRAME_DRIFT = "frame_drift"
    FRAME_UNDECLARED = "frame_undeclared"
    FRAME_CONFLICT_UNEXPECTED = "frame_conflict_unexpected"
    FORBIDDEN_FRAME_HIT = "forbidden_frame_hit"
    PIPELINE_MISMATCH = "pipeline_mismatch"


@dataclass(frozen=True)
class ParaphraseGroup:
    """One canonical statement plus paraphrases."""

    group_id: str
    expected_frame: FrameKind
    forbidden_frames: tuple[FrameKind, ...]
    expected_conflict_allowed: bool
    canonical_text: str
    paraphrases: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.paraphrases) < 4:
            raise ValueError(
                f"{self.group_id}: paraphrases must contain >= 4 entries"
            )

    def all_texts(self) -> tuple[str, ...]:
        return (self.canonical_text,) + self.paraphrases

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "expected_frame": self.expected_frame.value,
            "forbidden_frames": [f.value for f in self.forbidden_frames],
            "expected_conflict_allowed": self.expected_conflict_allowed,
            "canonical_text": self.canonical_text,
            "paraphrases": list(self.paraphrases),
        }


@dataclass(frozen=True)
class FrameInvarianceResult:
    """One paraphrase observation (Aufgabe 3)."""

    case_id: str
    group_id: str
    text: str
    expected_frame: FrameKind
    detected_frame: FrameKind
    state: str
    compatible: bool
    allowed_pipeline: tuple[str, ...]
    blocked_pipeline: tuple[str, ...]
    invariant_with_group: bool
    failure: FrameInvarianceFailure
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "group_id": self.group_id,
            "text": self.text,
            "expected_frame": self.expected_frame.value,
            "detected_frame": self.detected_frame.value,
            "state": self.state,
            "compatible": self.compatible,
            "allowed_pipeline": list(self.allowed_pipeline),
            "blocked_pipeline": list(self.blocked_pipeline),
            "invariant_with_group": self.invariant_with_group,
            "failure": self.failure.value,
            "replay_hash": self.replay_hash,
        }


__all__ = [
    "FrameInvarianceFailure",
    "FrameInvarianceResult",
    "ParaphraseGroup",
]
