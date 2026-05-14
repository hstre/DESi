"""Authority-free logical belief gate (v1.2).

A claim is never upgraded by authority, prestige, repetition,
citation count, document count, academic title, institutional
reputation, or source popularity.

A claim may only be upgraded if its reasoning chain is explicit,
gap-free, structurally valid, and replayable.

The logic package never reads source / author / title metadata,
even when it is offered as a kwarg. The five inference rules
(SYLLOGISM, IMPLICATION, TRANSITIVITY, CONTRADICTION, EQUIVALENCE)
are a closed enum; nothing outside that set can produce a
``LOGICALLY_SUPPORTED`` verdict.
"""
from __future__ import annotations

from .audit import (
    AuditResult,
    LogicalAuditor,
    LogicalState,
    replay,
)
from .bridge_claims import BRIDGE_METHOD, BridgeClaim, BridgeKind, propose_bridge
from .gap_detector import Gap, GapKind, detect_gap
from .inference import (
    InferenceMatch,
    InferenceRule,
    try_each_rule,
    validate_inference,
)
from .premises import (
    ConclusionProposition,
    Premise,
    PremiseExtractor,
    PremiseKind,
    Propositions,
)
from .proof_chain import ProofChain

__all__ = [
    "AuditResult",
    "BRIDGE_METHOD",
    "BridgeClaim",
    "BridgeKind",
    "ConclusionProposition",
    "Gap",
    "GapKind",
    "InferenceMatch",
    "InferenceRule",
    "LogicalAuditor",
    "LogicalState",
    "Premise",
    "PremiseExtractor",
    "PremiseKind",
    "ProofChain",
    "Propositions",
    "detect_gap",
    "propose_bridge",
    "replay",
    "try_each_rule",
    "validate_inference",
]
