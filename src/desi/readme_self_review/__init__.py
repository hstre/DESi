"""DESi README / System-Paper self-review (read-only).

An internal consistency and overreach audit of DESi's own
documentation (README on main = System Paper v1.1), performed by the
Reviewer Port against a fixed snapshot. DESi treats the README as an
external claim artifact and does NOT validate itself. The audit is
deliberately hard: its purpose is to surface overreach, unsupported
or unverified claims, scanner risks and misleading framing.
"""
from __future__ import annotations

from .claim_audit import (
    CLAIM_STATUSES, Claim, GateCondition, artifact_backing_rate,
    claims, claims_by_status, external_generalization_guard,
    forbidden_term_risk, gate_conditions, gate_failing_conditions,
    gate_passes_all, gate_passing_conditions, overreach_claims,
    replay_explanation_correct, synthetic_vs_real_separation,
    unsupported_numeric_claims,
)
from .report import (
    REPORT_VERDICTS, VERDICT_NOT_READY, VERDICT_PUBLIC_READY,
    build_claim_audit_artifact, build_go_no_go,
    build_overreach_report, build_revision_suggestions,
    recommendation,
)
from .reviewer_port import (
    AUDIT_FRAMING, compression_range_consistent,
    compression_range_phrasings, forbidden_term_hits, reviewed_hash,
    reviewer_port_module_present, stale_regression_runs,
)


__all__ = [
    "AUDIT_FRAMING",
    "CLAIM_STATUSES",
    "REPORT_VERDICTS",
    "VERDICT_NOT_READY",
    "VERDICT_PUBLIC_READY",
    "Claim",
    "GateCondition",
    "artifact_backing_rate",
    "build_claim_audit_artifact",
    "build_go_no_go",
    "build_overreach_report",
    "build_revision_suggestions",
    "claims",
    "claims_by_status",
    "compression_range_consistent",
    "compression_range_phrasings",
    "external_generalization_guard",
    "forbidden_term_hits",
    "forbidden_term_risk",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "gate_passing_conditions",
    "overreach_claims",
    "recommendation",
    "replay_explanation_correct",
    "reviewed_hash",
    "reviewer_port_module_present",
    "stale_regression_runs",
    "synthetic_vs_real_separation",
    "unsupported_numeric_claims",
]
