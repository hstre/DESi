"""DESi v28.4 - Self-Improvement Verdict (read-only).

Aggregates one signal per dimension from the v28.0-v28.3 layers,
checks the six-condition Concept Gate (replay integrity,
governance preservation, unsafe containment, branch isolation,
human-approval enforcement, replay stability), and classifies the
controlled self-improvement sandbox on a closed A-E taxonomy. The
goal is branch-isolated, replay-validated, human-gated
self-improvement evaluation - never autonomous self-modification.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, GateCondition,
    SelfImprovementMetrics, aggregate, authority_resistance,
    branch_isolation, classify_corpus, gate_conditions,
    gate_failing_conditions, gate_passes_all,
    governance_preservation, human_approval_enforcement,
    replay_integrity, replay_stability, unsafe_containment,
)
from .report import (
    REPORT_VERDICTS, VERDICT_GOVERNED, VERDICT_HALT,
    VERDICT_UNSTABLE, V284Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    SELF_IMPROVEMENT_CLASSES, SelfImprovementClass,
    class_meaning, class_rank, is_acceptable,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "REPORT_VERDICTS",
    "SELF_IMPROVEMENT_CLASSES",
    "VERDICT_GOVERNED",
    "VERDICT_HALT",
    "VERDICT_UNSTABLE",
    "GateCondition",
    "SelfImprovementClass",
    "SelfImprovementMetrics",
    "V284Report",
    "aggregate",
    "authority_resistance",
    "branch_isolation",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_preservation",
    "human_approval_enforcement",
    "is_acceptable",
    "replay_integrity",
    "replay_stability",
    "unsafe_containment",
]
