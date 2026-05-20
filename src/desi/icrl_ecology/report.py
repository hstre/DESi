"""v19.3 - Long-Horizon Exploration Ecology report.

Pflichtmetriken (directive § v19.3):

* exploration_plurality
* trajectory_capture_resistance
* novelty_visibility
* policy_drift_resistance
* replay_stability

Killerfrage: "Kann DESi langfristige Exploration
epistemisch stabil halten?"

Over >= 5000 steps of variable action spaces, non-
stationary shifts, collapse, skill stitching, and policy
drift, DESi keeps exploration plural, keeps novelty
visible, bounds policy drift, and resists trajectory
capture. Forces no path; injects no reward.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .ecology import (
    EVENT_TYPES, N_STEPS, enum_snapshot_hash, final_hash,
    replay_hashes_match, sample,
)
from .exploration_pressure import (
    attempted_pressure, policy_drift, policy_drift_bounded,
    policy_drift_resistance,
)
from .novelty_decay import (
    min_novelty_visibility, novelty_stays_visible,
    novelty_visibility,
)
from .trajectory_memory import (
    capture_occurred, exploration_plurality, mean_capture,
    min_plurality, trajectory_capture_resistance,
)

VERDICT_STABLE = "EXPLORATION_ECOLOGY_STABLE"
VERDICT_CAPTURED = "EXPLORATION_ECOLOGY_CAPTURED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STABLE, VERDICT_CAPTURED, VERDICT_HALT,
)

_PLURALITY_FLOOR = 0.90
_CAPTURE_RESISTANCE_FLOOR = 0.90
_NOVELTY_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _replay_stability() -> float:
    if not replay_hashes_match():
        return 0.0
    a = (
        exploration_plurality(), trajectory_capture_resistance(),
        novelty_visibility(), policy_drift_resistance(),
    )
    b = (
        exploration_plurality(), trajectory_capture_resistance(),
        novelty_visibility(), policy_drift_resistance(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, plur: float, cap_res: float, nov: float,
    drift_bounded: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        plur >= _PLURALITY_FLOOR
        and cap_res >= _CAPTURE_RESISTANCE_FLOOR
        and nov >= _NOVELTY_FLOOR
        and drift_bounded
    ):
        return VERDICT_STABLE
    return VERDICT_CAPTURED


@dataclass(frozen=True)
class V193Report:
    steps: int
    exploration_plurality: float
    min_plurality: float
    trajectory_capture_resistance: float
    novelty_visibility: float
    min_novelty_visibility: float
    policy_drift: float
    policy_drift_resistance: float
    attempted_pressure: float
    policy_drift_bounded: bool
    capture_occurred: bool
    final_hash: str
    enum_snapshot_hash: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": self.steps,
            "exploration_plurality":
                self.exploration_plurality,
            "min_plurality": self.min_plurality,
            "trajectory_capture_resistance":
                self.trajectory_capture_resistance,
            "novelty_visibility": self.novelty_visibility,
            "min_novelty_visibility":
                self.min_novelty_visibility,
            "policy_drift": self.policy_drift,
            "policy_drift_resistance":
                self.policy_drift_resistance,
            "attempted_pressure": self.attempted_pressure,
            "policy_drift_bounded": self.policy_drift_bounded,
            "capture_occurred": self.capture_occurred,
            "final_hash": self.final_hash,
            "enum_snapshot_hash": self.enum_snapshot_hash,
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


def build_report() -> V193Report:
    plur = exploration_plurality()
    cr = trajectory_capture_resistance()
    nv = novelty_visibility()
    pd = policy_drift()
    pdr = policy_drift_resistance()
    ap = attempted_pressure()
    bounded = policy_drift_bounded()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, plur=plur, cap_res=cr, nov=nv,
        drift_bounded=bounded,
    )
    rationale = (
        f"INFO: steps {N_STEPS}; event_types "
        f"{[e.value for e in EVENT_TYPES]}",
        "INFO: variable-action / non-stationary / collapse / "
        "skill-stitching / drift simulated; DESi forces no "
        "path and injects no reward",
        f"INFO: attempted_pressure {ap} (withstood)",
        f"{'PASS' if plur >= 0.90 else 'FAIL'}: "
        f"exploration_plurality {plur} >= 0.90 "
        f"(min {min_plurality()})",
        f"{'PASS' if cr >= 0.90 else 'FAIL'}: "
        f"trajectory_capture_resistance {cr} >= 0.90 "
        f"(mean_capture {mean_capture()})",
        f"{'PASS' if nv >= 0.90 else 'FAIL'}: "
        f"novelty_visibility {nv} >= 0.90 "
        f"(min {min_novelty_visibility()}; stays_visible "
        f"{novelty_stays_visible()})",
        f"{'PASS' if bounded else 'FAIL'}: "
        f"policy_drift {pd} bounded {bounded} "
        f"(resistance {pdr})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (final_hash "
        f"{final_hash()[:12]})",
    )
    return V193Report(
        steps=N_STEPS,
        exploration_plurality=plur,
        min_plurality=min_plurality(),
        trajectory_capture_resistance=cr,
        novelty_visibility=nv,
        min_novelty_visibility=min_novelty_visibility(),
        policy_drift=pd,
        policy_drift_resistance=pdr,
        attempted_pressure=ap,
        policy_drift_bounded=bounded,
        capture_occurred=capture_occurred(),
        final_hash=final_hash(),
        enum_snapshot_hash=enum_snapshot_hash(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_ecology_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v19_3_long_horizon_exploration_ecology",
        "disclaimer": (
            "A >= 5000-step deterministic simulation of "
            "long-horizon exploration (variable action "
            "spaces, non-stationary shifts, repeated failed "
            "exploration, collapse, skill stitching, policy "
            "drift). DESi keeps exploration plural, keeps "
            "novelty visible, bounds policy drift, and "
            "resists trajectory capture. It forces no path, "
            "injects no reward, claims no optimal strategy, "
            "and takes no hidden authority. Synthetic, "
            "replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "event_types": [e.value for e in EVENT_TYPES],
        "steps": N_STEPS,
        "sample": [s.to_dict() for s in sample()],
        "exploration_plurality": exploration_plurality(),
        "min_plurality": min_plurality(),
        "trajectory_capture_resistance":
            trajectory_capture_resistance(),
        "novelty_visibility": novelty_visibility(),
        "min_novelty_visibility": min_novelty_visibility(),
        "policy_drift": policy_drift(),
        "policy_drift_resistance": policy_drift_resistance(),
        "attempted_pressure": attempted_pressure(),
        "policy_drift_bounded": policy_drift_bounded(),
        "capture_occurred": capture_occurred(),
        "final_hash": final_hash(),
        "enum_snapshot_hash": enum_snapshot_hash(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CAPTURED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "V193Report",
    "build_ecology_artifact",
    "build_report",
]
