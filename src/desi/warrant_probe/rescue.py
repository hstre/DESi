"""Aufgaben 7 + 8 — rescue analysis + cross-probe agreement."""
from __future__ import annotations

from dataclasses import dataclass

from .cases import ResidueCase
from .classifier import Classification
from .enums import WarrantProbe
from .warrant_probes import (
    ProbeCaseOutcome, _PREDICATES, _protected_valid_texts,
    evaluate_all,
)


@dataclass(frozen=True)
class ProbeRescueSummary:
    probe: str
    rescued_cases: int
    rescue_rate: float
    false_blocks: int
    contamination_risk: int
    unsafe: bool
    rescued_chain_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe": self.probe,
            "rescued_cases": self.rescued_cases,
            "rescue_rate": self.rescue_rate,
            "false_blocks": self.false_blocks,
            "contamination_risk": self.contamination_risk,
            "unsafe": self.unsafe,
            "rescued_chain_ids": list(self.rescued_chain_ids),
        }


@dataclass(frozen=True)
class AgreementSummary:
    safe_probes: tuple[str, ...]
    cases_blocked_by_all_safe: int
    warrant_probe_agreement: float
    majority_rescue_clusters: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "safe_probes": list(self.safe_probes),
            "cases_blocked_by_all_safe":
                self.cases_blocked_by_all_safe,
            "warrant_probe_agreement":
                self.warrant_probe_agreement,
            "majority_rescue_clusters":
                list(self.majority_rescue_clusters),
        }


def _per_probe(
    cases: tuple[ResidueCase, ...],
    outcomes: tuple[ProbeCaseOutcome, ...],
) -> tuple[ProbeRescueSummary, ...]:
    protected = _protected_valid_texts()
    by_probe: dict[str, list[ProbeCaseOutcome]] = {}
    for o in outcomes:
        by_probe.setdefault(o.probe, []).append(o)
    out: list[ProbeRescueSummary] = []
    for probe in WarrantProbe:
        bucket = by_probe.get(probe.value, [])
        rescued = sum(1 for o in bucket if o.would_block)
        rate = (
            round(rescued / len(bucket), 6) if bucket else 0.0
        )
        predicate = _PREDICATES[probe]
        false_blocks = sum(
            1 for t in protected if predicate(t)
        )
        out.append(ProbeRescueSummary(
            probe=probe.value,
            rescued_cases=rescued,
            rescue_rate=rate,
            false_blocks=false_blocks,
            contamination_risk=false_blocks,
            unsafe=(false_blocks > 0),
            rescued_chain_ids=tuple(
                o.chain_id for o in bucket if o.would_block
            ),
        ))
    return tuple(out)


def _agreement(
    cases: tuple[ResidueCase, ...],
    outcomes: tuple[ProbeCaseOutcome, ...],
    summaries: tuple[ProbeRescueSummary, ...],
    classifications: tuple[Classification, ...],
) -> AgreementSummary:
    safe = tuple(s.probe for s in summaries if not s.unsafe)
    by_probe: dict[str, dict[str, bool]] = {}
    for o in outcomes:
        by_probe.setdefault(o.probe, {})[
            o.chain_id
        ] = o.would_block
    blocked_by_all_safe = 0
    rescued_by_any_safe: set[str] = set()
    for case in cases:
        if not safe:
            break
        if all(
            by_probe.get(p, {}).get(case.chain_id, False)
            for p in safe
        ):
            blocked_by_all_safe += 1
        if any(
            by_probe.get(p, {}).get(case.chain_id, False)
            for p in safe
        ):
            rescued_by_any_safe.add(case.chain_id)
    agreement = (
        round(blocked_by_all_safe / len(cases), 6)
        if cases else 0.0
    )
    by_class: dict[str, list[str]] = {}
    for case, cls in zip(cases, classifications):
        by_class.setdefault(
            cls.failure_class, [],
        ).append(case.chain_id)
    majority: list[str] = []
    for cluster, ids in by_class.items():
        rescued = sum(
            1 for i in ids if i in rescued_by_any_safe
        )
        if rescued * 2 >= len(ids) and ids:
            majority.append(cluster)
    return AgreementSummary(
        safe_probes=safe,
        cases_blocked_by_all_safe=blocked_by_all_safe,
        warrant_probe_agreement=agreement,
        majority_rescue_clusters=tuple(sorted(majority)),
    )


def analyse(
    cases: tuple[ResidueCase, ...],
    classifications: tuple[Classification, ...],
) -> tuple[
    tuple[ProbeRescueSummary, ...], AgreementSummary,
]:
    outcomes = evaluate_all(cases)
    per_probe = _per_probe(cases, outcomes)
    agreement = _agreement(
        cases, outcomes, per_probe, classifications,
    )
    return per_probe, agreement


__all__ = [
    "AgreementSummary", "ProbeRescueSummary", "analyse",
]
