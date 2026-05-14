"""Exception hierarchy for the SPL adapter (v1.0).

The adapter never raises naked exceptions across its public surface
unless something the *caller* did is wrong. Internal errors
(API timeout, malformed LLM JSON, cost-guard exhaustion) are
**fail-closed**: the offending input produces zero claims and a
ledger event is emitted, but no exception propagates to the caller.

These classes exist so test code can assert on the specific failure
mode when it deliberately drives the adapter into one.
"""
from __future__ import annotations


class SPLError(Exception):
    """Base class for every SPL adapter error."""


class GatewayRejection(SPLError):
    """A ClaimCandidate did not pass the gateway and was discarded.

    Attribute ``reason`` is one of a closed taxonomy:

    * ``ambiguous_claim``
    * ``hallucinated_relation``
    * ``empty_content``
    * ``invalid_method``
    * ``invalid_state``
    * ``no_backend_output``
    * ``per_document_budget_exhausted``  (v1.1)
    * ``unsupported_document_type``       (v1.1)
    * ``empty_document``                  (v1.1)
    * ``response_too_large``              (v1.1)
    """

    def __init__(self, reason: str, message: str = "") -> None:
        self.reason = reason
        super().__init__(message or reason)


class BackendError(SPLError):
    """The semantic backend failed to produce usable output.

    Used for: API errors, timeouts, invalid-JSON responses, empty
    outputs, oversized payloads, document-parser failures. The
    adapter converts every backend error into a fail-closed
    projection (no claims, ledger entry).

    v1.1 adds a coarse :attr:`category` so the adapter can choose
    between the ``LLM_REQUEST_FAILED`` (network) and
    ``LLM_RESPONSE_REJECTED`` (response-level) ledger events.
    """

    NETWORK_KINDS: frozenset[str] = frozenset({
        "timeout", "url_error", "transport_failed", "retry_exhausted",
        "missing_api_key", "llm_call_failed", "connection_error",
    })
    RESPONSE_KINDS: frozenset[str] = frozenset({
        "invalid_json", "invalid_schema", "empty_output",
        "response_too_large", "invalid_encoding",
    })
    PARSER_KINDS: frozenset[str] = frozenset({
        "unsupported_document_type", "empty_document",
        "pdf_parse_failed",
    })

    def __init__(self, kind: str, message: str = "") -> None:
        self.kind = kind
        super().__init__(message or kind)

    @property
    def category(self) -> str:
        if self.kind in self.NETWORK_KINDS:
            return "network"
        if self.kind in self.RESPONSE_KINDS:
            return "response"
        if self.kind in self.PARSER_KINDS:
            return "parser"
        # HTTP error kinds carry the status code as suffix.
        if self.kind.startswith("http_"):
            return "network"
        return "other"


class CostGuardError(SPLError):
    """The LLM cost guard refused another projection in this run."""


__all__ = [
    "BackendError",
    "CostGuardError",
    "GatewayRejection",
    "SPLError",
]
