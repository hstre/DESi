"""DESi v38.4 - Live LLM Validation Verdict (read-only).

Final verdict on real OpenRouter-based live-LLM validation. Aggregates
one score per dimension from the v38.0-v38.3 runs over REAL captured
Granite and DeepSeek outputs, checks a six-condition Concept Gate and
classifies on a closed A-E taxonomy. LLM outputs are observed
stochastic evidence graded by DESi, never canonical truth.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, GateCondition,
    LiveMetrics, aggregate, classify_corpus, deepseek_score,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    governance_identity, granite_score, hallucination_containment,
    replay_stability, routing_score,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PASSED,
    VERDICT_UNVALIDATED, V384Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    LIVE_CLASSES, LiveClass, class_meaning, class_rank, is_acceptable,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "LIVE_CLASSES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PASSED",
    "VERDICT_UNVALIDATED",
    "GateCondition",
    "LiveClass",
    "LiveMetrics",
    "V384Report",
    "aggregate",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "deepseek_score",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "granite_score",
    "hallucination_containment",
    "is_acceptable",
    "replay_stability",
    "routing_score",
]
