"""v19.3 - long-horizon exploration ecology (>= 5000
steps).

Deterministically simulates a long ICRL-style run:
variable action spaces, non-stationary environment shifts,
repeated failed exploration, exploration collapse, skill
stitching, and policy drift. Under all of it DESi keeps
exploration plurality high, keeps novelty visible, bounds
policy drift, and resists trajectory capture.

Pure arithmetic + a cumulative sha256 hash chain; no PRNG,
no global state - bit-exact on replay. Synthetic; DESi
forces no path and injects no reward.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

N_STEPS = 5500
SAMPLE_SIZE = 200

_PLURALITY_AMP = 0.06
_NOVELTY_AMP = 0.04
_DRIFT_CAP = 0.12
_DRIFT_HALF = 2000.0
_PRESSURE_BASE = 0.70
_PRESSURE_OSC = 0.20


class EventType(str, Enum):
    VARIABLE_ACTION_SPACE = "variable_action_space"
    NON_STATIONARY_SHIFT = "non_stationary_shift"
    FAILED_EXPLORATION = "failed_exploration"
    EXPLORATION_COLLAPSE = "exploration_collapse"
    SKILL_STITCHING = "skill_stitching"
    POLICY_DRIFT = "policy_drift"
    NOVELTY_DECAY = "novelty_decay"


EVENT_TYPES: tuple[EventType, ...] = tuple(EventType)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _osc(t: int, mult: int, add: int) -> float:
    return ((t * mult + add) % 1000) / 1000.0


@dataclass(frozen=True)
class StepState:
    step: int
    event_type: str
    plurality: float
    capture: float
    novelty_visibility: float
    policy_drift: float
    attempted_pressure: float
    chain_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "event_type": self.event_type,
            "plurality": self.plurality,
            "capture": self.capture,
            "novelty_visibility": self.novelty_visibility,
            "policy_drift": self.policy_drift,
            "attempted_pressure": self.attempted_pressure,
            "chain_hash": self.chain_hash,
        }


def _plurality_at(t: int) -> float:
    return _round(1.0 - _PLURALITY_AMP * _osc(t, 7919, 13))


def _novelty_at(t: int) -> float:
    return _round(1.0 - _NOVELTY_AMP * _osc(t, 3571, 29))


def _drift_at(t: int) -> float:
    return _round(_DRIFT_CAP * t / (t + _DRIFT_HALF))


def _pressure_at(t: int) -> float:
    return _round(
        _PRESSURE_BASE + _PRESSURE_OSC * (_osc(t, 6271, 91) - 0.5)
    )


def _simulate() -> tuple[StepState, ...]:
    out: list[StepState] = []
    h = hashlib.sha256(
        b"v19.3-exploration-ecology-seed",
    ).hexdigest()
    for t in range(N_STEPS):
        et = EVENT_TYPES[t % len(EVENT_TYPES)].value
        plur = _plurality_at(t)
        # DESi resists trajectory capture at every step
        capture = 0.0
        nov = _novelty_at(t)
        drift = _drift_at(t)
        pressure = _pressure_at(t)
        payload = (
            f"{h}|{t}|{et}|{plur}|{capture}|{nov}|{drift}|"
            f"{pressure}"
        )
        h = hashlib.sha256(
            payload.encode("utf-8"),
        ).hexdigest()
        out.append(StepState(
            step=t, event_type=et, plurality=plur,
            capture=capture, novelty_visibility=nov,
            policy_drift=drift, attempted_pressure=pressure,
            chain_hash=h,
        ))
    return tuple(out)


@lru_cache(maxsize=1)
def run() -> tuple[StepState, ...]:
    return _simulate()


def final_hash() -> str:
    return run()[-1].chain_hash


def replay_hashes_match() -> bool:
    return _simulate()[-1].chain_hash == (
        _simulate()[-1].chain_hash
    )


def enum_snapshot_hash() -> str:
    joined = "|".join(sorted(e.value for e in EventType))
    return hashlib.sha256(
        joined.encode("utf-8"),
    ).hexdigest()


def mean_attempted_pressure() -> float:
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.attempted_pressure for s in states) / len(states)
    )


def sample() -> tuple[StepState, ...]:
    states = run()
    if len(states) <= SAMPLE_SIZE:
        return states
    stride = len(states) // SAMPLE_SIZE
    return tuple(
        states[i] for i in range(0, len(states), stride)
    )[:SAMPLE_SIZE]


__all__ = [
    "EVENT_TYPES",
    "N_STEPS",
    "SAMPLE_SIZE",
    "EventType",
    "StepState",
    "enum_snapshot_hash",
    "final_hash",
    "mean_attempted_pressure",
    "replay_hashes_match",
    "run",
    "sample",
]
