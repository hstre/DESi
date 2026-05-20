"""SPL DESi Adapter — natural-language entry point.

v1.0: deterministic + stubbed LLM backends.
v1.1: real DeepSeek client (env-only key, 10s timeout, 2 retries,
50 KB response cap), :class:`SourceDocument`, multi-MIME parsing
(plain / markdown / html / pdf), per-document cost guard, source
provenance fields, and 5 new ledger event types.

External text becomes a DESi Claim only via this package. The order
of operations is strict:

    SourceDocument             ─┐
      │                          ↓
      ↓                       project_document (v1.1)
    DocumentParser.parse(...)   │
      ↓                          ↓
    normalised text  ─────────→ project_text (v1.0)
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
    PER_DOCUMENT_PROJECTION_BUDGET,
    SPLAdapter,
    SPLGateway,
    SPLProjectionResult,
)
from .backend import (
    DEEPSEEK_MODEL_NAME,
    DEEPSEEK_MODEL_VERSION,
    MAX_LLM_RESPONSE_BYTES,
    DeterministicSemanticBackend,
    LLMSemanticBackend,
    SemanticBackend,
    SemanticUnit,
)
from .deepseek_client import (
    API_KEY_ENV_VAR,
    DEEPSEEK_API_URL,
    DEEPSEEK_MODEL_ID,
    DeepSeekClient,
    DeepSeekResponse,
    HARD_TIMEOUT_SECONDS,
    MAX_RESPONSE_SIZE_BYTES,
    MAX_RETRIES,
    RETRY_BACKOFF_SECONDS,
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
from .parser import (
    PARSER_VERSION,
    DocumentParser,
    ParseResult,
)
from .provenance import (
    SPLProvenance,
    make_deterministic_provenance,
    make_llm_provenance,
)
from .source import SUPPORTED_CONTENT_TYPES, SourceDocument

__all__ = [
    "API_KEY_ENV_VAR",
    "BackendError",
    "ClaimCandidate",
    "CostGuardError",
    "DEEPSEEK_API_URL",
    "DEEPSEEK_MODEL_ID",
    "DEEPSEEK_MODEL_NAME",
    "DEEPSEEK_MODEL_VERSION",
    "DeepSeekClient",
    "DeepSeekResponse",
    "DeterministicSemanticBackend",
    "DocumentParser",
    "GatewayRejection",
    "HARD_TIMEOUT_SECONDS",
    "LEGAL_METHODS",
    "LLMSemanticBackend",
    "LLM_PROJECTION_BUDGET",
    "MAX_LLM_RESPONSE_BYTES",
    "MAX_RESPONSE_SIZE_BYTES",
    "MAX_RETRIES",
    "PARSER_VERSION",
    "PER_DOCUMENT_PROJECTION_BUDGET",
    "ParseResult",
    "RETRY_BACKOFF_SECONDS",
    "SPLAdapter",
    "SPLError",
    "SPLGateway",
    "SPLProjectionResult",
    "SPLProvenance",
    "SUPPORTED_CONTENT_TYPES",
    "SemanticBackend",
    "SemanticUnit",
    "SourceDocument",
    "candidate_to_claim",
    "make_deterministic_provenance",
    "make_llm_provenance",
]
