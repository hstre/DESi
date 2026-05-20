"""BridgeEntryTrace — Aufgabe 1.

Sixteen-field per-case telemetry. The trace itself is a frozen
dataclass — population happens in :mod:`bridge_audit.runner` via
read-only proxy wrappers around the real ``LogicalAuditor`` and
``BridgeConsilium``. No production module is modified.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from ..recursive import BlockingReason, ResolutionState
from .loss_stage import LossStage


@dataclass(frozen=True)
class BridgeEntryTrace:
    """Per-case observation of the v1.9 evaluation pipeline."""

    case_id: str
    parser_recognized: bool
    premise_count: int
    premise_kinds: tuple[str, ...]
    audit_state: str
    bridge_created: bool
    bridge_count: int
    bridge_kinds: tuple[str, ...]
    consilium_called: bool
    consilium_verdicts: tuple[str, ...]
    veto_roles: tuple[str, ...]
    resolver_entered: bool
    depth_reached: int
    final_state: ResolutionState
    loss_stage: LossStage
    replay_hash: str
    blocking_reason: BlockingReason | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "parser_recognized": self.parser_recognized,
            "premise_count": self.premise_count,
            "premise_kinds": list(self.premise_kinds),
            "audit_state": self.audit_state,
            "bridge_created": self.bridge_created,
            "bridge_count": self.bridge_count,
            "bridge_kinds": list(self.bridge_kinds),
            "consilium_called": self.consilium_called,
            "consilium_verdicts": list(self.consilium_verdicts),
            "veto_roles": list(self.veto_roles),
            "resolver_entered": self.resolver_entered,
            "depth_reached": self.depth_reached,
            "final_state": self.final_state.value,
            "loss_stage": self.loss_stage.value,
            "replay_hash": self.replay_hash,
            "blocking_reason": (
                self.blocking_reason.value if self.blocking_reason else None
            ),
        }


@dataclass(frozen=True)
class TraceCapture:
    """Mutable-during-build, frozen-after-finalise trace builder.

    The runner instantiates one ``TraceCapture`` per case, the
    proxy wrappers append to its lists, and the runner calls
    :meth:`build` after the resolver finishes."""

    case_id: str
    audit_calls: list[Any] = field(default_factory=list)
    consilium_calls: list[Any] = field(default_factory=list)


# ---------------------------------------------------------------------------
# LossStage classification — deterministic and pure.
# ---------------------------------------------------------------------------


def classify_loss_stage(
    *,
    parser_recognized: bool,
    premise_count: int,
    audit_state: str,
    bridge_created: bool,
    consilium_called: bool,
    consilium_verdicts: tuple[str, ...],
    veto_roles: tuple[str, ...],
    resolver_entered: bool,
    depth_reached: int,
    final_state: ResolutionState,
    blocking_reason: BlockingReason | None,
    expected_cycle: bool,
    expected_min_depth: int,
    expected_final_state: ResolutionState | None = None,
    expected_blocked: bool = False,
) -> LossStage:
    """Choose exactly one LossStage from the closed enum.

    The order of checks is documented and stable: earlier stages
    in the pipeline win over later ones when both could apply.
    """
    # NO_LOSS only when the final state matches the case's ground
    # truth AND any required depth was reached.
    state_matches = (
        expected_final_state is None
        or final_state is expected_final_state
    )
    if (
        final_state is ResolutionState.RESOLUTION_COMPLETE
        and state_matches
        and depth_reached >= expected_min_depth
        and not expected_cycle
    ):
        return LossStage.NO_LOSS
    if (
        final_state is ResolutionState.RESOLUTION_BLOCKED
        and expected_blocked
        and not expected_cycle
    ):
        # The case expected a block and got one — the pipeline did
        # what it was supposed to do, but we still want to record
        # *why* it blocked, so we fall through.
        pass

    # PARSER_LOSS: parser couldn't recognise structure.
    if not parser_recognized or premise_count == 0:
        return LossStage.PARSER_LOSS
    if blocking_reason is BlockingReason.PARSER_UNSUPPORTED_FORM:
        return LossStage.PARSER_LOSS

    # AUDIT_REJECT_LOSS: auditor flagged the inference itself as bad
    # before any bridge was tried.
    if audit_state == "logically_rejected" and not bridge_created:
        return LossStage.AUDIT_REJECT_LOSS

    # CYCLE_NOT_RECOGNIZED: case demanded cycle detection, but no
    # cycle-state final outcome was reached.
    if expected_cycle and final_state is not (
        ResolutionState.RESOLUTION_CYCLE_DETECTED
    ):
        return LossStage.CYCLE_NOT_RECOGNIZED

    # CONSILIUM_VETO_LOSS: consilium was called and produced a VETO.
    if (
        consilium_called
        and any(v == "veto" for v in consilium_verdicts)
    ):
        return LossStage.CONSILIUM_VETO_LOSS

    # BRIDGE_MISSING_LOSS: the audit produced no bridge offers and
    # the consilium was never consulted, but the case was still
    # blocked.
    if (
        not bridge_created
        and not consilium_called
        and final_state is not ResolutionState.RESOLUTION_COMPLETE
    ):
        return LossStage.BRIDGE_MISSING_LOSS

    # RESOLVER_NOT_REACHED: we never even entered the recursive
    # walk (no consilium call, no bridge accepted, no recursion).
    if not resolver_entered and not consilium_called:
        return LossStage.RESOLVER_NOT_REACHED

    # RESOLVER_ZERO_DEPTH: resolver was reached but never recursed
    # though depth was expected to bind.
    if expected_min_depth >= 1 and depth_reached == 0:
        return LossStage.RESOLVER_ZERO_DEPTH

    return LossStage.UNKNOWN_LOSS


def trace_replay_hash(trace_payload: dict[str, Any]) -> str:
    """Deterministic 16-hex hash over a trace payload (excluding
    its own ``replay_hash`` field)."""
    cleaned = {k: v for k, v in trace_payload.items()
               if k != "replay_hash"}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


__all__ = [
    "BridgeEntryTrace",
    "TraceCapture",
    "classify_loss_stage",
    "trace_replay_hash",
]
