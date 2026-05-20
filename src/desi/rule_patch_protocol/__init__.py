"""DESi v2.8 Rule Patch Protocol — read-only orchestration."""
from __future__ import annotations

from .candidate import GuardDescriptor, PatchCandidate
from .known_patches import (
    causal_chain_v2_7_candidate,
    fake_rule_without_guards_candidate,
)
from .phases import PHASE_ORDER, PatchPhase
from .protocol import RulePatchProtocol
from .record import (
    PhaseOutcome,
    RulePatchRecord,
    compute_record_replay_hash,
)
from .runners import (
    compute_benchmark_hashes,
    run_discovery,
    run_guard_synthesis,
    run_implementation,
    run_regression,
    run_replay_verification,
    run_risk_probe,
)

__all__ = [
    "GuardDescriptor",
    "PHASE_ORDER",
    "PatchCandidate",
    "PatchPhase",
    "PhaseOutcome",
    "RulePatchProtocol",
    "RulePatchRecord",
    "causal_chain_v2_7_candidate",
    "compute_benchmark_hashes",
    "compute_record_replay_hash",
    "fake_rule_without_guards_candidate",
    "run_discovery",
    "run_guard_synthesis",
    "run_implementation",
    "run_regression",
    "run_replay_verification",
    "run_risk_probe",
]
