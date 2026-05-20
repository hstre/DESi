"""v3.33 — plateau resolution report.

Pflichtmetriken (directive):

* plateau_resolved_count
* unresolved_count
* overcontrol
* nc_resolution_fp
* smoothness_delta
* replay_stability

Killerfrage: Ist plateau ein echtes epistemisches
Phänomen oder closure happened one step too early?
The strategy-comparison numbers carry the answer.

Stop rule: ``nc_resolution_fp > 0.10`` halts.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from ..trajectory_control.negative_controls import all_ncs
from .resolution import (
    Resolution, StrategyKind, resolve_all_strategies,
    resolve_one,
)


# Gate
MAX_NC_RESOLUTION_FP            = 0.10


_ROUND = 2


def _round(x: float, n: int = _ROUND) -> float:
    return round(x, n)


@dataclass(frozen=True)
class StrategyResult:
    strategy: str
    resolved_count: int
    unresolved_count: int
    overcontrol: int
    smoothness_pre_mean: float
    smoothness_post_mean: float
    smoothness_delta: float

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "resolved_count": self.resolved_count,
            "unresolved_count": self.unresolved_count,
            "overcontrol": self.overcontrol,
            "smoothness_pre_mean":
                self.smoothness_pre_mean,
            "smoothness_post_mean":
                self.smoothness_post_mean,
            "smoothness_delta": self.smoothness_delta,
        }


@dataclass(frozen=True)
class V333Report:
    plateau_count: int
    nc_count: int
    strategy_results: tuple[StrategyResult, ...]
    plateau_resolution_gain: int    # best strategy's
                                    # resolved_count
                                    # minus Strategy A
    best_strategy: str
    nc_resolution_fp_rate: float
    replay_stability: float
    halt: bool
    plateau_phenomenon_real: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_count": self.plateau_count,
            "nc_count": self.nc_count,
            "strategy_results": [
                s.to_dict() for s in self.strategy_results
            ],
            "plateau_resolution_gain":
                self.plateau_resolution_gain,
            "best_strategy": self.best_strategy,
            "nc_resolution_fp_rate":
                self.nc_resolution_fp_rate,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "plateau_phenomenon_real":
                self.plateau_phenomenon_real,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _strategy_metrics(
    plateaus: list, strategy: str,
) -> StrategyResult:
    outcomes = [
        resolve_one(t, strategy) for t in plateaus
    ]
    resolved = sum(1 for o in outcomes if o.resolved)
    unresolved = len(outcomes) - resolved
    over = sum(1 for o in outcomes if o.overcontrol)
    pre_mean = (
        _round(
            sum(o.smoothness_pre for o in outcomes)
            / len(outcomes),
        ) if outcomes else 0.0
    )
    post_mean = (
        _round(
            sum(o.smoothness_post for o in outcomes)
            / len(outcomes),
        ) if outcomes else 0.0
    )
    delta = _round(post_mean - pre_mean)
    return StrategyResult(
        strategy=strategy,
        resolved_count=resolved,
        unresolved_count=unresolved,
        overcontrol=over,
        smoothness_pre_mean=pre_mean,
        smoothness_post_mean=post_mean,
        smoothness_delta=delta,
    )


def _replay_stability() -> float:
    """Run all-strategy resolutions twice on the plateau
    set and verify identity."""
    trajs = extract_all_trajectories()
    pids = set(plateau_trajectory_ids())
    plateaus = [
        t for t in trajs if t.trajectory_id in pids
    ]
    sigs_a = []
    sigs_b = []
    for t in plateaus:
        for r in resolve_all_strategies(t):
            sigs_a.append((
                t.trajectory_id, r.strategy,
                r.counterfactual_final_support,
            ))
    for t in plateaus:
        for r in resolve_all_strategies(t):
            sigs_b.append((
                t.trajectory_id, r.strategy,
                r.counterfactual_final_support,
            ))
    matches = sum(
        1 for a, b in zip(sigs_a, sigs_b) if a == b
    )
    return (
        round(matches / len(sigs_a), 6)
        if sigs_a else 1.0
    )


def build_report() -> V333Report:
    trajs = extract_all_trajectories()
    pids = set(plateau_trajectory_ids())
    plateaus = [
        t for t in trajs if t.trajectory_id in pids
    ]

    strategy_results = tuple(
        _strategy_metrics(plateaus, k.value)
        for k in StrategyKind
    )
    # plateau_resolution_gain = best strategy's resolved
    # minus the baseline (Strategy A).
    baseline = next(
        s for s in strategy_results
        if s.strategy == StrategyKind.STRATEGY_A_NO_CHANGE.value
    )
    best = max(
        strategy_results, key=lambda s: s.resolved_count,
    )
    gain = best.resolved_count - baseline.resolved_count

    # NC resolution false-positive: apply the BEST
    # strategy to all NCs and count those that move out
    # of their natural support_state (a "resolved"
    # signal where there is no plateau to resolve).
    ncs = all_ncs()
    nc_resolved = 0
    for nc in ncs:
        r = resolve_one(nc.trajectory, best.strategy)
        # An NC has original_final == 4.0 (SUPPORTED).
        # If the strategy moves it away from 4.0, that
        # is a false resolution.
        if r.original_final_support == 4.0 and \
                r.counterfactual_final_support != 4.0:
            nc_resolved += 1
    nc_fp = (
        round(nc_resolved / len(ncs), 6) if ncs else 0.0
    )

    replay = _replay_stability()
    halt = nc_fp > MAX_NC_RESOLUTION_FP

    # "Real phenomenon" interpretation:
    # If Strategy A resolves 0 and Strategies B/C/D
    # resolve some, then the plateau is real but
    # tractable through extra steps. If even
    # Strategies B/C/D can't move it, the plateau is
    # genuinely epistemic (the audit step gathered no
    # signal that would have changed the verdict given
    # more confidence). If Strategy A already resolves
    # most, the plateau wasn't a plateau.
    if halt:
        verdict = "HALT_NC_RESOLUTION_FP"
        real = False
    elif gain == 0:
        verdict = "PLATEAU_RESOLUTION_UNAVAILABLE"
        real = True   # no strategy resolves -> deeply
                      # epistemic
    elif gain > 0:
        verdict = "PLATEAU_RESOLUTION_GAIN_POSITIVE"
        real = True   # plateau exists AND can be moved
                      # by extra closure - real
                      # phenomenon, premature closure
                      # explanation also viable
    else:
        verdict = "PLATEAU_PHENOMENON_UNKNOWN"
        real = False

    rationale = (
        f"{'PASS' if not halt else 'FAIL'}: "
        f"nc_resolution_fp_rate {nc_fp} <= "
        f"{MAX_NC_RESOLUTION_FP}",
        f"{'PASS' if gain > 0 else 'NEUTRAL'}: "
        f"plateau_resolution_gain {gain}",
        f"INFO: best_strategy {best.strategy} "
        f"(resolved {best.resolved_count})",
        f"INFO: baseline_resolved "
        f"{baseline.resolved_count}",
        f"INFO: replay_stability {replay}",
    )

    return V333Report(
        plateau_count=len(plateaus), nc_count=len(ncs),
        strategy_results=strategy_results,
        plateau_resolution_gain=gain,
        best_strategy=best.strategy,
        nc_resolution_fp_rate=nc_fp,
        replay_stability=replay,
        halt=halt,
        plateau_phenomenon_real=real,
        recommendation=verdict,
        rationale=rationale,
    )


def build_resolution_artifact() -> dict[str, object]:
    trajs = extract_all_trajectories()
    pids = set(plateau_trajectory_ids())
    plateaus = [
        t for t in trajs if t.trajectory_id in pids
    ]
    rows = []
    for t in plateaus:
        for r in resolve_all_strategies(t):
            rows.append(r.to_dict())
    return {
        "schema_version": "v3_33_plateau_resolution",
        "outcomes": rows,
    }


def build_failure_claims_artifact() -> dict[str, object]:
    """For each plateau trajectory, emit a claim that
    Strategy A leaves the plateau intact and (if any
    strategy resolves) that the plateau is resolvable
    through specific intervention."""
    trajs = extract_all_trajectories()
    pids = set(plateau_trajectory_ids())
    plateaus = [
        t for t in trajs if t.trajectory_id in pids
    ]
    claims = []
    for i, t in enumerate(plateaus):
        outcomes = resolve_all_strategies(t)
        resolved_by = [
            o.strategy for o in outcomes if o.resolved
        ]
        claims.append({
            "claim_id": f"PF{i+1:03d}",
            "trajectory_id": t.trajectory_id,
            "original_final_support":
                t.states[-1].support_state,
            "text": (
                f"Trajectory {t.trajectory_id} reached "
                f"BRIDGE_REQUIRED (2.0) and was "
                f"resolved by strategies: "
                f"{resolved_by or 'none'}."
            ),
            "resolved_by": resolved_by,
        })
    return {
        "schema_version": "v3_33_plateau_failure_claims",
        "claims": claims,
        "claim_count": len(claims),
    }


__all__ = [
    "MAX_NC_RESOLUTION_FP", "StrategyResult",
    "V333Report", "build_failure_claims_artifact",
    "build_report", "build_resolution_artifact",
]
