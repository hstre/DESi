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
from .proposal import MutationProposal
from .sandbox import CloneSandbox, StableConfig


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
