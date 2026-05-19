"""v9.3 — 5000-step strategic-pressure
trajectory.

Round-robins through three closed input streams:

  step % 3 == 0  ->  actor-ecology (v9.0)
  step % 3 == 1  ->  gaming attempts (v9.1)
  step % 3 == 2  ->  broadcast lineage (v9.2)

Each step records the detector verdict plus a
sha256 snapshot of the governance closed-enum
set, so any runtime mutation surfaces in
``capture_risk``.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..coalition_warfare.coalitions import (
    CoalitionRole, fixture as v92_fixture,
)
from ..coalition_warfare.lineage import (
    detected_coalitions,
)
from ..governance_gaming.gaming import (
    GamingKind, fixture as v91_fixture,
)
from ..governance_gaming.rule_exploitation import (
    detect_kind as gaming_detect,
)
from ..strategic_epistemics.actors import (
    ActorKind, fixture as v90_fixture,
)
from ..strategic_epistemics.strategies import (
    classify_actor,
)
from ..strategic_epistemics.trust import (
    trust_score_for,
)


STEP_COUNT: int = 5000


class StrategicStream(str, Enum):
    ACTOR_ECOLOGY  = "actor_ecology"
    GAMING         = "gaming"
    COALITION      = "coalition"


STRATEGIC_STREAMS: tuple[str, ...] = tuple(
    s.value for s in StrategicStream
)


_FORBIDDEN_TARGET_TOKENS: tuple[str, ...] = (
    "src/desi/pre_t10_rule",
    "src/desi/pre_t10_v2/rule.py",
    "src/desi/pre_t10_v2_deploy/decision.py",
    "BLINDNESS_CHECK_THRESHOLD",
    "auto_deploy", "self_modify",
    "skip_gate", "disable_check",
)


@dataclass(frozen=True)
class StrategicStep:
    step: int
    stream: str
    source_id: str
    verdict: str
    trust: float
    governance_snapshot_hash: str
    cumulative_hash: str
    gate_bypass: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "stream": self.stream,
            "source_id": self.source_id,
            "verdict": self.verdict,
            "trust": self.trust,
            "governance_snapshot_hash":
                self.governance_snapshot_hash,
            "cumulative_hash":
                self.cumulative_hash,
            "gate_bypass": self.gate_bypass,
        }


def _governance_snapshot_hash() -> str:
    raw = repr((
        tuple(k.value for k in ActorKind),
        tuple(k.value for k in GamingKind),
        tuple(k.value for k in CoalitionRole),
    ))
    return hashlib.sha256(
        raw.encode("utf-8"),
    ).hexdigest()[:16]


def _actor_step(item) -> tuple[str, str, float]:
    detected = classify_actor(item)
    trust = trust_score_for(detected.value)
    return (
        item.actor_id, detected.value, trust,
    )


def _gaming_step(item) -> tuple[
    str, str, float,
]:
    detected = gaming_detect(item.text)
    trust = (
        1.0 if detected == GamingKind.NORMAL
        else 0.0
    )
    return (
        item.attempt_id, detected.value, trust,
    )


def _coalition_step(item) -> tuple[
    str, str, float,
]:
    in_coalition = any(
        item.broadcast_id in members
        for _, members in detected_coalitions()
    )
    verdict = (
        "coalition_member" if in_coalition
        else item.coalition_role
    )
    trust = (
        0.1 if in_coalition
        else 1.0 if item.coalition_role == (
            CoalitionRole.DISSENTER.value
        )
        else 0.7
    )
    return (
        item.broadcast_id, verdict, trust,
    )


def _is_gate_bypass(label: str) -> bool:
    low = label.lower()
    return any(
        tok.lower() in low
        for tok in _FORBIDDEN_TARGET_TOKENS
    )


@lru_cache(maxsize=1)
def trajectory() -> tuple[StrategicStep, ...]:
    out: list[StrategicStep] = []
    running = b""
    for step in range(STEP_COUNT):
        idx = step // 3
        gh = _governance_snapshot_hash()
        if step % 3 == 0:
            pool = v90_fixture()
            item = pool[idx % len(pool)]
            stream = StrategicStream.ACTOR_ECOLOGY
            sid, verdict, trust = _actor_step(
                item,
            )
        elif step % 3 == 1:
            pool = v91_fixture()
            item = pool[idx % len(pool)]
            stream = StrategicStream.GAMING
            sid, verdict, trust = _gaming_step(
                item,
            )
        else:
            pool = v92_fixture()
            item = pool[idx % len(pool)]
            stream = StrategicStream.COALITION
            sid, verdict, trust = (
                _coalition_step(item)
            )
        bypass = _is_gate_bypass(sid)
        running = hashlib.sha256(
            running
            + f"{step}:{stream.value}:{sid}:"
              f"{verdict}:{trust}:{gh}:{bypass}"
              .encode("utf-8"),
        ).digest()
        out.append(StrategicStep(
            step=step, stream=stream.value,
            source_id=sid, verdict=verdict,
            trust=trust,
            governance_snapshot_hash=gh,
            cumulative_hash=running.hex()[:16],
            gate_bypass=bypass,
        ))
    return tuple(out)


def replay_trajectory() -> tuple[
    StrategicStep, ...,
]:
    trajectory.cache_clear()
    return trajectory()


def trajectory_final_hash() -> str:
    t = trajectory()
    return t[-1].cumulative_hash if t else ""


__all__ = [
    "STEP_COUNT",
    "STRATEGIC_STREAMS",
    "StrategicStep",
    "StrategicStream",
    "replay_trajectory",
    "trajectory",
    "trajectory_final_hash",
]
