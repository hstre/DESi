"""DESi v33.1 - Drift Benchmark Adapter (read-only).

Maps external drift benchmark forms onto DESi's six internal drift
dimensions. Claims may move (visibly, lineage-tracked); the protected
core never drifts; objective drift and memory poisoning are resisted.
Drift is reported, never hidden, and governance semantics are kept.
"""
from __future__ import annotations

from .agentlab_adapter import (
    AGENTLAB_FORMS, all_forms_keep_core_fixed,
    contradiction_claim_drift, core_unmoved, evidence_claim_drift,
    memory_poisoning_rejected,
)
from .belief_shift_adapter import (
    belief_shift, belief_shift_is_visible, objective_is_pinned,
    objective_shift,
)
from .drift_adapter import (
    CORE_DRIFT_DIMENSIONS, DRIFT_FORMS, INTERNAL_DRIFT_DIMENSIONS,
    DriftBenchmarkAdapter, adapter, map_form,
)
from .output_drift_adapter import (
    artifact_drift, artifact_is_stable, output_claim_drift,
    replay_drift,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_MAPPED, VERDICT_PARTIAL,
    V331Report, build_drift_artifact, build_report,
    claim_lineage_preservation, drift_mapping_integrity,
    drift_metrics, drift_visibility, governance_preservation,
    replay_stability,
)


__all__ = [
    "AGENTLAB_FORMS",
    "CORE_DRIFT_DIMENSIONS",
    "DRIFT_FORMS",
    "INTERNAL_DRIFT_DIMENSIONS",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_MAPPED",
    "VERDICT_PARTIAL",
    "DriftBenchmarkAdapter",
    "V331Report",
    "adapter",
    "all_forms_keep_core_fixed",
    "artifact_drift",
    "artifact_is_stable",
    "belief_shift",
    "belief_shift_is_visible",
    "build_drift_artifact",
    "build_report",
    "claim_lineage_preservation",
    "contradiction_claim_drift",
    "core_unmoved",
    "drift_mapping_integrity",
    "drift_metrics",
    "drift_visibility",
    "evidence_claim_drift",
    "governance_preservation",
    "map_form",
    "memory_poisoning_rejected",
    "objective_is_pinned",
    "objective_shift",
    "output_claim_drift",
    "replay_drift",
    "replay_stability",
]
