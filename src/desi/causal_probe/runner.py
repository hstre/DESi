"""CausalChainProbeRunner — Aufgabe 3 + 5.

Walks the 50 v1.5 cases and the 30 v2.3 multi-step cases, applies
the hypothetical trigger from :mod:`causal_probe.pattern`, and
annotates each triggered candidate with the subset of
:class:`RiskFlag` values that applies.

Strictly read-only: no production module is modified. The real
:class:`LogicalAuditor` provides premise data; the real
:class:`RecursiveResolver` provides the case's *current* final
state. Neither is rebound or patched.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..benchmark import ALL_CASES as MAIN_CASES, Category as MainCategory
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..benchmark_multistep.case import MultiStepCategory
from ..logic import LogicalAuditor
from ..recursive import RecursiveResolver
from .pattern import (
    BenchmarkSource,
    CausalChainCandidate,
    candidate_replay_hash,
    count_atomic_sequence,
    count_repeated_content,
    hypothetical_trigger,
)
from .risk import KNOWN_FALSE_POSITIVE_CASE_IDS, RiskFlag


def _count_therefore(text: str) -> int:
    lo = text.lower()
    n = 0
    start = 0
    while True:
        i = lo.find("therefore", start)
        if i < 0:
            break
        n += 1
        start = i + len("therefore")
    return n


# Mapping from category to the risk flag the probe attaches when
# the hypothetical trigger fires on a case in that category.
_MAIN_RISK_BY_CATEGORY: dict[MainCategory, RiskFlag] = {
    MainCategory.A_EVERYDAY_CAUSALITY: (
        RiskFlag.WOULD_TOUCH_EVERYDAY_CAUSAL_CASE
    ),
    MainCategory.C_AUTHORITY_TRAPS: RiskFlag.WOULD_TOUCH_AUTHORITY_CASE,
    MainCategory.D_METAPHOR_AMBIGUITY: RiskFlag.WOULD_TOUCH_METAPHOR_CASE,
    MainCategory.E_PHILOSOPHICAL_STRESS: (
        RiskFlag.WOULD_TOUCH_PHILOSOPHY_CASE
    ),
}


_MULTISTEP_RISK_BY_CATEGORY: dict[MultiStepCategory, RiskFlag] = {
    MultiStepCategory.R1_TWO_STEP: (
        RiskFlag.WOULD_TOUCH_VALID_MULTISTEP_CASE
    ),
    MultiStepCategory.R2_THREE_STEP: (
        RiskFlag.WOULD_TOUCH_VALID_MULTISTEP_CASE
    ),
    MultiStepCategory.R3_FOUR_STEP: (
        RiskFlag.WOULD_TOUCH_VALID_MULTISTEP_CASE
    ),
    MultiStepCategory.R4_HIDDEN_CONTRADICTION: (
        RiskFlag.WOULD_TOUCH_CONTRADICTION_CASE
    ),
    MultiStepCategory.R5_CYCLIC_DEPENDENCY: (
        RiskFlag.WOULD_TOUCH_CYCLE_CASE
    ),
}


@dataclass(frozen=True)
class CausalProbeRun:
    timestamp: datetime
    candidates: tuple[CausalChainCandidate, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "candidates": [c.to_dict() for c in self.candidates],
        }


class CausalChainProbeRunner:
    """Walks the union of v1.5 + v2.3 cases, one candidate per case."""

    def run(self) -> CausalProbeRun:
        candidates: list[CausalChainCandidate] = []
        for case in MAIN_CASES:
            candidates.append(self._probe_main(case))
        for case in ALL_MULTISTEP_CASES:
            candidates.append(self._probe_multistep(case))
        # Deterministic ordering by source-prefix + case_id.
        candidates.sort(
            key=lambda c: (c.benchmark_source.value, c.case_id),
        )
        return CausalProbeRun(
            timestamp=datetime.now(timezone.utc),
            candidates=tuple(candidates),
        )

    # ------------------------------------------------------------------
    # Per-case probes
    # ------------------------------------------------------------------

    def _probe_main(self, case: Any) -> CausalChainCandidate:
        auditor = LogicalAuditor()
        audit = auditor.audit(case.text)
        kinds = tuple(p.kind.value for p in audit.propositions.premises)
        premise_count = len(audit.propositions.premises)
        therefore_count = _count_therefore(case.text)
        atomic_seq = count_atomic_sequence(kinds)
        subj, pred = count_repeated_content(case.text)
        triggered, reason = hypothetical_trigger(
            premise_count=premise_count,
            therefore_count=therefore_count,
            atomic_sequence=atomic_seq,
        )
        # Current final state via a real resolver call — purely
        # observational, no side effects on the case set.
        resolver = RecursiveResolver()
        res = resolver.resolve(case.text)
        flags = _assign_main_risk_flags(case, triggered)
        return _finalize_candidate(
            case_id=case.case_id,
            source=BenchmarkSource.MAIN_50,
            text=case.text,
            premise_count=premise_count,
            therefore_count=therefore_count,
            atomic_seq=atomic_seq,
            subj=subj, pred=pred,
            triggered=triggered, reason=reason,
            flags=flags,
            expected_label=case.ground_truth.value,
            current_state=res.final_state,
        )

    def _probe_multistep(self, case: Any) -> CausalChainCandidate:
        auditor = LogicalAuditor()
        audit = auditor.audit(case.text)
        kinds = tuple(p.kind.value for p in audit.propositions.premises)
        premise_count = len(audit.propositions.premises)
        therefore_count = _count_therefore(case.text)
        atomic_seq = count_atomic_sequence(kinds)
        subj, pred = count_repeated_content(case.text)
        triggered, reason = hypothetical_trigger(
            premise_count=premise_count,
            therefore_count=therefore_count,
            atomic_sequence=atomic_seq,
        )
        resolver = RecursiveResolver()
        res = resolver.resolve(case.text)
        flags = _assign_multistep_risk_flags(case, triggered)
        return _finalize_candidate(
            case_id=case.case_id,
            source=BenchmarkSource.MULTISTEP_30,
            text=case.text,
            premise_count=premise_count,
            therefore_count=therefore_count,
            atomic_seq=atomic_seq,
            subj=subj, pred=pred,
            triggered=triggered, reason=reason,
            flags=flags,
            expected_label=case.expected_final_state.value,
            current_state=res.final_state,
        )


def _assign_main_risk_flags(case: Any, triggered: bool) -> tuple[RiskFlag, ...]:
    if not triggered:
        return ()
    flags: list[RiskFlag] = []
    cat_flag = _MAIN_RISK_BY_CATEGORY.get(case.category)
    if cat_flag is not None:
        flags.append(cat_flag)
    if case.case_id in KNOWN_FALSE_POSITIVE_CASE_IDS:
        flags.append(RiskFlag.WOULD_REOPEN_KNOWN_FALSE_POSITIVE)
    if not flags:
        flags.append(RiskFlag.NO_RISK_FLAG)
    # Deterministic order: enum declaration order.
    enum_order = {f: i for i, f in enumerate(RiskFlag)}
    return tuple(sorted(set(flags), key=lambda f: enum_order[f]))


def _assign_multistep_risk_flags(
    case: Any, triggered: bool,
) -> tuple[RiskFlag, ...]:
    if not triggered:
        return ()
    flag = _MULTISTEP_RISK_BY_CATEGORY.get(case.category)
    if flag is None:
        return (RiskFlag.NO_RISK_FLAG,)
    return (flag,)


def _finalize_candidate(
    *,
    case_id: str,
    source: BenchmarkSource,
    text: str,
    premise_count: int,
    therefore_count: int,
    atomic_seq: int,
    subj: int,
    pred: int,
    triggered: bool,
    reason: str,
    flags: tuple[RiskFlag, ...],
    expected_label: str,
    current_state: Any,
) -> CausalChainCandidate:
    payload = {
        "case_id": case_id,
        "benchmark_source": source.value,
        "text": text,
        "premise_count": premise_count,
        "therefore_count": therefore_count,
        "atomic_sequence": atomic_seq,
        "repeated_subjects": subj,
        "repeated_predicates": pred,
        "candidate_triggered": triggered,
        "trigger_reason": reason,
        "risk_flags": [f.value for f in flags],
        "expected_label": expected_label,
        "current_final_state": current_state.value,
    }
    replay = candidate_replay_hash(payload)
    return CausalChainCandidate(
        case_id=case_id,
        benchmark_source=source,
        text=text,
        premise_count=premise_count,
        therefore_count=therefore_count,
        atomic_sequence=atomic_seq,
        repeated_subjects=subj,
        repeated_predicates=pred,
        candidate_triggered=triggered,
        trigger_reason=reason,
        risk_flags=flags,
        expected_label=expected_label,
        current_final_state=current_state,
        replay_hash=replay,
    )


__all__ = ["CausalChainProbeRunner", "CausalProbeRun"]
