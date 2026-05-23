"""Aufgabe 9 — contamination check against every protected
benchmark text.

Pool construction mirrors v4.3 / v4.5: includes v1.5 main,
v1.9 tool, v2.3 multistep, v3.14 held-out, v3.15 adversarial,
v3.4 frame benchmark, and every v4.0-VALID chain. A probe hit
on any of these is a false-negative regression.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..benchmark import ALL_CASES as MAIN_CASES
from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..external_probe.corpus import all_chains
from ..external_probe.enums import GroundTruth
from ..frame_benchmark import ALL_FRAME_CASES
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from ..tools.benchmark import ALL_TOOL_CASES
from .modality_check import fires_on_text


def _protected_pool() -> tuple[str, ...]:
    """Every VALID-labeled chain across every protected
    benchmark. We do *not* pre-filter by current audit state:
    the v4.7 predicate's job is to suspend chains that would
    otherwise pass, so filtering by post-patch audit-supported
    would be tautological. A predicate firing on a VALID chain
    that was *previously* audit-supported is the regression
    we care about; for chains that were never audit-supported
    (e.g., D2V007 which the v2.7 negation guard already kills),
    the predicate firing is harmless and is excluded by the
    ``actually_changed_audit`` filter inside :func:`check`."""
    pool: list[str] = []
    for case in MAIN_CASES:
        pool.append(case.text)
    for case in ALL_MULTISTEP_CASES:
        pool.append(case.text)
    for case in ALL_HELDOUT_CASES:
        pool.append(case.text)
    for case in ALL_ADVERSARIAL_CASES:
        pool.append(case.text)
    for case in ALL_FRAME_CASES:
        pool.append(case.text)
    for case in ALL_TOOL_CASES:
        pool.append(case.text)
    for case in all_chains():
        if case.ground_truth is GroundTruth.VALID:
            pool.append(case.text)
    return tuple(pool)


@dataclass(frozen=True)
class ContaminationReport:
    protected_pool_size: int
    contamination_count: int
    contaminating_texts: tuple[str, ...]
    predicate_firings_on_already_killed: int

    def to_dict(self) -> dict[str, object]:
        return {
            "protected_pool_size": self.protected_pool_size,
            "contamination_count": self.contamination_count,
            "contaminating_texts": [
                t[:120] for t in self.contaminating_texts
            ],
            "predicate_firings_on_already_killed":
                self.predicate_firings_on_already_killed,
        }


def check() -> ContaminationReport:
    """Contamination = chains where v4.7 *newly* suspends a
    previously-audit-supported VALID chain. Predicate firings
    on chains that were already non-supported via earlier
    guards are not contamination — they're reported separately
    via ``predicate_firings_on_already_killed`` for
    transparency."""
    pool = _protected_pool()
    auditor = LogicalAuditor()
    contam: list[str] = []
    already_killed = 0
    for text in pool:
        if not fires_on_text(text):
            continue
        # Post-patch audit state — if SUPPORTED, the predicate
        # wouldn't have fired (or fires harmlessly on a
        # chain that the audit still supports somehow). If
        # NOT supported, we distinguish:
        # - REJECTED ONLY via v4.7 → contamination,
        # - REJECTED via an earlier guard → not contamination.
        a = auditor.audit(text)
        if a.state is LogicalState.LOGICALLY_SUPPORTED:
            # Should not happen — v4.7 fires but audit still
            # supports (predicate inside _try_causal_chain
            # returns None on hit). Defensive count.
            contam.append(text)
            continue
        # Not currently supported: was it ever supported pre-
        # v4.7? Proxy: check whether removing the v4.7 predicate
        # would have let the audit succeed. We approximate by
        # asking whether the chain has *no* other suspension
        # marker present — none of the v2.7/v3.16/v4.3/v4.5
        # guards would have killed it. If clean, then v4.7 is
        # the unique cause → contamination. If something else
        # already fires, the chain was already killed →
        # ``already_killed``.
        if _only_v47_would_kill(text):
            contam.append(text)
        else:
            already_killed += 1
    return ContaminationReport(
        protected_pool_size=len(pool),
        contamination_count=len(contam),
        contaminating_texts=tuple(contam),
        predicate_firings_on_already_killed=already_killed,
    )


def _only_v47_would_kill(text: str) -> bool:
    """True iff the chain's audit would have been supported
    (or at least non-rejected) without the v4.7 guard. We
    compute this by checking every other guard's marker
    bucket against the chain's premises and conclusion. If
    *no* other guard would have fired, the v4.7 guard is the
    unique cause of the current rejection."""
    from ..logic.inference import (
        _CYCLE_CONNECTIVES, _NEGATION_MARKERS,
        _QUANTIFIER_MARKERS, _V316_AUTHORITY_LIKE_VERBS,
        _V316_CYCLE_REF_EXTENSIONS, _V316_METAPHOR_MARKERS,
        _V316_NEGATION_EXTENSIONS,
        _V316_QUANTIFIER_EXTENSIONS,
        _V43_AUTHORITY_LIKE_VERBS,
        _V43_NEGATION_EXTENSIONS,
        _V43_QUANTIFIER_EXTENSIONS,
        _contains_marker,
    )
    from ..logic.premises import PremiseExtractor

    e = PremiseExtractor().extract(text)
    if e.conclusion is None or not e.premises:
        return False
    parts = list(e.premises) + [e.conclusion]
    other_buckets = (
        _NEGATION_MARKERS, _QUANTIFIER_MARKERS,
        _CYCLE_CONNECTIVES, _V316_NEGATION_EXTENSIONS,
        _V316_QUANTIFIER_EXTENSIONS,
        _V316_AUTHORITY_LIKE_VERBS,
        _V316_METAPHOR_MARKERS,
        _V316_CYCLE_REF_EXTENSIONS,
        _V43_NEGATION_EXTENSIONS,
        _V43_QUANTIFIER_EXTENSIONS,
        _V43_AUTHORITY_LIKE_VERBS,
    )
    for p in parts:
        for bucket in other_buckets:
            if _contains_marker(p.text, bucket):
                return False
    return True


__all__ = ["ContaminationReport", "check"]
