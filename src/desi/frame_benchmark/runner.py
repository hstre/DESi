"""FrameBenchmarkRunner — Aufgabe 8."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..frames import (
    FrameDeclaration,
    FrameDetector,
    FrameKind,
    check_compatibility,
)
from ..memory.claim import ClaimState
from .case import FrameBenchmarkCase
from .cases import ALL_FRAME_CASES


def _post_audit_state(
    declared_kind: FrameKind,
    fired_buckets: tuple[FrameKind, ...],
) -> ClaimState:
    if declared_kind is FrameKind.FRAME_UNDECLARED and len(fired_buckets) > 1:
        return ClaimState.FRAME_CONFLICT
    if declared_kind is FrameKind.FRAME_UNDECLARED:
        return ClaimState.FRAME_UNDECLARED
    return ClaimState.FRAME_DECLARED


@dataclass(frozen=True)
class FrameBenchmarkResult:
    case: FrameBenchmarkCase
    declaration: FrameDeclaration
    fired_buckets: tuple[FrameKind, ...]
    actual_state: ClaimState
    frame_correct: bool
    state_correct: bool
    pipeline_correct: bool

    @property
    def correct(self) -> bool:
        return (
            self.frame_correct
            and self.state_correct
            and self.pipeline_correct
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case.to_dict(),
            "declaration": self.declaration.to_dict(),
            "fired_buckets": [k.value for k in self.fired_buckets],
            "actual_state": self.actual_state.value,
            "frame_correct": self.frame_correct,
            "state_correct": self.state_correct,
            "pipeline_correct": self.pipeline_correct,
            "correct": self.correct,
        }


@dataclass(frozen=True)
class FrameBenchmarkRun:
    timestamp: datetime
    results: tuple[FrameBenchmarkResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
        }


class FrameBenchmarkRunner:
    def __init__(
        self,
        *,
        detector: FrameDetector | None = None,
    ) -> None:
        self._detector = detector or FrameDetector()

    def run(self) -> FrameBenchmarkRun:
        out: list[FrameBenchmarkResult] = []
        for case in ALL_FRAME_CASES:
            decl = self._detector.detect(
                claim_id=case.case_id, source_text=case.text,
            )
            fired = self._detector.detect_conflicting_buckets(case.text)
            actual_state = _post_audit_state(decl.frame_kind, fired)
            compat = check_compatibility(declared_frame=decl.frame_kind)
            frame_correct = decl.frame_kind is case.expected_frame
            state_correct = actual_state is case.expected_state
            pipeline_correct = (
                compat.allowed_pipeline == case.expected_allowed_pipeline
                and compat.blocked_pipeline == case.expected_blocked_pipeline
            )
            out.append(FrameBenchmarkResult(
                case=case,
                declaration=decl,
                fired_buckets=fired,
                actual_state=actual_state,
                frame_correct=frame_correct,
                state_correct=state_correct,
                pipeline_correct=pipeline_correct,
            ))
        return FrameBenchmarkRun(
            timestamp=datetime.now(timezone.utc),
            results=tuple(out),
        )


__all__ = [
    "FrameBenchmarkResult",
    "FrameBenchmarkRun",
    "FrameBenchmarkRunner",
]
