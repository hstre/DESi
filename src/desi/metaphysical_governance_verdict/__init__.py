"""DESi v18.4 - Metaphysical Governance Verdict
(read-only, abstract).

Aggregates v18.0-v18.3 into five directive metrics, a
closed A-E taxonomy, and a six-condition concept gate.
Answers the Killerfrage: can an epistemic system survive
metaphysical authority pressure without becoming
dogmatic? DESi claims no metaphysical authority and ranks
no tradition.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT,
    AggregateMetrics, GateCondition, aggregate,
    authority_resistance, capture_resistance, class_rank,
    classify_corpus, conflict_rich, dissent_preservation,
    epistemic_plurality, false_certainty_rate,
    gate_conditions, gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    PHASE_VERDICTS, VERDICT_HALT, VERDICT_SURVIVED,
    VERDICT_UNSTABLE, V184Report, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    METAPHYSICAL_GOVERNANCE_CLASSES,
    MetaphysicalGovernanceClass,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "METAPHYSICAL_GOVERNANCE_CLASSES",
    "PHASE_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_SURVIVED",
    "VERDICT_UNSTABLE",
    "AggregateMetrics",
    "GateCondition",
    "MetaphysicalGovernanceClass",
    "V184Report",
    "aggregate",
    "authority_resistance",
    "build_report",
    "build_verdict_artifact",
    "capture_resistance",
    "class_rank",
    "classify_corpus",
    "conflict_rich",
    "dissent_preservation",
    "epistemic_plurality",
    "false_certainty_rate",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
]
