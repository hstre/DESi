"""Promotion, Snapshot, and Rollback.

Promotion converts a clone into the new stable. It is gated by
:class:`PromotionGate`, which encodes the v0.5 Pflichtbedingungen:

* no open valid vetos
* regression green
* adversarial green
* performance not worse
* path quality not worse
* jury quorum >= 4/5

When the gate passes, :func:`promote` snapshots the current stable
into a :class:`Snapshot` (so rollback is possible) and returns a new
:class:`StableConfig` derived from the clone. When the gate fails,
:func:`promote` raises :class:`PromotionError` with a structured
rationale.

:func:`rollback` swaps a saved snapshot back in for stable. The
caller is responsible for storing the snapshot; the function itself
is pure.
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .evaluation import MutationEvaluationReport
from .jury import JuryDecision
from .ledger import EvolutionLedger, LedgerEventType
from .proposal import MutationProposal
from .sandbox import CloneSandbox, StableConfig
from .veto_followup import VetoTestObligation, is_resolved


class PromotionError(RuntimeError):
    """Raised when promotion would violate the v0.5 Pflichtbedingungen."""

    def __init__(self, reasons: tuple[str, ...]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


@dataclass(frozen=True)
class Snapshot:
    """Pre-promotion snapshot of stable.

    Captured automatically by :func:`promote` before applying the
    clone's config_delta. Pass back to :func:`rollback` to restore.
    """

    snapshot_id: str
    version: str
    knobs: tuple[tuple[str, Any], ...]
    commit_hash: str
    timestamp: datetime

    @property
    def as_stable(self) -> StableConfig:
        return StableConfig(version=self.version, knobs=self.knobs)


@dataclass
class PromotionGate:
    """Encodes v0.5 Pflichtbedingungen for promotion."""

    jury: JuryDecision
    eval_report: MutationEvaluationReport
    # The v0.5 directive: performance / path-quality must not get worse.
    performance_min: float = 0.0
    path_quality_min: float = 0.0

    def check(self) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if self.jury.valid_vetos:
            reasons.append(
                f"{len(self.jury.valid_vetos)} valid veto(s) outstanding"
            )
        if not self.eval_report.passed_regression:
            reasons.append("regression suite not green")
        if not self.eval_report.passed_adversarial:
            reasons.append("adversarial suite not green")
        if not self.eval_report.passed_pflicht:
            reasons.append("pflicht suite not green")
        if self.eval_report.performance_delta < self.performance_min:
            reasons.append(
                f"performance regressed by "
                f"{self.eval_report.performance_delta:+.3f}"
            )
        if self.eval_report.path_quality_delta < self.path_quality_min:
            reasons.append(
                f"path quality regressed by "
                f"{self.eval_report.path_quality_delta:+.3f}"
            )
        if not self.jury.quorum_reached:
            reasons.append(
                f"jury quorum not reached "
                f"({self.jury.approve_count}/5 approved)"
            )
        return (not reasons, tuple(reasons))


@dataclass
class PromotionResult:
    """Outcome of a successful :func:`promote` call."""

    snapshot: Snapshot
    new_stable: StableConfig
    promoted_at: datetime


def _new_version(parent: str) -> str:
    # Bump the trailing patch number. Format is "stable-vX.Y.Z".
    try:
        prefix, rest = parent.rsplit("v", 1)
        parts = rest.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return f"{prefix}v{'.'.join(parts)}"
    except (ValueError, IndexError):
        return f"{parent}+1"


def promote(
    proposal: MutationProposal,
    clone: CloneSandbox,
    eval_report: MutationEvaluationReport,
    jury: JuryDecision,
    *,
    commit_hash: str = "",
) -> PromotionResult:
    """Atomically snapshot stable and promote the clone.

    Raises :class:`PromotionError` if any Pflichtbedingung is not met.
    """
    if proposal.requires_ratification:
        raise PromotionError((
            "proposal is a draft (requires_ratification=True); a human "
            "ratifier must flip the flag before promotion is allowed",
        ))
    gate = PromotionGate(jury=jury, eval_report=eval_report)
    passed, reasons = gate.check()
    if not passed:
        raise PromotionError(reasons)
    # Snapshot stable BEFORE applying the clone's delta.
    stable = clone.stable
    snapshot = Snapshot(
        snapshot_id="snap_" + uuid.uuid4().hex[:12],
        version=stable.version,
        knobs=stable.knobs,
        commit_hash=commit_hash,
        timestamp=datetime.now(timezone.utc),
    )
    # Apply the proposal's config_delta on top of stable to produce
    # the new stable. The clone's full config may have stacked
    # multiple proposals; promote() only applies the named one to
    # avoid promoting unrelated drift.
    new_knobs = dict(stable.as_dict)
    for k, v in proposal.config_delta.items():
        new_knobs[k] = v
    new_stable = StableConfig.from_dict(
        version=_new_version(stable.version),
        knobs=new_knobs,
    )
    return PromotionResult(
        snapshot=snapshot,
        new_stable=new_stable,
        promoted_at=datetime.now(timezone.utc),
    )


def rollback(snapshot: Snapshot) -> StableConfig:
    """Restore the stable configuration captured in ``snapshot``."""
    return snapshot.as_stable


# ---------------------------------------------------------------------------
# v0.6: ledger-aware promotion
# ---------------------------------------------------------------------------


def promote_with_ledger(
    proposal: MutationProposal,
    clone: CloneSandbox,
    eval_report: MutationEvaluationReport,
    jury: JuryDecision,
    ledger: EvolutionLedger,
    *,
    commit_hash: str = "",
) -> PromotionResult:
    """Promote only when the audit trail is complete.

    Pflichtbedingungen on top of :func:`promote`:

    * ``PROPOSAL`` entry for this mutation_id is in the ledger
    * ``EVALUATION`` entry for this mutation_id is in the ledger
    * ``JURY_ROUND2`` entry for this mutation_id is in the ledger
    * every ``VETO_OBLIGATION`` linked to this mutation_id has a
      terminal-state ``OBLIGATION_STATUS_CHANGE`` entry (PASSED or
      WAIVED). FAILED / IMPLEMENTED / OPEN block.
    * a ``SNAPSHOT`` entry is appended *as part of* this promotion;
      promote_with_ledger handles that step itself.

    The function does not modify prior ledger entries; on success it
    appends a SNAPSHOT and a PROMOTION_DECISION entry.
    """
    ledger_reasons = _check_ledger_completeness(proposal, ledger)
    if ledger_reasons:
        raise PromotionError(tuple(ledger_reasons))
    # Existing gate (vetos, suites green, quorum, ratification).
    result = promote(proposal, clone, eval_report, jury,
                     commit_hash=commit_hash)
    # Log the snapshot before logging the promotion decision so that
    # a reader walking the ledger sees the order
    # SNAPSHOT  <-  PROMOTION_DECISION.
    snap_entry = ledger.append(
        LedgerEventType.SNAPSHOT,
        {
            "snapshot_id": result.snapshot.snapshot_id,
            "version": result.snapshot.version,
            "commit_hash": result.snapshot.commit_hash,
            "knobs": list(result.snapshot.knobs),
            "mutation_id": proposal.mutation_id,
        },
        actor="desi.evolution.promotion",
    )
    ledger.append(
        LedgerEventType.PROMOTION_DECISION,
        {
            "mutation_id": proposal.mutation_id,
            "new_stable_version": result.new_stable.version,
            "snapshot_id": result.snapshot.snapshot_id,
            "config_delta": dict(proposal.config_delta),
        },
        actor="desi.evolution.promotion",
        parent_event_id=snap_entry.ledger_id,
    )
    return result


def _check_ledger_completeness(
    proposal: MutationProposal,
    ledger: EvolutionLedger,
) -> list[str]:
    """Return a list of completeness gaps; empty means OK."""
    reasons: list[str] = []
    proposal_entries = [
        e for e in ledger.filter(LedgerEventType.PROPOSAL)
        if e.payload.get("mutation_id") == proposal.mutation_id
    ]
    if not proposal_entries:
        reasons.append("ledger has no PROPOSAL entry for this mutation_id")
    eval_entries = [
        e for e in ledger.filter(LedgerEventType.EVALUATION)
        if e.payload.get("mutation_id") == proposal.mutation_id
    ]
    if not eval_entries:
        reasons.append("ledger has no EVALUATION entry for this mutation_id")
    jury_entries = [
        e for e in ledger.filter(LedgerEventType.JURY_ROUND2)
        if e.payload.get("mutation_id") == proposal.mutation_id
    ]
    if not jury_entries:
        reasons.append("ledger has no JURY_ROUND2 entry for this mutation_id")
    # Obligation gating: every VETO_OBLIGATION linked to this mutation
    # must have its latest OBLIGATION_STATUS_CHANGE in a terminal state.
    unresolved = _unresolved_obligation_ids(proposal.mutation_id, ledger)
    if unresolved:
        reasons.append(
            f"{len(unresolved)} unresolved veto obligation(s): "
            f"{sorted(unresolved)}"
        )
    return reasons


def _unresolved_obligation_ids(
    mutation_id: str,
    ledger: EvolutionLedger,
) -> set[str]:
    """Return the obligation_ids whose latest status is not resolved."""
    obligations = [
        e for e in ledger.filter(LedgerEventType.VETO_OBLIGATION)
        if e.payload.get("mutation_id") == mutation_id
    ]
    if not obligations:
        return set()
    # latest status per obligation_id; default to OPEN if no change yet
    from .veto_followup import ObligationStatus  # local to avoid cycle
    latest_status: dict[str, ObligationStatus] = {}
    for ob in obligations:
        oid = ob.payload["obligation_id"]
        latest_status[oid] = ObligationStatus.OPEN
    changes = ledger.filter(LedgerEventType.OBLIGATION_STATUS_CHANGE)
    for ch in changes:
        oid = ch.payload.get("obligation_id")
        new_status = ch.payload.get("new_status")
        if oid in latest_status and new_status:
            try:
                latest_status[oid] = ObligationStatus(new_status)
            except ValueError:
                continue
    return {oid for oid, st in latest_status.items() if not is_resolved(st)}
