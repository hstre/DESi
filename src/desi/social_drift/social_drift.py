"""v7.3 — 1000-step social-drift trajectory.

Round-robins through three closed input streams:

  step % 3 == 0  ->  narrative_pressure (v7.0)
  step % 3 == 1  ->  tribal_conflicts   (v7.1)
  step % 3 == 2  ->  virality_pressure  (v7.2)

Each step classifies the consumed claim using
the closed Certainty enum and records a
deterministic step. The classifier is
identity-blind, virality-blind, narrative-aware
- exactly as v7.0/7.1/7.2 require.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..social_reality.frames import (
    FrameCertainty,
)
from ..social_reality.narratives import (
    NarrativeKind, fixture as v70_fixture,
)
from ..social_reality.pressure import (
    pressure_axes, under_pressure,
)
from ..tribal_conflicts.identity import (
    IdentityCertainty,
)
from ..tribal_conflicts.tribes import (
    fixture as v71_fixture,
)
from ..virality_pressure.attention import (
    ViralCertainty,
)
from ..virality_pressure.virality import (
    fixture as v72_fixture,
)


STEP_COUNT: int = 1000


class SocialStream(str, Enum):
    NARRATIVE  = "narrative"
    TRIBAL     = "tribal"
    VIRALITY   = "virality"


SOCIAL_STREAMS: tuple[str, ...] = tuple(
    s.value for s in SocialStream
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
class SocialStep:
    step: int
    stream: str
    source_id: str
    source_label: str
    certainty: str
    under_pressure: bool
    pressure_axes: tuple[str, ...]
    cumulative_hash: str
    gate_bypass: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "stream": self.stream,
            "source_id": self.source_id,
            "source_label": self.source_label,
            "certainty": self.certainty,
            "under_pressure":
                self.under_pressure,
            "pressure_axes":
                list(self.pressure_axes),
            "cumulative_hash":
                self.cumulative_hash,
            "gate_bypass": self.gate_bypass,
        }


def _narrative_step(claim) -> tuple[
    str, str, str, bool, tuple[str, ...],
]:
    axes = pressure_axes(claim.text)
    pressed = bool(axes)
    if pressed:
        cert = FrameCertainty.LOW.value
    elif (
        claim.narrative_kind
        == NarrativeKind.NEUTRAL_REPORT.value
    ):
        cert = FrameCertainty.HIGH.value
    else:
        cert = FrameCertainty.MEDIUM.value
    return (
        claim.claim_id,
        claim.narrative_kind,
        cert, pressed, axes,
    )


def _tribal_step(claim) -> tuple[
    str, str, str, bool, tuple[str, ...],
]:
    q = claim.epistemic_quality
    if q >= 0.70:
        cert = IdentityCertainty.HIGH.value
    elif q >= 0.40:
        cert = IdentityCertainty.MEDIUM.value
    else:
        cert = IdentityCertainty.LOW.value
    return (
        claim.claim_id, claim.tribe,
        cert, False, (),
    )


def _virality_step(claim) -> tuple[
    str, str, str, bool, tuple[str, ...],
]:
    t = claim.truthiness
    if t >= 0.70:
        cert = ViralCertainty.HIGH.value
    elif t >= 0.40:
        cert = ViralCertainty.MEDIUM.value
    else:
        cert = ViralCertainty.LOW.value
    label = (
        "high_truth" if t >= 0.70
        else "low_truth" if t < 0.40
        else "mid_truth"
    )
    return (
        claim.claim_id, label,
        cert, False, (),
    )


def _step_inputs(step: int) -> tuple[
    SocialStream, tuple[
        str, str, str, bool, tuple[str, ...],
    ],
]:
    """Round-robin streams; within each stream
    cycle the pool by ``step // 3`` to avoid
    aliasing the per-pool index against the
    stream selector."""
    idx = step // 3
    if step % 3 == 0:
        pool = v70_fixture()
        c = pool[idx % len(pool)]
        return (
            SocialStream.NARRATIVE,
            _narrative_step(c),
        )
    if step % 3 == 1:
        pool = v71_fixture()
        c = pool[idx % len(pool)]
        return (
            SocialStream.TRIBAL,
            _tribal_step(c),
        )
    pool = v72_fixture()
    c = pool[idx % len(pool)]
    return (
        SocialStream.VIRALITY,
        _virality_step(c),
    )


def _is_gate_bypass(label: str) -> bool:
    low = label.lower()
    return any(
        tok.lower() in low
        for tok in _FORBIDDEN_TARGET_TOKENS
    )


@lru_cache(maxsize=1)
def trajectory() -> tuple[SocialStep, ...]:
    out: list[SocialStep] = []
    running = b""
    for step in range(STEP_COUNT):
        stream, payload = _step_inputs(step)
        sid, label, cert, pressed, axes = (
            payload
        )
        bypass = _is_gate_bypass(label)
        running = hashlib.sha256(
            running
            + f"{step}:{stream.value}:{sid}:"
              f"{cert}:{pressed}:{bypass}"
              .encode("utf-8"),
        ).digest()
        out.append(SocialStep(
            step=step, stream=stream.value,
            source_id=sid,
            source_label=label,
            certainty=cert,
            under_pressure=pressed,
            pressure_axes=axes,
            cumulative_hash=(
                running.hex()[:16]
            ),
            gate_bypass=bypass,
        ))
    return tuple(out)


def replay_trajectory() -> tuple[
    SocialStep, ...,
]:
    trajectory.cache_clear()
    return trajectory()


def trajectory_final_hash() -> str:
    t = trajectory()
    return t[-1].cumulative_hash if t else ""


__all__ = [
    "SOCIAL_STREAMS",
    "STEP_COUNT",
    "SocialStep",
    "SocialStream",
    "replay_trajectory",
    "trajectory",
    "trajectory_final_hash",
]
