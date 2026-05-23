"""DESi v19.4 - Exploration Governance Verdict (read-only).

Aggregates v19.0-v19.3 into five directive metrics, a
closed A-E taxonomy, and a six-condition concept gate.
Answers the Killerfrage: can DESi structure exploration
without becoming a hidden optimisation instance? DESi
replaces no policy, manipulates no reward, and claims no
optimal strategy.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT,
    AggregateMetrics, GateCondition, aggregate,
    capture_resistance, class_rank, classify_corpus,
    conflict_rich, exploration_preservation, gate_conditions,
    gate_failing_conditions, gate_passes_all,
    hidden_authority_drift, novelty_visibility,
    redundancy_reduction,
)
from .report import (
    PHASE_VERDICTS, VERDICT_HALT, VERDICT_STRUCTURED,
    VERDICT_UNSTABLE, V194Report, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    EXPLORATION_GOVERNANCE_CLASSES, ExplorationGovernanceClass,
)


__all__ = [
    "EXPLORATION_GOVERNANCE_CLASSES",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "PHASE_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNSTABLE",
    "AggregateMetrics",
    "ExplorationGovernanceClass",
    "GateCondition",
    "V194Report",
    "aggregate",
    "build_report",
    "build_verdict_artifact",
    "capture_resistance",
    "class_rank",
    "classify_corpus",
    "conflict_rich",
    "exploration_preservation",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "hidden_authority_drift",
    "novelty_visibility",
    "redundancy_reduction",
]
