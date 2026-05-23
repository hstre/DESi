"""v27.3 - long-horizon research ecology (5200 steps).

A deterministic, replay-exact simulation of research evolution
over the corpus: method trends rise and fall, hype waves
oscillate, ideas go dormant and are rediscovered. Everything is
computed by fixed arithmetic over the corpus (no PRNG, no learned
model). Crucially, nothing is ever deleted - a dormant method
stays present at low strength - so research plurality, fragile
claims and open questions are preserved throughout. A hash chain
makes the whole run replay-verifiable.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache

from desi.research_harvester import (
    all_claims, all_methods, papers,
)
from desi.research_harvester.taxonomy import ClaimClass as K

_STEPS = 5200
_LOW = 0.05          # floor strength: dormant, never deleted
_DORMANT_BELOW = 0.20
_SAMPLE_EVERY = 26   # -> 200 sampled steps


def _osc(t: int, mult: int, add: int) -> float:
    return ((t * mult + add) % 1000) / 1000.0


def _topics() -> tuple[str, ...]:
    seen: set[str] = set()
    for p in papers():
        seen.update(p.metadata.categories)
    return tuple(sorted(seen))


def _strength(idx: int, t: int) -> float:
    mult = 7 + 3 * idx
    add = 11 * idx + 1
    return _LOW + (1.0 - _LOW) * _osc(t, mult, add)


def _hype(idx: int, t: int) -> float:
    mult = 13 + 5 * idx
    add = 17 * idx + 3
    return _osc(t, mult, add)


@dataclass(frozen=True)
class StepSample:
    step: int
    active_lines: int
    dormant_lines: int
    total_hype: float
    max_hype: float
    fragile_visible: int
    open_question_visible: int
    conflict_count: int
    step_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "active_lines": self.active_lines,
            "dormant_lines": self.dormant_lines,
            "total_hype": self.total_hype,
            "max_hype": self.max_hype,
            "fragile_visible": self.fragile_visible,
            "open_question_visible": self.open_question_visible,
            "conflict_count": self.conflict_count,
            "step_hash": self.step_hash,
        }


@dataclass(frozen=True)
class EcologyRun:
    steps: int
    method_count: int
    topic_count: int
    fragile_total: int
    open_question_total: int
    conflict_count: int
    min_present_lines: int
    min_active_ratio: float
    hype_peak: float
    hype_trough: float
    forgotten_events: int
    rediscovery_events: int
    chain_head: str
    sample: tuple[StepSample, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": self.steps,
            "method_count": self.method_count,
            "topic_count": self.topic_count,
            "fragile_total": self.fragile_total,
            "open_question_total": self.open_question_total,
            "conflict_count": self.conflict_count,
            "min_present_lines": self.min_present_lines,
            "min_active_ratio": self.min_active_ratio,
            "hype_peak": self.hype_peak,
            "hype_trough": self.hype_trough,
            "forgotten_events": self.forgotten_events,
            "rediscovery_events": self.rediscovery_events,
            "chain_head": self.chain_head,
            "sample": [s.to_dict() for s in self.sample],
        }


@lru_cache(maxsize=1)
def run() -> EcologyRun:
    methods = all_methods()
    topics = _topics()
    n_methods = len(methods)
    fragile_total = sum(
        1 for c in all_claims()
        if c.claim_class == K.SPECULATIVE.value
    )
    open_q_total = sum(
        1 for c in all_claims()
        if c.claim_class == K.OPEN_QUESTION.value
    )
    conflict_count = sum(len(p.conflicts) for p in papers())

    chain = "research_ecology_v27_3"
    min_present = n_methods
    hype_peak = 0.0
    hype_trough = 1.0
    forgotten = 0
    rediscovered = 0
    prev_dormant = [False] * n_methods
    sample: list[StepSample] = []

    for t in range(_STEPS):
        present = 0
        active = 0
        dormant = 0
        for i in range(n_methods):
            s = _strength(i, t)
            if s > 0.0:
                present += 1
            is_dormant = s < _DORMANT_BELOW
            if is_dormant:
                dormant += 1
                if not prev_dormant[i]:
                    forgotten += 1
            else:
                active += 1
                if prev_dormant[i]:
                    rediscovered += 1
            prev_dormant[i] = is_dormant

        total_hype = 0.0
        step_max_hype = 0.0
        for j in range(len(topics)):
            h = _hype(j, t)
            total_hype += h
            if h > step_max_hype:
                step_max_hype = h
        total_hype = round(total_hype, 6)
        if step_max_hype > hype_peak:
            hype_peak = step_max_hype
        if step_max_hype < hype_trough:
            hype_trough = step_max_hype
        if present < min_present:
            min_present = present

        summary = (
            f"{t}|{active}|{dormant}|{total_hype}|"
            f"{fragile_total}|{open_q_total}|{conflict_count}"
        )
        chain = hashlib.sha256(
            (chain + "|" + summary).encode("utf-8"),
        ).hexdigest()

        if t % _SAMPLE_EVERY == 0:
            sample.append(StepSample(
                step=t, active_lines=active,
                dormant_lines=dormant, total_hype=total_hype,
                max_hype=round(step_max_hype, 6),
                fragile_visible=fragile_total,
                open_question_visible=open_q_total,
                conflict_count=conflict_count,
                step_hash=chain,
            ))

    return EcologyRun(
        steps=_STEPS,
        method_count=n_methods,
        topic_count=len(topics),
        fragile_total=fragile_total,
        open_question_total=open_q_total,
        conflict_count=conflict_count,
        min_present_lines=min_present,
        min_active_ratio=round(min_present / n_methods, 6),
        hype_peak=round(hype_peak, 6),
        hype_trough=round(hype_trough, 6),
        forgotten_events=forgotten,
        rediscovery_events=rediscovered,
        chain_head=chain,
        sample=tuple(sample),
    )


__all__ = [
    "EcologyRun",
    "StepSample",
    "run",
]
