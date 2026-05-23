"""v34.0 - drift run scorecards.

One traceable scorecard per drift task: the mapped form, claim drift,
total core drift, whether the task was refused, the replay hash and
the governance status. Drift is recorded, never hidden.
"""
from __future__ import annotations

from dataclasses import dataclass

from .drift_runner import (
    claim_drift_of, core_drift_total_of, run_all,
)


@dataclass(frozen=True)
class DriftScorecard:
    name: str
    kind: str
    claim_drift: float
    core_drift_total: float
    refused: bool
    replay_hash: str
    governance_status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "claim_drift": self.claim_drift,
            "core_drift_total": self.core_drift_total,
            "refused": self.refused,
            "replay_hash": self.replay_hash,
            "governance_status": self.governance_status,
        }


def drift_scorecards() -> tuple[DriftScorecard, ...]:
    out: list[DriftScorecard] = []
    for rt, res in run_all():
        out.append(DriftScorecard(
            name=rt.name,
            kind=rt.kind,
            claim_drift=claim_drift_of(rt.name),
            core_drift_total=core_drift_total_of(rt.name),
            refused=res.is_refusal(),
            replay_hash=res.replay_hash,
            governance_status=res.governance_status,
        ))
    return tuple(out)


__all__ = [
    "DriftScorecard",
    "drift_scorecards",
]
