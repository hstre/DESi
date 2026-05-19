"""v10.3 — 10000-step institutional-drift
trajectory.

Round-robins through three closed input streams:

  step % 3 == 0  ->  v10.0 institutions
  step % 3 == 1  ->  v10.1 layered decisions
  step % 3 == 2  ->  v10.2 past decisions

Each step records a sha256 snapshot of the
closed-enum spaces (institution kinds,
governance layers, precedent kinds) PLUS the
power_share / authority alignment / validity
flag of the consumed item. Any closed-enum
mutation surfaces as ``institutional_capture``;
any gate bypass attempt surfaces in the
``gate_bypass`` flag.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..governance_layering.layers import (
    GOVERNANCE_LAYERS,
    fixture as v101_fixture,
)
from ..institutional_governance.institutions import (
    INSTITUTION_KINDS,
    fixture as v100_fixture,
)
from ..path_dependence.memory import (
    PRECEDENT_KINDS,
    fixture as v102_fixture,
)


STEP_COUNT: int = 10000


class InstitutionalStream(str, Enum):
    INSTITUTION  = "institution"
    LAYER        = "layer"
    PRECEDENT    = "precedent"


INSTITUTIONAL_STREAMS: tuple[str, ...] = tuple(
    s.value for s in InstitutionalStream
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
class InstitutionalStep:
    step: int
    stream: str
    item_id: str
    quality_score: float
    closed_enum_hash: str
    cumulative_hash: str
    gate_bypass: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "stream": self.stream,
            "item_id": self.item_id,
            "quality_score":
                self.quality_score,
            "closed_enum_hash":
                self.closed_enum_hash,
            "cumulative_hash":
                self.cumulative_hash,
            "gate_bypass": self.gate_bypass,
        }


def _closed_enum_hash() -> str:
    raw = repr((
        tuple(INSTITUTION_KINDS),
        tuple(GOVERNANCE_LAYERS),
        tuple(PRECEDENT_KINDS),
    ))
    return hashlib.sha256(
        raw.encode("utf-8"),
    ).hexdigest()[:16]


def _institution_step(item) -> tuple[str, float]:
    return (
        item.institution_id,
        item.trust_index,
    )


def _layer_step(item) -> tuple[str, float]:
    # Quality = aligns_with_parent flag mapped
    # to 1.0/0.0.
    return (
        item.decision_id,
        1.0 if item.aligns_with_parent else 0.0,
    )


def _precedent_step(item) -> tuple[str, float]:
    return (
        item.decision_id,
        1.0 if item.is_currently_valid else 0.0,
    )


def _is_gate_bypass(label: str) -> bool:
    low = label.lower()
    return any(
        tok.lower() in low
        for tok in _FORBIDDEN_TARGET_TOKENS
    )


@lru_cache(maxsize=1)
def trajectory() -> tuple[
    InstitutionalStep, ...,
]:
    out: list[InstitutionalStep] = []
    running = b""
    for step in range(STEP_COUNT):
        idx = step // 3
        ceh = _closed_enum_hash()
        if step % 3 == 0:
            pool = v100_fixture()
            item = pool[idx % len(pool)]
            stream = (
                InstitutionalStream.INSTITUTION
            )
            sid, q = _institution_step(item)
        elif step % 3 == 1:
            pool = v101_fixture()
            item = pool[idx % len(pool)]
            stream = (
                InstitutionalStream.LAYER
            )
            sid, q = _layer_step(item)
        else:
            pool = v102_fixture()
            item = pool[idx % len(pool)]
            stream = (
                InstitutionalStream.PRECEDENT
            )
            sid, q = _precedent_step(item)
        bypass = _is_gate_bypass(sid)
        running = hashlib.sha256(
            running
            + f"{step}:{stream.value}:{sid}:"
              f"{q}:{ceh}:{bypass}"
              .encode("utf-8"),
        ).digest()
        out.append(InstitutionalStep(
            step=step, stream=stream.value,
            item_id=sid, quality_score=q,
            closed_enum_hash=ceh,
            cumulative_hash=running.hex()[:16],
            gate_bypass=bypass,
        ))
    return tuple(out)


def replay_trajectory() -> tuple[
    InstitutionalStep, ...,
]:
    trajectory.cache_clear()
    return trajectory()


def trajectory_final_hash() -> str:
    t = trajectory()
    return t[-1].cumulative_hash if t else ""


__all__ = [
    "INSTITUTIONAL_STREAMS",
    "InstitutionalStep",
    "InstitutionalStream",
    "STEP_COUNT",
    "replay_trajectory",
    "trajectory",
    "trajectory_final_hash",
]
