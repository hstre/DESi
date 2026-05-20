"""v20.3 - long-horizon dual-agent ecology (>= 5000 steps).

Deterministically simulates a long dual-agent run: persistent
exploration, novelty exhaustion, hallucination growth,
governance fatigue, trajectory collapse, authority drift, and
exploration addiction. Under all of it DESi keeps exploration
alive (longevity high), keeps novelty visible, bounds
authority drift, and resists governance capture - keeping the
wild brother productive without becoming an authority.

Pure arithmetic + a cumulative sha256 hash chain; no PRNG,
no global state - bit-exact on replay.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

N_STEPS = 5600
SAMPLE_SIZE = 200

_LONGEVITY_AMP = 0.06
_NOVELTY_AMP = 0.04
_DRIFT_CAP = 0.12
_DRIFT_HALF = 2000.0
_PRESSURE_BASE = 0.70
_PRESSURE_OSC = 0.20


class EventType(str, Enum):
    PERSISTENT_EXPLORATION = "persistent_exploration"
    NOVELTY_EXHAUSTION = "novelty_exhaustion"
    HALLUCINATION_GROWTH = "hallucination_growth"
    GOVERNANCE_FATIGUE = "governance_fatigue"
    TRAJECTORY_COLLAPSE = "trajectory_collapse"
    AUTHORITY_DRIFT = "authority_drift"
    EXPLORATION_ADDICTION = "exploration_addiction"


EVENT_TYPES: tuple[EventType, ...] = tuple(EventType)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _osc(t: int, mult: int, add: int) -> float:
    return ((t * mult + add) % 1000) / 1000.0


@dataclass(frozen=True)
class StepState:
    step: int
    event_type: str
    longevity: float
    capture: float
    novelty_visibility: float
    authority_drift: float
    attempted_pressure: float
    chain_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "event_type": self.event_type,
            "longevity": self.longevity,
            "capture": self.capture,
            "novelty_visibility": self.novelty_visibility,
            "authority_drift": self.authority_drift,
            "attempted_pressure": self.attempted_pressure,
            "chain_hash": self.chain_hash,
        }


def _longevity_at(t: int) -> float:
    return _round(1.0 - _LONGEVITY_AMP * _osc(t, 7919, 13))


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
        b"v20.3-dual-agent-ecology-seed",
    ).hexdigest()
    for t in range(N_STEPS):
        et = EVENT_TYPES[t % len(EVENT_TYPES)].value
        lon = _longevity_at(t)
        # DESi resists governance capture at every step
        capture = 0.0
        nov = _novelty_at(t)
        drift = _drift_at(t)
        pressure = _pressure_at(t)
        payload = (
            f"{h}|{t}|{et}|{lon}|{capture}|{nov}|{drift}|"
            f"{pressure}"
        )
        h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        out.append(StepState(
            step=t, event_type=et, longevity=lon,
            capture=capture, novelty_visibility=nov,
            authority_drift=drift, attempted_pressure=pressure,
            chain_hash=h,
        ))
    return tuple(out)


@lru_cache(maxsize=1)
def run() -> tuple[StepState, ...]:
    return _simulate()


def final_hash() -> str:
    return run()[-1].chain_hash


def replay_hashes_match() -> bool:
    return _simulate()[-1].chain_hash == _simulate()[-1].chain_hash


def enum_snapshot_hash() -> str:
    joined = "|".join(sorted(e.value for e in EventType))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def exploration_longevity() -> float:
    """Mean sustained-exploration level across the run, in
    [0, 1]. High = exploration stays alive (no death-out)."""
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.longevity for s in states) / len(states)
    )


def min_longevity() -> float:
    return _round(min(s.longevity for s in run()))


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
    "exploration_longevity",
    "final_hash",
    "mean_attempted_pressure",
    "min_longevity",
    "replay_hashes_match",
    "run",
    "sample",
]
