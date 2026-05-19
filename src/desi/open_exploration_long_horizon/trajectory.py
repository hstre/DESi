"""v12.3 — 5000-step long-horizon trajectory.

Round-robins through three closed input
streams:

  step % 3 == 0  ->  v12.0 wild hypotheses
  step % 3 == 1  ->  v12.1 governed groups
  step % 3 == 2  ->  v12.2 false-pattern
                     classifications

Within each stream the pool is cycled by
``step // 3`` so the per-pool index doesn't
alias against the stream selector. Every step
records the consumed item's epistemic status
plus a sha256 closed-enum snapshot.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..false_patterns.pattern_detection import (
    classified_patterns as v122_patterns,
)
from ..governed_exploration.compression import (
    compressed_groups,
)
from ..open_math.explorer import (
    HYPOTHESIS_SHAPES,
    fixture as v120_fixture,
)
from ..open_math.governance import (
    governed_hypotheses,
)
from ..open_math.hypotheses import (
    EPISTEMIC_STATUSES,
)


STEP_COUNT: int = 5000


class LongHorizonStream(str, Enum):
    WILD      = "wild"
    GOVERNED  = "governed"
    PATTERN   = "pattern"


LONG_HORIZON_STREAMS: tuple[str, ...] = tuple(
    s.value for s in LongHorizonStream
)


@dataclass(frozen=True)
class LongHorizonStep:
    step: int
    stream: str
    item_id: str
    status: str
    closed_enum_hash: str
    cumulative_hash: str
    governance_bypass: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "stream": self.stream,
            "item_id": self.item_id,
            "status": self.status,
            "closed_enum_hash":
                self.closed_enum_hash,
            "cumulative_hash":
                self.cumulative_hash,
            "governance_bypass":
                self.governance_bypass,
        }


def _closed_enum_hash() -> str:
    raw = repr((
        tuple(EPISTEMIC_STATUSES),
        tuple(HYPOTHESIS_SHAPES),
    ))
    return hashlib.sha256(
        raw.encode("utf-8"),
    ).hexdigest()[:16]


def _wild_step(item) -> tuple[str, str]:
    return (
        item.hypothesis_id,
        item.ground_truth_status,
    )


def _governed_step(
    group: tuple[str, tuple[str, ...]],
) -> tuple[str, str]:
    key, _ = group
    # key is "status|shape"
    status = key.split("|", 1)[0]
    return (key, status)


def _pattern_step(item) -> tuple[str, str]:
    return (
        item.claim_id,
        item.detected_kind,
    )


@lru_cache(maxsize=1)
def trajectory() -> tuple[
    LongHorizonStep, ...,
]:
    out: list[LongHorizonStep] = []
    running = b""
    wild = v120_fixture()
    grouped = compressed_groups()
    patterns = v122_patterns()
    for step in range(STEP_COUNT):
        idx = step // 3
        ceh = _closed_enum_hash()
        if step % 3 == 0:
            item = wild[idx % len(wild)]
            stream = LongHorizonStream.WILD
            sid, status = _wild_step(item)
        elif step % 3 == 1:
            item = grouped[
                idx % len(grouped)
            ]
            stream = LongHorizonStream.GOVERNED
            sid, status = _governed_step(item)
        else:
            item = patterns[
                idx % len(patterns)
            ]
            stream = LongHorizonStream.PATTERN
            sid, status = _pattern_step(item)
        # Governance bypass = unknown status
        # somehow escaping the closed enum.
        bypass = status not in (
            EPISTEMIC_STATUSES
        ) and status not in {
            "numerological", "small_sample",
            "spurious_cluster",
            "overfit_regularity", "genuine",
        }
        running = hashlib.sha256(
            running
            + f"{step}:{stream.value}:{sid}:"
              f"{status}:{ceh}:{bypass}"
              .encode("utf-8"),
        ).digest()
        out.append(LongHorizonStep(
            step=step, stream=stream.value,
            item_id=sid, status=status,
            closed_enum_hash=ceh,
            cumulative_hash=running.hex()[:16],
            governance_bypass=bypass,
        ))
    return tuple(out)


def replay_trajectory() -> tuple[
    LongHorizonStep, ...,
]:
    trajectory.cache_clear()
    return trajectory()


def trajectory_final_hash() -> str:
    t = trajectory()
    return t[-1].cumulative_hash if t else ""


__all__ = [
    "LONG_HORIZON_STREAMS",
    "LongHorizonStep",
    "LongHorizonStream",
    "STEP_COUNT",
    "replay_trajectory",
    "trajectory",
    "trajectory_final_hash",
]
