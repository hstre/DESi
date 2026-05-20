"""DESi v20.4 - Dual-Agent Governance Verdict (read-only).

Aggregates v20.0-v20.3 into five directive metrics, a closed
A-E taxonomy, and a six-condition concept gate. Answers the
Killerfrage: can an epistemically governed wild brother be
more productive than conservative governance alone? DESi
governs the wild without replacing the policy or taking
hidden authority.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, AggregateMetrics,
    GateCondition, aggregate, authority_resistance, class_rank,
    classify_corpus, conflict_rich, exploration_diversity,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    hallucination_containment, novelty_preservation,
    productive_conflict, productivity_gain, wild_not_eliminated,
)
from .report import (
    PHASE_VERDICTS, VERDICT_GOVERNED, VERDICT_HALT,
    VERDICT_UNGOVERNED, V204Report, build_report,
    build_verdict_artifact,
)
from .taxonomy import DUAL_AGENT_CLASSES, DualAgentClass


__all__ = [
    "DUAL_AGENT_CLASSES",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "PHASE_VERDICTS",
    "VERDICT_GOVERNED",
    "VERDICT_HALT",
    "VERDICT_UNGOVERNED",
    "AggregateMetrics",
    "DualAgentClass",
    "GateCondition",
    "V204Report",
    "aggregate",
    "authority_resistance",
    "build_report",
    "build_verdict_artifact",
    "class_rank",
    "classify_corpus",
    "conflict_rich",
    "exploration_diversity",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "hallucination_containment",
    "novelty_preservation",
    "productive_conflict",
    "productivity_gain",
    "wild_not_eliminated",
]
