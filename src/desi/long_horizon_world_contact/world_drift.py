"""v6.3 — 500-step world-contact trajectory.

At each step DESi consumes one item from one of
three closed input streams - paper claims
(v6.0), adversarial claims (v6.1), or
ecology-corpus claims (v6.2) - and runs it
through the trap detector + ambiguity detector.
Every step record is a deterministic function
of (step_index, input_stream, source_item).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..adversarial_claims.adversarial import (
    TrapKind, detect_trap, trapped_claims,
)
from ..adversarial_claims.ambiguity import (
    AmbiguityKind, detect_ambiguity,
)
from ..adversarial_claims.conflict_injector import (
    Certainty,
)
from ..conflict_ecology.cross_paper import (
    corpus as ecology_corpus,
)
from ..world_contact.claim_extractor import (
    ExtractedKind, corpus_extractions,
)


STEP_COUNT: int = 500


class StreamKind(str, Enum):
    PAPER       = "paper"
    ADVERSARIAL = "adversarial"
    ECOLOGY     = "ecology"


STREAM_KINDS: tuple[str, ...] = tuple(
    s.value for s in StreamKind
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
class WorldStep:
    step: int
    stream: str
    source_id: str
    text: str
    detected_trap: str
    detected_ambiguity: str
    certainty: str
    cumulative_hash: str
    hallucinated: bool
    gate_bypass: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "stream": self.stream,
            "source_id": self.source_id,
            "text": self.text,
            "detected_trap":
                self.detected_trap,
            "detected_ambiguity":
                self.detected_ambiguity,
            "certainty": self.certainty,
            "cumulative_hash":
                self.cumulative_hash,
            "hallucinated":
                self.hallucinated,
            "gate_bypass": self.gate_bypass,
        }


def _paper_claim_pool() -> tuple[
    tuple[str, str], ...,
]:
    pool: list[tuple[str, str]] = []
    for paper, units in corpus_extractions():
        for u in units:
            if u.kind == (
                ExtractedKind.CLAIM.value
            ):
                pool.append((
                    paper.paper_id, u.sentence,
                ))
    return tuple(pool)


def _adversarial_claim_pool() -> tuple[
    tuple[str, str], ...,
]:
    return tuple(
        (c.claim_id, c.text)
        for c in trapped_claims()
    )


def _ecology_claim_pool() -> tuple[
    tuple[str, str], ...,
]:
    return tuple(
        (p.paper_id, p.text)
        for p in ecology_corpus()
    )


@lru_cache(maxsize=1)
def _all_pools() -> dict[
    str, tuple[tuple[str, str], ...],
]:
    return {
        StreamKind.PAPER.value:
            _paper_claim_pool(),
        StreamKind.ADVERSARIAL.value:
            _adversarial_claim_pool(),
        StreamKind.ECOLOGY.value:
            _ecology_claim_pool(),
    }


def _certainty_for(
    trap: TrapKind, amb: AmbiguityKind,
) -> Certainty:
    if trap != TrapKind.NORMAL:
        return Certainty.LOW
    if amb != AmbiguityKind.NONE:
        return Certainty.MEDIUM
    return Certainty.HIGH


def _step_stream(step: int) -> StreamKind:
    return (
        StreamKind.PAPER,
        StreamKind.ADVERSARIAL,
        StreamKind.ECOLOGY,
    )[step % 3]


def _is_hallucinated(
    text: str, source_pool: tuple[
        tuple[str, str], ...,
    ],
) -> bool:
    for _, t in source_pool:
        if text == t:
            return False
    return True


def _is_gate_bypass(text: str) -> bool:
    low = text.lower()
    return any(
        tok.lower() in low
        for tok in _FORBIDDEN_TARGET_TOKENS
    )


@lru_cache(maxsize=1)
def trajectory() -> tuple[WorldStep, ...]:
    pools = _all_pools()
    out: list[WorldStep] = []
    running = b""
    for step in range(STEP_COUNT):
        stream = _step_stream(step)
        pool = pools[stream.value]
        if not pool:
            continue
        source_id, text = pool[
            step % len(pool)
        ]
        trap = detect_trap(text)
        amb = detect_ambiguity(text)
        cert = _certainty_for(trap, amb)
        hallucinated = _is_hallucinated(
            text, pool,
        )
        bypass = _is_gate_bypass(text)
        running = hashlib.sha256(
            running
            + f"{step}:{stream.value}:"
              f"{source_id}:{trap.value}:"
              f"{cert.value}:{hallucinated}:"
              f"{bypass}"
              .encode("utf-8"),
        ).digest()
        out.append(WorldStep(
            step=step, stream=stream.value,
            source_id=source_id, text=text,
            detected_trap=trap.value,
            detected_ambiguity=amb.value,
            certainty=cert.value,
            cumulative_hash=(
                running.hex()[:16]
            ),
            hallucinated=hallucinated,
            gate_bypass=bypass,
        ))
    return tuple(out)


def replay_trajectory() -> tuple[
    WorldStep, ...,
]:
    trajectory.cache_clear()
    return trajectory()


def trajectory_final_hash() -> str:
    t = trajectory()
    if not t:
        return ""
    return t[-1].cumulative_hash


__all__ = [
    "STEP_COUNT",
    "STREAM_KINDS",
    "StreamKind",
    "WorldStep",
    "replay_trajectory",
    "trajectory",
    "trajectory_final_hash",
]
