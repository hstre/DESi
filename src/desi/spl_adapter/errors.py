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
    """

    def __init__(self, reason: str, message: str = "") -> None:
        self.reason = reason
        super().__init__(message or reason)


class BackendError(SPLError):
    """The semantic backend failed to produce usable output.

    Used for: API errors, timeouts, invalid-JSON responses, empty
    outputs. The adapter converts every backend error into a
    fail-closed projection (no claims, ledger entry).
    """

    def __init__(self, kind: str, message: str = "") -> None:
        self.kind = kind
        super().__init__(message or kind)


class CostGuardError(SPLError):
    """The LLM cost guard refused another projection in this run."""


__all__ = [
    "BackendError",
    "CostGuardError",
    "GatewayRejection",
    "SPLError",
]
