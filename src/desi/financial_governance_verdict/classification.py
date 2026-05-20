"""v15.4 - aggregate metrics, concept gate, and
corpus governance verdict.

Rolls up the v15.0-v15.3 sprint results into the
five directive metrics and the six-condition
concept gate. The corpus verdict is the most
concentrated firm class present (priority-ordered).

The post-hoc label is consulted ONLY to validate
(recalls, false-accusation accounting); the per-
firm classification itself is post-hoc-free.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.financial_governance import (
    ADVERSE_POST_HOC, PostHocLabel,
)
from desi.financial_governance import (
    build_report as _v0_report,
    clean_firm_low_priority_rate,
    ex_ante_structure_recall,
)
from desi.financial_narrative_drift import (
    build_report as _v1_report,
    clean_firm_low_drift_rate,
    ex_ante_drift_recall,
)
from desi.financial_blindness import (
    build_report as _v2_report,
    clean_firm_sound_rate, ex_ante_pool_recall,
    firm_pool_verdicts, recoverability_signal,
)
from desi.financial_audit_compression import (
    audit_search_reduction,
    build_report as _v3_report,
    critical_signal_preservation,
    ex_ante_critical_preservation,
    false_suppression_rate,
)

from .taxonomy import (
    GovernanceClass, class_rank, classify_firm,
    firm_classes,
)

# Concept-gate floors / ceilings (directive § v15.4).
GATE_CRITICAL_PRESERVATION = 0.95
GATE_FALSE_ACCUSATION = 0.05
GATE_SEARCH_REDUCTION = 0.30
GATE_GOVERNANCE_INTEGRITY = 0.90
GATE_EPISTEMIC_TRANSPARENCY = 0.90

GATE_PASS_STATEMENT = (
    "DESi kann finanzielle Auditraeume epistemisch "
    "strukturieren."
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _non_adverse_ids() -> list[str]:
    return [
        v.firm_id for v in firm_pool_verdicts()
        if v.post_hoc_label not in ADVERSE_POST_HOC
    ]


def false_accusation_rate() -> float:
    """POST-HOC VALIDATION. Fraction of firms with
    no later adverse outcome that DESi nonetheless
    escalated to an accusation-level class (D or
    E). MEDIUM ('audit_sensitive') is a request for
    a closer look, not an accusation, so it does
    NOT count."""
    non_adverse = _non_adverse_ids()
    if not non_adverse:
        return 0.0
    accused = {
        GovernanceClass.D_OPACITY_HEAVY.value,
        GovernanceClass
        .E_GOVERNANCE_RISK_CONCENTRATED.value,
    }
    n = sum(
        1 for fid in non_adverse
        if classify_firm(fid) in accused
    )
    return _round(n / len(non_adverse))


def _clean_specificity() -> float:
    return _mean([
        clean_firm_low_priority_rate(),
        clean_firm_low_drift_rate(),
        clean_firm_sound_rate(),
    ])


def audit_priority_quality() -> float:
    """Mean ex-ante detection quality across the
    four sprints (recall of the later-adverse
    firms / preservation of their critical
    signals)."""
    return _round(_mean([
        ex_ante_structure_recall(),
        ex_ante_drift_recall(),
        ex_ante_pool_recall(),
        ex_ante_critical_preservation(),
    ]))


def _sub_replays() -> list[float]:
    return [
        _v0_report().replay_stability,
        _v1_report().replay_stability,
        _v2_report().replay_stability,
        _v3_report().replay_stability,
    ]


def governance_integrity() -> float:
    """Process integrity: clean firms not accused,
    no critical signal suppressed, clean-firm
    specificity held, and full replay."""
    return _round(_mean([
        1.0 - false_accusation_rate(),
        1.0 - false_suppression_rate(),
        _clean_specificity(),
        min(_sub_replays()),
    ]))


def epistemic_transparency() -> float:
    """How inspectable the structuring is: fully
    reproducible, pools recoverable, no hidden
    signal suppression, prioritisation traceable."""
    return _round(_mean([
        min(_sub_replays()),
        recoverability_signal(),
        critical_signal_preservation(),
        audit_priority_quality(),
    ]))


@dataclass(frozen=True)
class AggregateMetrics:
    audit_priority_quality: float
    false_accusation_rate: float
    governance_integrity: float
    epistemic_transparency: float
    critical_signal_preservation: float
    audit_search_reduction: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "audit_priority_quality":
                self.audit_priority_quality,
            "false_accusation_rate":
                self.false_accusation_rate,
            "governance_integrity":
                self.governance_integrity,
            "epistemic_transparency":
                self.epistemic_transparency,
            "critical_signal_preservation":
                self.critical_signal_preservation,
            "audit_search_reduction":
                self.audit_search_reduction,
            "replay_stability":
                self.replay_stability,
        }


def _meta_replay() -> float:
    if min(_sub_replays()) < 1.0:
        return 0.0
    a = _aggregate_tuple()
    b = _aggregate_tuple()
    return 1.0 if a == b else 0.0


def _aggregate_tuple() -> tuple[float, ...]:
    return (
        audit_priority_quality(),
        false_accusation_rate(),
        critical_signal_preservation(),
        audit_search_reduction(),
        false_suppression_rate(),
        recoverability_signal(),
        _clean_specificity(),
    )


def aggregate() -> AggregateMetrics:
    return AggregateMetrics(
        audit_priority_quality=(
            audit_priority_quality()
        ),
        false_accusation_rate=(
            false_accusation_rate()
        ),
        governance_integrity=governance_integrity(),
        epistemic_transparency=(
            epistemic_transparency()
        ),
        critical_signal_preservation=(
            critical_signal_preservation()
        ),
        audit_search_reduction=(
            audit_search_reduction()
        ),
        replay_stability=_meta_replay(),
    )


@dataclass(frozen=True)
class GateCondition:
    name: str
    value: float
    threshold: float
    comparator: str
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "comparator": self.comparator,
            "passed": self.passed,
        }


def gate_conditions() -> tuple[GateCondition, ...]:
    m = aggregate()
    raw = [
        (
            "critical_signal_preservation",
            m.critical_signal_preservation,
            GATE_CRITICAL_PRESERVATION, ">=",
            m.critical_signal_preservation
            >= GATE_CRITICAL_PRESERVATION,
        ),
        (
            "false_accusation_rate",
            m.false_accusation_rate,
            GATE_FALSE_ACCUSATION, "<=",
            m.false_accusation_rate
            <= GATE_FALSE_ACCUSATION,
        ),
        (
            "audit_search_reduction",
            m.audit_search_reduction,
            GATE_SEARCH_REDUCTION, ">=",
            m.audit_search_reduction
            >= GATE_SEARCH_REDUCTION,
        ),
        (
            "governance_integrity",
            m.governance_integrity,
            GATE_GOVERNANCE_INTEGRITY, ">=",
            m.governance_integrity
            >= GATE_GOVERNANCE_INTEGRITY,
        ),
        (
            "epistemic_transparency",
            m.epistemic_transparency,
            GATE_EPISTEMIC_TRANSPARENCY, ">=",
            m.epistemic_transparency
            >= GATE_EPISTEMIC_TRANSPARENCY,
        ),
        (
            "replay_stability",
            m.replay_stability, 1.0, "==",
            m.replay_stability == 1.0,
        ),
    ]
    return tuple(
        GateCondition(
            name=n, value=_round(v),
            threshold=t, comparator=c, passed=p,
        )
        for (n, v, t, c, p) in raw
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        c.name for c in gate_conditions()
        if not c.passed
    )


def corpus_class() -> str:
    """The most concentrated firm class present."""
    classes = list(firm_classes().values())
    if not classes:
        return (
            GovernanceClass
            .A_EPISTEMICALLY_TRANSPARENT.value
        )
    return max(classes, key=class_rank)


def class_histogram() -> dict[str, int]:
    hist = {c: 0 for c in (
        GovernanceClass.A_EPISTEMICALLY_TRANSPARENT.value,
        GovernanceClass.B_STRUCTURALLY_STABLE.value,
        GovernanceClass.C_AUDIT_SENSITIVE.value,
        GovernanceClass.D_OPACITY_HEAVY.value,
        GovernanceClass.E_GOVERNANCE_RISK_CONCENTRATED.value,
    )}
    for c in firm_classes().values():
        hist[c] += 1
    return hist


__all__ = [
    "GATE_PASS_STATEMENT",
    "AggregateMetrics",
    "GateCondition",
    "aggregate",
    "audit_priority_quality",
    "class_histogram",
    "corpus_class",
    "epistemic_transparency",
    "false_accusation_rate",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_integrity",
]
