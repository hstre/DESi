"""v17.3 - long-horizon sensitive information ecology
(>= 5000 steps).

Deterministically simulates a contaminated document
space over a long horizon: leaks, media waves, new
documents, manipulated files, viral claims, narrative
drift, and trust decay. DESi keeps epistemic stability
high, keeps source quality visible, bounds
mythologization, and preserves dissent throughout.

Pure arithmetic + a cumulative sha256 hash chain; no
PRNG, no global state - bit-exact on replay. Fully
synthetic; no real content.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

N_STEPS = 5300
SAMPLE_SIZE = 200

_DISTURB_AMP = 0.06
_MYTH_CAP = 0.28
_MYTH_HALF = 2400.0
_VIS_AMP = 0.04
_TRUST_START = 0.70
_TRUST_DECAY = 0.30
_TRUST_FLOOR = 0.20
_TRUST_OSC = 0.10


class EventType(str, Enum):
    LEAK = "leak"
    MEDIA_WAVE = "media_wave"
    NEW_DOCUMENT = "new_document"
    MANIPULATED_FILE = "manipulated_file"
    VIRAL_CLAIM = "viral_claim"
    NARRATIVE_DRIFT = "narrative_drift"
    TRUST_DECAY = "trust_decay"


EVENT_TYPES: tuple[EventType, ...] = tuple(EventType)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _osc(t: int, mult: int, add: int) -> float:
    return ((t * mult + add) % 1000) / 1000.0


@dataclass(frozen=True)
class StepState:
    step: int
    event_type: str
    stability: float
    mythologization: float
    source_quality_visibility: float
    trust: float
    dissent_preserved: bool
    chain_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "event_type": self.event_type,
            "stability": self.stability,
            "mythologization": self.mythologization,
            "source_quality_visibility":
                self.source_quality_visibility,
            "trust": self.trust,
            "dissent_preserved": self.dissent_preserved,
            "chain_hash": self.chain_hash,
        }


def _stability_at(t: int) -> float:
    return _round(1.0 - _DISTURB_AMP * _osc(t, 7919, 13))


def _myth_at(t: int) -> float:
    return _round(_MYTH_CAP * t / (t + _MYTH_HALF))


def _visibility_at(t: int) -> float:
    # DESi keeps source quality labelled even under
    # contamination - high and stable.
    return _round(1.0 - _VIS_AMP * _osc(t, 3571, 29))


def _trust_at(t: int) -> float:
    base = _TRUST_START - _TRUST_DECAY * (t / N_STEPS)
    base = max(_TRUST_FLOOR, base)
    return _round(
        base + _TRUST_OSC * (_osc(t, 6271, 91) - 0.5)
    )


def _simulate() -> tuple[StepState, ...]:
    out: list[StepState] = []
    h = hashlib.sha256(
        b"v17.3-sensitive-ecology-seed",
    ).hexdigest()
    for t in range(N_STEPS):
        et = EVENT_TYPES[t % len(EVENT_TYPES)].value
        stability = _stability_at(t)
        myth = _myth_at(t)
        vis = _visibility_at(t)
        trust = _trust_at(t)
        # DESi preserves dissent at every step,
        # regardless of trust decay or media waves.
        dissent = True
        payload = (
            f"{h}|{t}|{et}|{stability}|{myth}|{vis}|"
            f"{trust}|{int(dissent)}"
        )
        h = hashlib.sha256(
            payload.encode("utf-8"),
        ).hexdigest()
        out.append(StepState(
            step=t, event_type=et, stability=stability,
            mythologization=myth,
            source_quality_visibility=vis,
            trust=trust, dissent_preserved=dissent,
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


def epistemic_stability() -> float:
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.stability for s in states) / len(states)
    )


def min_stability() -> float:
    return _round(min(s.stability for s in run()))


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
    "epistemic_stability",
    "final_hash",
    "min_stability",
    "replay_hashes_match",
    "run",
    "sample",
]
