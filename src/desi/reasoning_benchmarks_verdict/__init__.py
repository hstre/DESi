"""DESi v36.4 - Reasoning Benchmark Verdict (read-only).

Final verdict on the reasoning benchmark runs. Aggregates one score
per family from the v36.0-v36.3 runs (instruction, scientific
grounding, logic, multi-hop), checks a six-condition Concept Gate and
classifies on a closed A-E taxonomy. Tests DESi's deterministic
epistemic governance on the formats, not LLM task accuracy.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, GateCondition,
    ReasoningMetrics, aggregate, classify_corpus, gate_conditions,
    gate_failing_conditions, gate_passes_all, governance_identity,
    instruction_score, logic_score, multihop_score, replay_stability,
    scientific_grounding_score,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PASSED,
    VERDICT_UNVALIDATED, V364Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    REASONING_CLASSES, ReasoningClass, class_meaning, class_rank,
    is_acceptable,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "REASONING_CLASSES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PASSED",
    "VERDICT_UNVALIDATED",
    "GateCondition",
    "ReasoningClass",
    "ReasoningMetrics",
    "V364Report",
    "aggregate",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "instruction_score",
    "is_acceptable",
    "logic_score",
    "multihop_score",
    "replay_stability",
    "scientific_grounding_score",
]
