"""DESi v35.1 - Real Drift Benchmark Runs (read-only).

Runs the connector-loaded BeliefShift, MemEvoBench and AgentDrift
datasets through the v33 drift adapter. Claims update visibly and
lineage-tracked; poisoning is rejected; objective drift is resisted;
authority escalation is refused. The protected core never drifts.
"""
from __future__ import annotations

from .agentdrift_runner import (
    agentdrift_results, authority_escalations_refused,
    objective_drift_resistance,
)
from .beliefshift_runner import (
    KIND_TO_FORM, beliefshift_results, run_family,
    run_normalized_drift,
)
from .memevo_runner import (
    memevo_results, memory_poisoning_resistance,
    poisoning_rejected_count,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V351Report, build_real_drift_artifact, build_report,
    claim_lineage_preservation, drift_run_metrics, drift_visibility,
    governance_preservation, replay_stability,
)
from .scorecard import (
    DriftRunScorecard, all_drift_results, drift_scorecards,
)


__all__ = [
    "KIND_TO_FORM",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "DriftRunScorecard",
    "V351Report",
    "agentdrift_results",
    "all_drift_results",
    "authority_escalations_refused",
    "beliefshift_results",
    "build_real_drift_artifact",
    "build_report",
    "claim_lineage_preservation",
    "drift_run_metrics",
    "drift_scorecards",
    "drift_visibility",
    "governance_preservation",
    "memevo_results",
    "memory_poisoning_resistance",
    "objective_drift_resistance",
    "poisoning_rejected_count",
    "replay_stability",
    "run_family",
    "run_normalized_drift",
]
