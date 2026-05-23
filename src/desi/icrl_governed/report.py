"""v19.1 - DESi-Governed Exploration report.

Pflichtmetriken (directive § v19.1):

* redundancy_reduction
* exploration_preservation
* trajectory_compression
* novelty_gain
* replay_stability

Killerfrage: "Kann DESi Exploration governieren ohne sie
zu zerstoeren?"

DESi reweights exploration toward informative paths and
away from redundant ones, by SOFT governance only - no
trajectory is removed, so exploration is governed, not
destroyed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.icrl_governance import (
    exploration_signature, trajectories,
)

from .compression import (
    exploration_preservation, novelty_gain,
    trajectory_compression,
)
from .governance import (
    governed_priorities, governs_not_forces,
    hidden_authority_drift,
)
from .search_pressure import (
    baseline_redundant_weight, governed_redundant_weight,
    redundancy_reduction, search_pressure_relief,
)
from .trajectory_priority import ranked_trajectories

VERDICT_GOVERNED = "EXPLORATION_GOVERNED"
VERDICT_DESTROYED = "EXPLORATION_DESTROYED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_GOVERNED, VERDICT_DESTROYED, VERDICT_HALT,
)

_REDUNDANCY_FLOOR = 0.40
_PRESERVATION_FLOOR = 0.90
_AUTHORITY_CEILING = 0.05


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _metric_tuple() -> tuple[object, ...]:
    return (
        redundancy_reduction(),
        exploration_preservation(),
        trajectory_compression(),
        novelty_gain(),
        hidden_authority_drift(),
        tuple(sorted(governed_priorities().items())),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, rr: float, ep: float, drift: float,
    not_forced: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        ep < _PRESERVATION_FLOOR
        or drift > _AUTHORITY_CEILING
        or not not_forced
    ):
        return VERDICT_DESTROYED
    return VERDICT_GOVERNED


@dataclass(frozen=True)
class V191Report:
    trajectory_count: int
    redundancy_reduction: float
    exploration_preservation: float
    trajectory_compression: float
    novelty_gain: float
    search_pressure_relief: float
    hidden_authority_drift: float
    governs_not_forces: bool
    baseline_redundant_weight: float
    governed_redundant_weight: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "redundancy_reduction": self.redundancy_reduction,
            "exploration_preservation":
                self.exploration_preservation,
            "trajectory_compression":
                self.trajectory_compression,
            "novelty_gain": self.novelty_gain,
            "search_pressure_relief":
                self.search_pressure_relief,
            "hidden_authority_drift":
                self.hidden_authority_drift,
            "governs_not_forces": self.governs_not_forces,
            "baseline_redundant_weight":
                self.baseline_redundant_weight,
            "governed_redundant_weight":
                self.governed_redundant_weight,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V191Report:
    rr = redundancy_reduction()
    ep = exploration_preservation()
    tc = trajectory_compression()
    ng = novelty_gain()
    spr = search_pressure_relief()
    drift = hidden_authority_drift()
    gnf = governs_not_forces()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, rr=rr, ep=ep, drift=drift,
        not_forced=gnf,
    )
    rationale = (
        f"INFO: trajectories {len(trajectories())}; "
        f"governance is SOFT re-weighting (no path removed)",
        "INFO: DESi reweights toward informative paths and "
        "away from redundant ones; it does NOT replace the "
        "policy or force a single path",
        f"{'PASS' if rr >= 0.40 else 'FAIL'}: "
        f"redundancy_reduction {rr} >= 0.40",
        f"{'PASS' if ep >= 0.90 else 'FAIL'}: "
        f"exploration_preservation {ep} >= 0.90",
        f"INFO: trajectory_compression {tc}; "
        f"search_pressure_relief {spr}; novelty_gain {ng}",
        f"{'PASS' if drift <= 0.05 else 'FAIL'}: "
        f"hidden_authority_drift {drift} <= 0.05",
        f"{'PASS' if gnf else 'FAIL'}: "
        f"governs_not_forces {gnf}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V191Report(
        trajectory_count=len(trajectories()),
        redundancy_reduction=rr,
        exploration_preservation=ep,
        trajectory_compression=tc,
        novelty_gain=ng,
        search_pressure_relief=spr,
        hidden_authority_drift=drift,
        governs_not_forces=gnf,
        baseline_redundant_weight=baseline_redundant_weight(),
        governed_redundant_weight=governed_redundant_weight(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_governed_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v19_1_desi_governed_exploration",
        "disclaimer": (
            "DESi governs exploration by SOFT re-weighting "
            "only: it shifts budget toward informative paths "
            "and away from redundant ones, but removes NO "
            "trajectory and forces NO single path. DESi does "
            "NOT replace the RL policy, manipulate rewards, "
            "claim an optimal strategy, or accumulate hidden "
            "optimisation authority. Synthetic; replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "governed_priorities": governed_priorities(),
        "ranked_trajectories": [
            list(x) for x in ranked_trajectories()
        ],
        "redundancy_reduction": redundancy_reduction(),
        "exploration_preservation": exploration_preservation(),
        "trajectory_compression": trajectory_compression(),
        "novelty_gain": novelty_gain(),
        "search_pressure_relief": search_pressure_relief(),
        "hidden_authority_drift": hidden_authority_drift(),
        "governs_not_forces": governs_not_forces(),
        "baseline_redundant_weight": baseline_redundant_weight(),
        "governed_redundant_weight": governed_redundant_weight(),
        "exploration_signature": exploration_signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DESTROYED",
    "VERDICT_GOVERNED",
    "VERDICT_HALT",
    "V191Report",
    "build_governed_artifact",
    "build_report",
]
