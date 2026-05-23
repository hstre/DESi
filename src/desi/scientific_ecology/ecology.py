"""v13.3 — 5000-step scientific-ecology
trajectory.

Round-robins through three closed input
streams:

  step % 3 == 0  ->  v13.0 paper claims
  step % 3 == 1  ->  v13.1 sludge classifications
  step % 3 == 2  ->  v13.2 manipulation
                     classifications

Each step records a sha256 snapshot of the
closed-enum spaces. Any drift surfaces as
governance erosion.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..adversarial_research.manipulation import (
    MANIPULATION_KINDS,
    fixture as v132_fixture,
)
from ..adversarial_research.selective_reporting import (
    classified_manipulations,
)
from ..paper_integrity.claims import (
    PAPER_CLASSES,
    fixture as v130_fixture,
)
from ..sludge_detection.sludge import (
    SLUDGE_VERDICTS,
    classified_papers,
)


STEP_COUNT: int = 5000


class EcologyStream(str, Enum):
    PAPER         = "paper"
    SLUDGE        = "sludge"
    MANIPULATION  = "manipulation"


ECOLOGY_STREAMS: tuple[str, ...] = tuple(
    s.value for s in EcologyStream
)


@dataclass(frozen=True)
class EcologyStep:
    step: int
    stream: str
    item_id: str
    verdict: str
    closed_enum_hash: str
    cumulative_hash: str
    gate_bypass: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "stream": self.stream,
            "item_id": self.item_id,
            "verdict": self.verdict,
            "closed_enum_hash":
                self.closed_enum_hash,
            "cumulative_hash":
                self.cumulative_hash,
            "gate_bypass": self.gate_bypass,
        }


def _closed_enum_hash() -> str:
    raw = repr((
        tuple(PAPER_CLASSES),
        tuple(SLUDGE_VERDICTS),
        tuple(MANIPULATION_KINDS),
    ))
    return hashlib.sha256(
        raw.encode("utf-8"),
    ).hexdigest()[:16]


def _paper_step(item) -> tuple[str, str]:
    return (item.paper_id, item.paper_class)


def _sludge_step(item) -> tuple[str, str]:
    return (item.paper_id, item.verdict)


def _manipulation_step(item) -> tuple[
    str, str,
]:
    return (item.claim_id, item.detected_kind)


_VALID_VERDICTS: frozenset[str] = (
    frozenset(PAPER_CLASSES)
    | frozenset(SLUDGE_VERDICTS)
    | frozenset(MANIPULATION_KINDS)
)


@lru_cache(maxsize=1)
def trajectory() -> tuple[EcologyStep, ...]:
    out: list[EcologyStep] = []
    running = b""
    papers = v130_fixture()
    sludge = classified_papers()
    mans = classified_manipulations()
    for step in range(STEP_COUNT):
        idx = step // 3
        ceh = _closed_enum_hash()
        if step % 3 == 0:
            item = papers[idx % len(papers)]
            stream = EcologyStream.PAPER
            sid, verdict = _paper_step(item)
        elif step % 3 == 1:
            item = sludge[idx % len(sludge)]
            stream = EcologyStream.SLUDGE
            sid, verdict = _sludge_step(item)
        else:
            item = mans[idx % len(mans)]
            stream = EcologyStream.MANIPULATION
            sid, verdict = _manipulation_step(
                item,
            )
        bypass = verdict not in _VALID_VERDICTS
        running = hashlib.sha256(
            running
            + f"{step}:{stream.value}:{sid}:"
              f"{verdict}:{ceh}:{bypass}"
              .encode("utf-8"),
        ).digest()
        out.append(EcologyStep(
            step=step, stream=stream.value,
            item_id=sid, verdict=verdict,
            closed_enum_hash=ceh,
            cumulative_hash=running.hex()[:16],
            gate_bypass=bypass,
        ))
    return tuple(out)


def replay_trajectory() -> tuple[
    EcologyStep, ...,
]:
    trajectory.cache_clear()
    return trajectory()


def trajectory_final_hash() -> str:
    t = trajectory()
    return t[-1].cumulative_hash if t else ""


__all__ = [
    "ECOLOGY_STREAMS",
    "EcologyStep",
    "EcologyStream",
    "STEP_COUNT",
    "replay_trajectory",
    "trajectory",
    "trajectory_final_hash",
]
