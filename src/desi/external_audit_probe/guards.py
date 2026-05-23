"""Aufgabe 7 — guard pressure map.

For every false-support case we report which of the 14
``CAUSAL_CHAIN`` guards *would have* fired had their marker
buckets been extended with the surface tokens observed in the
chain. Every actual guard that fires returns ``None`` and the
chain never becomes a false support; so by construction the
true-firing rate is zero on this case set. The interesting
quantity is the *latent* firing rate: how many cases carry at
least one suspension-class surface token (a "shadow guard
hit") that v3.16's closed marker tuples failed to catch.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..logic.inference import (
    _NEGATION_MARKERS, _QUANTIFIER_MARKERS, _CYCLE_CONNECTIVES,
    _V316_NEGATION_EXTENSIONS, _V316_QUANTIFIER_EXTENSIONS,
    _V316_AUTHORITY_LIKE_VERBS, _V316_METAPHOR_MARKERS,
    _V316_CYCLE_REF_EXTENSIONS,
)
from .cases import FalseSupportCase
from .replay import ReplayRecord, _suspension_markers_fired


_V27_BUCKETS: dict[str, tuple[str, ...]] = {
    "v27_negation":   _NEGATION_MARKERS,
    "v27_quantifier": _QUANTIFIER_MARKERS,
    "v27_cycle":      _CYCLE_CONNECTIVES,
}

_V316_BUCKETS: dict[str, tuple[str, ...]] = {
    "v316_negation":   _V316_NEGATION_EXTENSIONS,
    "v316_quantifier": _V316_QUANTIFIER_EXTENSIONS,
    "v316_authority":  _V316_AUTHORITY_LIKE_VERBS,
    "v316_metaphor":   _V316_METAPHOR_MARKERS,
    "v316_cycle":      _V316_CYCLE_REF_EXTENSIONS,
}


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    padded = " " + text.lower() + " "
    return any(m in padded for m in markers)


@dataclass(frozen=True)
class GuardPressure:
    chain_id: str
    actual_guard_hits: tuple[str, ...]
    shadow_guard_hits: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "actual_guard_hits": list(self.actual_guard_hits),
            "shadow_guard_hits": list(self.shadow_guard_hits),
        }


def measure_guard_pressure(
    case: FalseSupportCase, record: ReplayRecord,
) -> GuardPressure:
    actual: list[str] = []
    for name, bucket in {**_V27_BUCKETS, **_V316_BUCKETS}.items():
        if _contains_any(case.text, bucket):
            actual.append(name)
    shadow = list(record.suspension_markers)
    return GuardPressure(
        chain_id=case.chain_id,
        actual_guard_hits=tuple(sorted(set(actual))),
        shadow_guard_hits=tuple(shadow),
    )


@dataclass(frozen=True)
class GuardPressureSummary:
    total: int
    actual_firing_rate: float
    shadow_firing_rate: float
    cases_with_zero_guard_hits: int
    actual_bucket_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "actual_firing_rate": self.actual_firing_rate,
            "shadow_firing_rate": self.shadow_firing_rate,
            "cases_with_zero_guard_hits":
                self.cases_with_zero_guard_hits,
            "actual_bucket_counts":
                dict(self.actual_bucket_counts),
        }


def summarise(
    pressures: tuple[GuardPressure, ...],
) -> GuardPressureSummary:
    n = len(pressures)
    actual_counts: dict[str, int] = {}
    actual_nonzero = 0
    shadow_nonzero = 0
    zero_both = 0
    for p in pressures:
        for b in p.actual_guard_hits:
            actual_counts[b] = actual_counts.get(b, 0) + 1
        if p.actual_guard_hits:
            actual_nonzero += 1
        if p.shadow_guard_hits:
            shadow_nonzero += 1
        if not p.actual_guard_hits and not p.shadow_guard_hits:
            zero_both += 1
    return GuardPressureSummary(
        total=n,
        actual_firing_rate=(
            round(actual_nonzero / n, 6) if n else 0.0
        ),
        shadow_firing_rate=(
            round(shadow_nonzero / n, 6) if n else 0.0
        ),
        cases_with_zero_guard_hits=zero_both,
        actual_bucket_counts={
            k: actual_counts[k] for k in sorted(actual_counts)
        },
    )


__all__ = [
    "GuardPressure", "GuardPressureSummary",
    "measure_guard_pressure", "summarise",
]
