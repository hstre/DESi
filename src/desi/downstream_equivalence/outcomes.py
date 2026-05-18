"""v3.98 — downstream outcome derivation.

We derive an eight-tuple downstream signature per
anchor in the entangled (G+E) pair from its
trajectory's state sequence:

* ``final_verdict``      - LogicalState encoded
  in ``support_state`` at the last state.
* ``rescue_eligible``    - confidence >= 0.50 at
  the final state AND any branch_cost > 0
  appears across the trajectory.
* ``intervention_kind``  - closed enum derived
  from (final_verdict, contradiction trajectory).
* ``failure_class``      - derived from
  (final_verdict, audit shape).
* ``audit_outcome``      - derived from the
  confidence trajectory and final support.
* ``branch_path``        - tuple of branch_cost
  values (one per state).
* ``support_path``       - tuple of support_state
  values.
* ``rollback_required``  - True iff confidence
  decreased monotonically across any window.

Each axis is a closed enum (or a deterministic
function of the state vector). No semantic content
feeds the derivation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_members,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..novel_families import all_family_members


class FinalVerdict(str, Enum):
    UNDER_LOGICAL_AUDIT = "under_logical_audit"
    GAP_DETECTED        = "gap_detected"
    BRIDGE_REQUIRED     = "bridge_required"
    LOGICALLY_REJECTED  = "logically_rejected"
    LOGICALLY_SUPPORTED = "logically_supported"
    UNKNOWN             = "unknown"


_SUPPORT_TO_VERDICT: dict[float, str] = {
    0.0: FinalVerdict.UNDER_LOGICAL_AUDIT.value,
    1.0: FinalVerdict.GAP_DETECTED.value,
    2.0: FinalVerdict.BRIDGE_REQUIRED.value,
    3.0: FinalVerdict.LOGICALLY_REJECTED.value,
    4.0: FinalVerdict.LOGICALLY_SUPPORTED.value,
}


class InterventionKind(str, Enum):
    NONE              = "none"
    AUDIT_REPAIR      = "audit_repair"
    BRIDGE_INSERT     = "bridge_insert"
    CONTRADICTION_FIX = "contradiction_fix"
    REJECT            = "reject"


class FailureClass(str, Enum):
    NONE                  = "none"
    PARSER_LOSS           = "parser_loss"
    AUDIT_LOSS            = "audit_loss"
    RESOLUTION_BLOCKED    = "resolution_blocked"
    CONTRADICTION         = "contradiction"


class AuditOutcome(str, Enum):
    ACCEPTED              = "accepted"
    REJECTED              = "rejected"
    UNRESOLVED            = "unresolved"


def _final_verdict(support_state: float) -> str:
    return _SUPPORT_TO_VERDICT.get(
        support_state,
        FinalVerdict.UNKNOWN.value,
    )


def _rescue_eligible(traj) -> bool:
    final = traj.states[-1]
    if final.confidence < 0.50:
        return False
    return any(
        s.branch_cost > 0.0 for s in traj.states
    )


def _intervention_kind(
    traj, final_verdict: str,
) -> str:
    final = traj.states[-1]
    if final_verdict == (
        FinalVerdict.LOGICALLY_SUPPORTED.value
    ):
        return InterventionKind.NONE.value
    if final_verdict == (
        FinalVerdict.LOGICALLY_REJECTED.value
    ):
        if any(
            s.contradiction_load > 0.0
            for s in traj.states
        ):
            return (
                InterventionKind.CONTRADICTION_FIX
                .value
            )
        return InterventionKind.REJECT.value
    if final_verdict == (
        FinalVerdict.BRIDGE_REQUIRED.value
    ):
        return InterventionKind.BRIDGE_INSERT.value
    if final_verdict == (
        FinalVerdict.GAP_DETECTED.value
    ):
        return InterventionKind.AUDIT_REPAIR.value
    return InterventionKind.NONE.value


def _failure_class(
    traj, final_verdict: str,
) -> str:
    if final_verdict == (
        FinalVerdict.LOGICALLY_SUPPORTED.value
    ):
        return FailureClass.NONE.value
    if final_verdict == (
        FinalVerdict.LOGICALLY_REJECTED.value
    ):
        if any(
            s.contradiction_load > 0.0
            for s in traj.states
        ):
            return FailureClass.CONTRADICTION.value
        return FailureClass.AUDIT_LOSS.value
    if final_verdict == (
        FinalVerdict.BRIDGE_REQUIRED.value
    ):
        return FailureClass.RESOLUTION_BLOCKED.value
    if final_verdict == (
        FinalVerdict.GAP_DETECTED.value
    ):
        return FailureClass.PARSER_LOSS.value
    return FailureClass.NONE.value


def _audit_outcome(
    traj, final_verdict: str,
) -> str:
    if final_verdict == (
        FinalVerdict.LOGICALLY_SUPPORTED.value
    ):
        return AuditOutcome.ACCEPTED.value
    if final_verdict in {
        FinalVerdict.LOGICALLY_REJECTED.value,
    }:
        return AuditOutcome.REJECTED.value
    return AuditOutcome.UNRESOLVED.value


def _rollback_required(traj) -> bool:
    confs = [s.confidence for s in traj.states]
    if len(confs) < 2:
        return False
    return any(
        confs[i + 1] < confs[i]
        for i in range(len(confs) - 1)
    )


def _branch_path(traj) -> tuple[float, ...]:
    return tuple(
        s.branch_cost for s in traj.states
    )


def _support_path(traj) -> tuple[float, ...]:
    return tuple(
        s.support_state for s in traj.states
    )


@dataclass(frozen=True)
class DownstreamSignature:
    trajectory_id: str
    family_id: str
    final_verdict: str
    rescue_eligible: bool
    intervention_kind: str
    failure_class: str
    audit_outcome: str
    branch_path: tuple[float, ...]
    support_path: tuple[float, ...]
    rollback_required: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "family_id": self.family_id,
            "final_verdict": self.final_verdict,
            "rescue_eligible":
                self.rescue_eligible,
            "intervention_kind":
                self.intervention_kind,
            "failure_class": self.failure_class,
            "audit_outcome": self.audit_outcome,
            "branch_path": list(self.branch_path),
            "support_path":
                list(self.support_path),
            "rollback_required":
                self.rollback_required,
        }


@lru_cache(maxsize=1)
def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


@lru_cache(maxsize=1)
def all_downstream_signatures() -> tuple[
    DownstreamSignature, ...,
]:
    members = set(entangled_members())
    fam = _family_lookup()
    out: list[DownstreamSignature] = []
    for t in extract_all_trajectories():
        if t.trajectory_id not in members:
            continue
        final_v = _final_verdict(
            t.states[-1].support_state,
        )
        out.append(DownstreamSignature(
            trajectory_id=t.trajectory_id,
            family_id=fam.get(t.trajectory_id, "?"),
            final_verdict=final_v,
            rescue_eligible=_rescue_eligible(t),
            intervention_kind=_intervention_kind(
                t, final_v,
            ),
            failure_class=_failure_class(
                t, final_v,
            ),
            audit_outcome=_audit_outcome(
                t, final_v,
            ),
            branch_path=_branch_path(t),
            support_path=_support_path(t),
            rollback_required=(
                _rollback_required(t)
            ),
        ))
    return tuple(sorted(
        out, key=lambda s: s.trajectory_id,
    ))


__all__ = [
    "AuditOutcome",
    "DownstreamSignature",
    "FailureClass",
    "FinalVerdict",
    "InterventionKind",
    "all_downstream_signatures",
]
