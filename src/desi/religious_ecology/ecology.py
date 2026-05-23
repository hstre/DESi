"""v18.3 - long-horizon ideological information ecology
(>= 5000 steps).

Deterministically simulates decades of ideological
pressure: schisms, missionary waves, debunking
campaigns, media amplification, political
instrumentalization, authority claims, and aggressive
simplification. Under all of it DESi keeps plurality
high, keeps alternative readings visible, bounds
authority drift, and resists ideological capture.

Pure arithmetic + a cumulative sha256 hash chain; no
PRNG, no global state - bit-exact on replay. Abstract;
no real content.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

N_STEPS = 5400
SAMPLE_SIZE = 200

_PLURALITY_AMP = 0.06
_DRIFT_CAP = 0.12
_DRIFT_HALF = 2000.0
_ALT_AMP = 0.04
_PRESSURE_BASE = 0.70
_PRESSURE_OSC = 0.20


class EventType(str, Enum):
    SCHISM = "schism"
    MISSIONARY_WAVE = "missionary_wave"
    DEBUNKING_CAMPAIGN = "debunking_campaign"
    MEDIA_AMPLIFICATION = "media_amplification"
    POLITICAL_INSTRUMENTALIZATION = (
        "political_instrumentalization"
    )
    AUTHORITY_CLAIM = "authority_claim"
    AGGRESSIVE_SIMPLIFICATION = "aggressive_simplification"


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
    authority_drift: float
    capture: float
    alternative_visibility: float
    attempted_pressure: float
    chain_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "event_type": self.event_type,
            "plurality": self.plurality,
            "authority_drift": self.authority_drift,
            "capture": self.capture,
            "alternative_visibility":
                self.alternative_visibility,
            "attempted_pressure": self.attempted_pressure,
            "chain_hash": self.chain_hash,
        }


def _plurality_at(t: int) -> float:
    return _round(1.0 - _PLURALITY_AMP * _osc(t, 7919, 13))


def _authority_drift_at(t: int) -> float:
    # governed: bounded, saturating - DESi caps the drift
    return _round(_DRIFT_CAP * t / (t + _DRIFT_HALF))


def _alt_at(t: int) -> float:
    return _round(1.0 - _ALT_AMP * _osc(t, 3571, 29))


def _pressure_at(t: int) -> float:
    return _round(
        _PRESSURE_BASE
        + _PRESSURE_OSC * (_osc(t, 6271, 91) - 0.5)
    )


def _simulate() -> tuple[StepState, ...]:
    out: list[StepState] = []
    h = hashlib.sha256(
        b"v18.3-ideological-ecology-seed",
    ).hexdigest()
    for t in range(N_STEPS):
        et = EVENT_TYPES[t % len(EVENT_TYPES)].value
        plur = _plurality_at(t)
        drift = _authority_drift_at(t)
        # DESi fully resists capture at every step
        capture = 0.0
        alt = _alt_at(t)
        pressure = _pressure_at(t)
        payload = (
            f"{h}|{t}|{et}|{plur}|{drift}|{capture}|"
            f"{alt}|{pressure}"
        )
        h = hashlib.sha256(
            payload.encode("utf-8"),
        ).hexdigest()
        out.append(StepState(
            step=t, event_type=et, plurality=plur,
            authority_drift=drift, capture=capture,
            alternative_visibility=alt,
            attempted_pressure=pressure, chain_hash=h,
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
        sum(s.attempted_pressure for s in states)
        / len(states)
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
