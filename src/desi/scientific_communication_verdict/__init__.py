"""DESi v22.4 - Scientific Communication Verdict (read-only).

Aggregates v22.0-v22.3 into six directive metrics, a closed
A-E taxonomy, and a six-condition concept gate. Answers the
Killerfrage: can DESi produce follow-up scientific
communication without becoming a hype machine? DESi makes no
global intelligence claim and claims no truth authority.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, AggregateMetrics,
    GateCondition, aggregate, claim_conservatism, class_rank,
    classify_corpus, epistemic_humility, exploratory,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    hype_resistance, paper_compatibility, technical_grounding,
)
from .report import (
    PHASE_VERDICTS, VERDICT_GROUNDED, VERDICT_HALT,
    VERDICT_INFLATED, V224Report, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    SCIENTIFIC_COMM_CLASSES, ScientificCommClass,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "PHASE_VERDICTS",
    "SCIENTIFIC_COMM_CLASSES",
    "VERDICT_GROUNDED",
    "VERDICT_HALT",
    "VERDICT_INFLATED",
    "AggregateMetrics",
    "GateCondition",
    "ScientificCommClass",
    "V224Report",
    "aggregate",
    "build_report",
    "build_verdict_artifact",
    "claim_conservatism",
    "class_rank",
    "classify_corpus",
    "epistemic_humility",
    "exploratory",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "hype_resistance",
    "paper_compatibility",
    "technical_grounding",
]
