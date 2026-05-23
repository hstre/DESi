"""Extract the v3.5 failures into the v3.6 schema — Aufgabe 1.

Strict expectation: **exactly 30 failures**. The runner re-runs
the v3.5 :class:`FrameInvarianceRunner` (read-only) and filters
``failure != none``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..frame_invariance import (
    FrameInvarianceFailure,
    FrameInvarianceRunner,
)
from ..frame_invariance.cases import ALL_GROUPS
from ..frames import FrameKind


_FRAME_MARKER_PREFIX = "frame:"


@dataclass(frozen=True)
class FrameFailureRecord:
    """Aufgabe 1 — one extracted failure with the required nine
    descriptive fields."""

    case_id: str
    canonical_group_id: str
    expected_frame: FrameKind
    detected_frame: FrameKind
    failure_type: FrameInvarianceFailure
    text: str
    explicit_marker_present: bool
    paraphrase_variant: int     # 0 = canonical, 1..N = paraphrase
    canonical_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "canonical_group_id": self.canonical_group_id,
            "expected_frame": self.expected_frame.value,
            "detected_frame": self.detected_frame.value,
            "failure_type": self.failure_type.value,
            "text": self.text,
            "explicit_marker_present": self.explicit_marker_present,
            "paraphrase_variant": self.paraphrase_variant,
            "canonical_text": self.canonical_text,
        }


def _parse_variant(case_id: str) -> int:
    """``T01:p0`` → 0 (canonical), ``T01:p3`` → 3."""
    if ":" in case_id:
        suffix = case_id.split(":", 1)[1]
        if suffix.startswith("p"):
            try:
                return int(suffix[1:])
            except ValueError:
                return -1
    return -1


def extract_failures() -> tuple[FrameFailureRecord, ...]:
    canonical_by_group = {g.group_id: g.canonical_text for g in ALL_GROUPS}
    run = FrameInvarianceRunner().run()
    failures: list[FrameFailureRecord] = []
    for r in run.results:
        if r.failure is FrameInvarianceFailure.NONE:
            continue
        failures.append(FrameFailureRecord(
            case_id=r.case_id,
            canonical_group_id=r.group_id,
            expected_frame=r.expected_frame,
            detected_frame=r.detected_frame,
            failure_type=r.failure,
            text=r.text,
            explicit_marker_present=(
                _FRAME_MARKER_PREFIX in r.text.lower()
            ),
            paraphrase_variant=_parse_variant(r.case_id),
            canonical_text=canonical_by_group.get(r.group_id, ""),
        ))
    return tuple(failures)


__all__ = ["FrameFailureRecord", "extract_failures"]
