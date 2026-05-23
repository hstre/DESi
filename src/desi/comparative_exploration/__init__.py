"""DESi v21.0 - Comparative Exploration Governance
(read-only).

Compares DESi-alone ICRL governance (v19) with DESi + Wild
Explorer dual-agent governance (v20) and computes the deltas
and a paper-readiness score. Answers whether controlled wild
exploration delivers real epistemic value without breaking
safety - the empirical paper thesis.
"""
from __future__ import annotations

from .comparison import (
    comparison_table, delta_authority_drift,
    delta_exploration_diversity, delta_hallucination_pressure,
    delta_novelty_gain, delta_redundancy_reduction,
    delta_replay_stability, desi_alone, dual_agent,
    dual_agent_gate_passed, productivity_gain,
)
from .paper_readiness import (
    paper_readiness_score, readiness_checklist,
)
from .report import (
    REPORT_VERDICTS, THESIS, VERDICT_DUAL_BETTER, VERDICT_HALT,
    VERDICT_NO_GAIN, GateCondition, V210Report,
    build_comparison_artifact, build_report, gate_conditions,
    gate_failing_conditions, gate_passes_all,
)


__all__ = [
    "REPORT_VERDICTS",
    "THESIS",
    "VERDICT_DUAL_BETTER",
    "VERDICT_HALT",
    "VERDICT_NO_GAIN",
    "GateCondition",
    "V210Report",
    "build_comparison_artifact",
    "build_report",
    "comparison_table",
    "delta_authority_drift",
    "delta_exploration_diversity",
    "delta_hallucination_pressure",
    "delta_novelty_gain",
    "delta_redundancy_reduction",
    "delta_replay_stability",
    "desi_alone",
    "dual_agent",
    "dual_agent_gate_passed",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "paper_readiness_score",
    "productivity_gain",
    "readiness_checklist",
]
