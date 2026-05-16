"""FrameInvarianceRunner — Aufgabe 3.

Runs the real v3.4 :class:`FrameDetector` and
:func:`check_compatibility` over every canonical + paraphrase
text in the corpus. Reports per-case outcomes and a per-group
``invariant_with_group`` flag.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..frames import FrameDetector, FrameKind, check_compatibility
from ..memory.claim import ClaimState
from .case import (
    FrameInvarianceFailure,
    FrameInvarianceResult,
    ParaphraseGroup,
)
from .cases import ALL_GROUPS, NEGATIVE_CONTROLS, NegativeControl


def _result_replay_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _state_for(detected: FrameKind, fired_buckets: tuple[FrameKind, ...]) -> str:
    if detected is FrameKind.FRAME_UNDECLARED and len(fired_buckets) > 1:
        return ClaimState.FRAME_CONFLICT.value
    if detected is FrameKind.FRAME_UNDECLARED:
        return ClaimState.FRAME_UNDECLARED.value
    return ClaimState.FRAME_DECLARED.value


def _classify_failure(
    *,
    detected: FrameKind,
    expected: FrameKind,
    forbidden: tuple[FrameKind, ...],
    state: str,
    allowed_pipelines: tuple[str, ...],
    expected_conflict_allowed: bool,
) -> FrameInvarianceFailure:
    """Project (detected, expected, state) onto one closed failure."""
    if detected is expected:
        return FrameInvarianceFailure.NONE
    if detected in forbidden:
        return FrameInvarianceFailure.FORBIDDEN_FRAME_HIT
    if state == ClaimState.FRAME_CONFLICT.value:
        if expected_conflict_allowed:
            return FrameInvarianceFailure.NONE
        return FrameInvarianceFailure.FRAME_CONFLICT_UNEXPECTED
    if state == ClaimState.FRAME_UNDECLARED.value:
        return FrameInvarianceFailure.FRAME_UNDECLARED
    # The pipeline check is loose at this stage; only flag when
    # the expected frame's allowed pipeline is empty while the
    # detected frame's is non-empty (or vice versa).
    from ..frames import allowed_pipelines as _ap
    if _ap(expected) != allowed_pipelines:
        return FrameInvarianceFailure.PIPELINE_MISMATCH
    return FrameInvarianceFailure.FRAME_DRIFT


@dataclass(frozen=True)
class NegativeControlResult:
    nc_id: str
    text_a: str
    text_b: str
    detected_a: FrameKind
    detected_b: FrameKind
    expected_a: FrameKind
    expected_b: FrameKind
    distinguished: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "nc_id": self.nc_id,
            "text_a": self.text_a,
            "text_b": self.text_b,
            "detected_a": self.detected_a.value,
            "detected_b": self.detected_b.value,
            "expected_a": self.expected_a.value,
            "expected_b": self.expected_b.value,
            "distinguished": self.distinguished,
        }


@dataclass(frozen=True)
class FrameInvarianceRun:
    timestamp: datetime
    results: tuple[FrameInvarianceResult, ...]
    negative_controls: tuple[NegativeControlResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
            "negative_controls":
                [n.to_dict() for n in self.negative_controls],
        }


class FrameInvarianceRunner:
    def __init__(
        self,
        *,
        detector: FrameDetector | None = None,
        groups: tuple[ParaphraseGroup, ...] = ALL_GROUPS,
        negative_controls: tuple[NegativeControl, ...] = NEGATIVE_CONTROLS,
    ) -> None:
        self._detector = detector or FrameDetector()
        self._groups = groups
        self._negative_controls = negative_controls

    def run(self) -> FrameInvarianceRun:
        results: list[FrameInvarianceResult] = []
        for group in self._groups:
            # Detect on every paraphrase + the canonical.
            per_text: list[tuple[str, str, FrameKind, str,
                                  tuple[str, ...], tuple[str, ...],
                                  FrameInvarianceFailure, bool]] = []
            detected_kinds: list[FrameKind] = []
            for idx, text in enumerate(group.all_texts()):
                decl = self._detector.detect(
                    claim_id=f"{group.group_id}:p{idx}", source_text=text,
                )
                fired = self._detector.detect_conflicting_buckets(text)
                state = _state_for(decl.frame_kind, fired)
                compat = check_compatibility(declared_frame=decl.frame_kind)
                failure = _classify_failure(
                    detected=decl.frame_kind,
                    expected=group.expected_frame,
                    forbidden=group.forbidden_frames,
                    state=state,
                    allowed_pipelines=compat.allowed_pipeline,
                    expected_conflict_allowed=group.expected_conflict_allowed,
                )
                per_text.append((
                    f"{group.group_id}:p{idx}", text, decl.frame_kind,
                    state, compat.allowed_pipeline,
                    compat.blocked_pipeline, failure,
                    compat.compatible,
                ))
                detected_kinds.append(decl.frame_kind)

            # Invariance = all paraphrases agree with canonical
            invariant = all(
                k is detected_kinds[0] for k in detected_kinds[1:]
            )

            for case_id, text, kind, state, allowed, blocked, failure, compat in per_text:
                payload = {
                    "case_id": case_id,
                    "group_id": group.group_id,
                    "text": text,
                    "expected_frame": group.expected_frame.value,
                    "detected_frame": kind.value,
                    "state": state,
                    "compatible": compat,
                    "allowed_pipeline": list(allowed),
                    "blocked_pipeline": list(blocked),
                    "invariant_with_group": invariant,
                    "failure": failure.value,
                }
                results.append(FrameInvarianceResult(
                    case_id=case_id,
                    group_id=group.group_id,
                    text=text,
                    expected_frame=group.expected_frame,
                    detected_frame=kind,
                    state=state,
                    compatible=compat,
                    allowed_pipeline=allowed,
                    blocked_pipeline=blocked,
                    invariant_with_group=invariant,
                    failure=failure,
                    replay_hash=_result_replay_hash(payload),
                ))

        # Negative controls — detect each text; the two MUST yield
        # different frames (and the directive's labels).
        nc_results: list[NegativeControlResult] = []
        for nc in self._negative_controls:
            da = self._detector.detect(
                claim_id=f"{nc.nc_id}:a", source_text=nc.text_a,
            ).frame_kind
            db = self._detector.detect(
                claim_id=f"{nc.nc_id}:b", source_text=nc.text_b,
            ).frame_kind
            distinguished = da is not db
            nc_results.append(NegativeControlResult(
                nc_id=nc.nc_id, text_a=nc.text_a, text_b=nc.text_b,
                detected_a=da, detected_b=db,
                expected_a=nc.frame_a, expected_b=nc.frame_b,
                distinguished=distinguished,
            ))

        return FrameInvarianceRun(
            timestamp=datetime.now(timezone.utc),
            results=tuple(results),
            negative_controls=tuple(nc_results),
        )


__all__ = [
    "FrameInvarianceRun",
    "FrameInvarianceRunner",
    "NegativeControlResult",
]
