"""SPL DESi Adapter — natural-language entry point (v1.0).

External text becomes a DESi Claim only via this package. The order
of operations is strict:

    Text
      ↓
    SemanticBackend.extract_units(text)
      ↓
    SemanticBackend.project_units(...) → tuple[ClaimCandidate, ...]
      ↓
    SPLGateway.admit(candidates, run_id=…)
      ↓
    candidate_to_claim(...) → tuple[Claim, ...]

The package is read-only with respect to memory and evolution
state. It never writes claims, never decides merges, never decides
promotion, never produces relations.
"""
from __future__ import annotations

from .adapter import (
    LLM_PROJECTION_BUDGET,
    SPLAdapter,
    SPLGateway,
    SPLProjectionResult,
)
from .backend import (
    DEEPSEEK_MODEL_NAME,
    DEEPSEEK_MODEL_VERSION,
    DeterministicSemanticBackend,
    LLMSemanticBackend,
    SemanticBackend,
    SemanticUnit,
)
from .errors import (
    BackendError,
    CostGuardError,
    GatewayRejection,
    SPLError,
)
from .mapping import (
    LEGAL_METHODS,
    ClaimCandidate,
    candidate_to_claim,
)
from .provenance import (
    SPLProvenance,
    make_deterministic_provenance,
    make_llm_provenance,
)

__all__ = [
    "BackendError",
    "ClaimCandidate",
    "CostGuardError",
    "DEEPSEEK_MODEL_NAME",
    "DEEPSEEK_MODEL_VERSION",
    "DeterministicSemanticBackend",
    "GatewayRejection",
    "LEGAL_METHODS",
    "LLMSemanticBackend",
    "LLM_PROJECTION_BUDGET",
    "SPLAdapter",
    "SPLError",
    "SPLGateway",
    "SPLProjectionResult",
    "SPLProvenance",
    "SemanticBackend",
    "SemanticUnit",
    "candidate_to_claim",
    "make_deterministic_provenance",
    "make_llm_provenance",
]
