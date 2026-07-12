"""Router-governance layer — DESi diagnoses, the router acts.

A thin, deterministic layer that consumes DESi/Layer-9 diagnostics (a read-only ``DesiReport``),
chooses an epistemic mode (alongside the existing tool/local/API routing), optionally builds a
guarded preprompt, verifies the answer after the fact, and audits the decision. It never enforces
inside DESi, never mutates persistent state (Layer-9's gate stays the authority), and never claims
metadata governance is proven.
"""
from desi_router.governance.audit import GovernanceAudit, audit_event
from desi_router.governance.clsp import (
    CATEGORIES as CLSP_CATEGORIES,
)
from desi_router.governance.clsp import (
    Cluster,
    classify,
    overamplification,
    to_eir_candidates,
    to_report_inputs,
)
from desi_router.governance.correction_packet import (
    build_correction_packet,
    packet_applies,
)
from desi_router.governance.modes import (
    MODES,
    RouterDecision,
    select_mode,
    update_allowed_after_verifier,
)
from desi_router.governance.k_stability import verdict_unstable
from desi_router.governance.preprompt import guarded_preprompt
from desi_router.governance.report import DesiReport, report_from_snapshot
from desi_router.governance.slice_attack import (
    ATTACK_VECTORS,
    SliceAttackResult,
    attack_slice,
)
from desi_router.governance.two_tier_gate import (
    GateResult,
    decide_commit,
    is_critical_update,
)
from desi_router.governance.verifier import VerifierResult, verify_answer

__all__ = ["DesiReport", "report_from_snapshot", "RouterDecision", "select_mode",
           "update_allowed_after_verifier", "MODES", "guarded_preprompt", "verify_answer",
           "VerifierResult", "GovernanceAudit", "audit_event",
           "GateResult", "decide_commit", "is_critical_update",
           "build_correction_packet", "packet_applies",
           "attack_slice", "SliceAttackResult", "ATTACK_VECTORS", "verdict_unstable",
           "classify", "to_eir_candidates", "to_report_inputs", "overamplification", "Cluster",
           "CLSP_CATEGORIES"]
