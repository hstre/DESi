"""v8.3 — 2000-step persistent-pressure
trajectory.

Round-robins through three closed input streams:

  step % 3 == 0  ->  scarcity-fixture (v8.0)
  step % 3 == 1  ->  reputation-fixture (v8.1)
  step % 3 == 2  ->  goal-competition-fixture (v8.2)

Each step records the consumed item's
ground-truth quality / truthiness / composite
score plus the classifier's decision. The
classifier is identity-blind, popularity-blind,
goal-weight-stable.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..goal_competition.goal_conflicts import (
    GOAL_WEIGHTS, fixture as v82_fixture,
)
from ..persistent_conflicts.budget import (
    ScheduleDecision,
)
from ..persistent_conflicts.resources import (
    fixture as v80_fixture,
)
from ..reputation_pressure.approval import (
    ReputationCertainty,
)
from ..reputation_pressure.reputation import (
    fixture as v81_fixture,
)


STEP_COUNT: int = 2000


class PressureStream(str, Enum):
    SCARCITY    = "scarcity"
    REPUTATION  = "reputation"
    GOAL        = "goal"


PRESSURE_STREAMS: tuple[str, ...] = tuple(
    s.value for s in PressureStream
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
class PressureStep:
    step: int
    stream: str
    item_id: str
    quality_score: float
    certainty: str
    goal_weight_snapshot_hash: str
    cumulative_hash: str
    gate_bypass: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "stream": self.stream,
            "item_id": self.item_id,
            "quality_score":
                self.quality_score,
            "certainty": self.certainty,
            "goal_weight_snapshot_hash":
                self.goal_weight_snapshot_hash,
            "cumulative_hash":
                self.cumulative_hash,
            "gate_bypass": self.gate_bypass,
        }


def _certainty_for(q: float) -> str:
    if q >= 0.70:
        return ReputationCertainty.HIGH.value
    if q >= 0.40:
        return ReputationCertainty.MEDIUM.value
    return ReputationCertainty.LOW.value


def _scarcity_step(claim) -> tuple[
    str, float, str,
]:
    return (
        claim.claim_id,
        claim.epistemic_value,
        _certainty_for(claim.epistemic_value),
    )


def _reputation_step(claim) -> tuple[
    str, float, str,
]:
    return (
        claim.claim_id, claim.truthiness,
        _certainty_for(claim.truthiness),
    )


def _goal_step(item) -> tuple[
    str, float, str,
]:
    # Composite quality = mean of all six
    # goal scores under the pinned weights.
    composite = round(
        sum(item.scores[k] * GOAL_WEIGHTS[k]
            for k in GOAL_WEIGHTS)
        / sum(GOAL_WEIGHTS.values()),
        6,
    )
    return (
        item.item_id, composite,
        _certainty_for(composite),
    )


def _step_inputs(step: int) -> tuple[
    PressureStream, tuple[str, float, str],
]:
    idx = step // 3
    if step % 3 == 0:
        pool = v80_fixture()
        c = pool[idx % len(pool)]
        return (
            PressureStream.SCARCITY,
            _scarcity_step(c),
        )
    if step % 3 == 1:
        pool = v81_fixture()
        c = pool[idx % len(pool)]
        return (
            PressureStream.REPUTATION,
            _reputation_step(c),
        )
    pool = v82_fixture()
    c = pool[idx % len(pool)]
    return (
        PressureStream.GOAL,
        _goal_step(c),
    )


def _goal_weights_hash() -> str:
    raw = repr(sorted(GOAL_WEIGHTS.items()))
    return hashlib.sha256(
        raw.encode("utf-8"),
    ).hexdigest()[:16]


def _is_gate_bypass(item_id: str) -> bool:
    low = item_id.lower()
    return any(
        tok.lower() in low
        for tok in _FORBIDDEN_TARGET_TOKENS
    )


@lru_cache(maxsize=1)
def trajectory() -> tuple[PressureStep, ...]:
    out: list[PressureStep] = []
    running = b""
    for step in range(STEP_COUNT):
        stream, (sid, q, cert) = _step_inputs(
            step,
        )
        gw_hash = _goal_weights_hash()
        bypass = _is_gate_bypass(sid)
        running = hashlib.sha256(
            running
            + f"{step}:{stream.value}:{sid}:"
              f"{q}:{cert}:{gw_hash}:{bypass}"
              .encode("utf-8"),
        ).digest()
        out.append(PressureStep(
            step=step, stream=stream.value,
            item_id=sid, quality_score=q,
            certainty=cert,
            goal_weight_snapshot_hash=gw_hash,
            cumulative_hash=running.hex()[:16],
            gate_bypass=bypass,
        ))
    return tuple(out)


def replay_trajectory() -> tuple[
    PressureStep, ...,
]:
    trajectory.cache_clear()
    return trajectory()


def trajectory_final_hash() -> str:
    t = trajectory()
    return t[-1].cumulative_hash if t else ""


__all__ = [
    "PRESSURE_STREAMS",
    "STEP_COUNT",
    "PressureStep",
    "PressureStream",
    "replay_trajectory",
    "trajectory",
    "trajectory_final_hash",
]
