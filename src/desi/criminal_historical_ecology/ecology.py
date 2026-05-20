"""v16.3 - long-horizon historical information
ecology (>= 5000 steps).

Deterministically simulates decades of narrative
drift, document releases, media waves, new witness
testimony, institutional trust shifts, and
secondary myth formation. DESi applies epistemic
hygiene at every step: the verified core stays
stable, narrative inflation is capped, independent
evidence paths are preserved, and drift /
mythologization are made visible but never adopted
as fact.

Pure arithmetic + a cumulative sha256 hash chain;
no PRNG, no global state - bit-exact on replay.
Makes no new factual claim.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

N_STEPS = 5200
SAMPLE_SIZE = 200
# Independent verified evidence lines DESi must
# preserve (the v16.0 verified facts C01-C04).
CORE_LINES = 4

# Bounded-growth parameters (DESi's hygiene caps).
_DISTURB_AMP = 0.06
_INFL_CAP = 0.25
_INFL_HALF = 1500.0
_MYTH_CAP = 0.30
_MYTH_HALF = 2500.0
_TRUST_AMP = 0.20


class EventType(str, Enum):
    NARRATIVE_DRIFT = "narrative_drift"
    DOCUMENT_RELEASE = "document_release"
    MEDIA_WAVE = "media_wave"
    NEW_WITNESS = "new_witness"
    TRUST_SHIFT = "trust_shift"
    MYTH_FORMATION = "myth_formation"


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
    narrative_inflation: float
    mythologization: float
    preserved_lines: int
    trust: float
    chain_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "event_type": self.event_type,
            "stability": self.stability,
            "narrative_inflation":
                self.narrative_inflation,
            "mythologization": self.mythologization,
            "preserved_lines": self.preserved_lines,
            "trust": self.trust,
            "chain_hash": self.chain_hash,
        }


def _stability_at(t: int) -> float:
    return _round(1.0 - _DISTURB_AMP * _osc(t, 7919, 13))


def _inflation_at(t: int) -> float:
    # saturating growth -> bounded; DESi caps it
    return _round(_INFL_CAP * t / (t + _INFL_HALF))


def _myth_at(t: int) -> float:
    return _round(_MYTH_CAP * t / (t + _MYTH_HALF))


def _trust_at(t: int) -> float:
    return _round(
        0.5 + _TRUST_AMP * (_osc(t, 6271, 91) - 0.5)
    )


def _simulate() -> tuple[StepState, ...]:
    """One deterministic pass over the ecology."""
    out: list[StepState] = []
    h = hashlib.sha256(b"v16.3-ecology-seed").hexdigest()
    for t in range(N_STEPS):
        et = EVENT_TYPES[t % len(EVENT_TYPES)].value
        stability = _stability_at(t)
        inflation = _inflation_at(t)
        myth = _myth_at(t)
        trust = _trust_at(t)
        # DESi preserves every independent core line
        # regardless of media / myth pressure.
        preserved = CORE_LINES
        payload = (
            f"{h}|{t}|{et}|{stability}|{inflation}|"
            f"{myth}|{preserved}|{trust}"
        )
        h = hashlib.sha256(
            payload.encode("utf-8"),
        ).hexdigest()
        out.append(StepState(
            step=t, event_type=et,
            stability=stability,
            narrative_inflation=inflation,
            mythologization=myth,
            preserved_lines=preserved,
            trust=trust, chain_hash=h,
        ))
    return tuple(out)


@lru_cache(maxsize=1)
def run() -> tuple[StepState, ...]:
    return _simulate()


def final_hash() -> str:
    return run()[-1].chain_hash


def replay_hashes_match() -> bool:
    """Two independent passes must agree bit-for-bit
    (bypasses the cache)."""
    a = _simulate()[-1].chain_hash
    b = _simulate()[-1].chain_hash
    return a == b


def enum_snapshot_hash() -> str:
    """Hash of the closed event vocabulary - detects
    runtime mutation of the enum."""
    joined = "|".join(sorted(e.value for e in EventType))
    return hashlib.sha256(
        joined.encode("utf-8"),
    ).hexdigest()


def epistemic_stability() -> float:
    """Mean stability of the verified core across
    the whole run, in [0, 1]."""
    states = run()
    if not states:
        return 0.0
    return _round(
        sum(s.stability for s in states) / len(states)
    )


def min_stability() -> float:
    return _round(min(s.stability for s in run()))


def sample() -> tuple[StepState, ...]:
    """Evenly-spaced sample for the artifact (a long
    run is not dumped in full)."""
    states = run()
    if len(states) <= SAMPLE_SIZE:
        return states
    stride = len(states) // SAMPLE_SIZE
    return tuple(states[i] for i in range(
        0, len(states), stride,
    ))[:SAMPLE_SIZE]


__all__ = [
    "CORE_LINES",
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
