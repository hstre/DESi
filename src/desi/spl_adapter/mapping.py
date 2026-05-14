"""ClaimCandidate → DESi Claim mapping (v1.0).

A :class:`ClaimCandidate` is the SPL's intermediate type — it sits
between the backend's raw output and DESi's memory layer. v1.0
mandates a tight, audited mapping into a DESi
:class:`desi.memory.claim.Claim`:

* ``content`` carries the canonical semantic proposition (not the raw
  source text).
* ``method`` is exactly one of two values:
  ``"deterministic_semantic_projection"`` or
  ``"llm_semantic_projection"``. No other method strings are
  permitted at the gateway.
* ``state`` is **always** :attr:`ClaimState.PROPOSED`. SPL never
  marks anything CONFIRMED, REVISED, MERGED, REJECTED, or SPLIT —
  those are downstream verdicts.

The mandatory "content ≠ method" invariant comes from the S7 family:
two claims with the same surface content but different methods must
remain distinct. The mapping never collapses them; identity is
derived from ``content + method + run_id`` (see :class:`Claim`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..memory.claim import Claim, ClaimState, Provenance
from .errors import GatewayRejection
from .provenance import SPLProvenance


# v1.0 directive: only these two method strings may attach to a Claim
# produced by SPL. Any other value is a gateway error and the
# candidate is rejected with ``reason="invalid_method"``.
LEGAL_METHODS: frozenset[str] = frozenset({
    "deterministic_semantic_projection",
    "llm_semantic_projection",
})


@dataclass
class ClaimCandidate:
    """Intermediate type emitted by an :class:`SemanticBackend`.

    ``proposed_relations`` is informational only — v1.0 forbids the
    SPL from emitting relations. If a backend ever does propose one
    (e.g. an LLM that hallucinated a SUPPORTS edge), the gateway
    rejects the candidate with ``reason="hallucinated_relation"``.
    """

    content: str
    method: str
    spl_provenance: SPLProvenance
    raw_text: str = ""
    confidence: float = 1.0
    ambiguous: bool = False
    proposed_relations: tuple[tuple[str, str, str], ...] = field(
        default_factory=tuple,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "method": self.method,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "ambiguous": self.ambiguous,
            "proposed_relations": [list(r) for r in self.proposed_relations],
            "spl_provenance": self.spl_provenance.to_dict(),
        }


def candidate_to_claim(
    candidate: ClaimCandidate,
    *,
    run_id: str,
) -> Claim:
    """Map a :class:`ClaimCandidate` to a memory-layer Claim.

    Refuses to map if:

    * ``content`` is empty
    * ``method`` is not in :data:`LEGAL_METHODS`

    State is always :attr:`ClaimState.PROPOSED`. Confidence is
    propagated from the candidate but clipped to ``[0.0, 1.0]``.
    """
    if not candidate.content:
        raise GatewayRejection("empty_content", "candidate has empty content")
    if candidate.method not in LEGAL_METHODS:
        raise GatewayRejection("invalid_method",
                                f"method={candidate.method!r} not allowed")
    operator_path: tuple[str, ...] = (candidate.method,)
    prov = Provenance(
        source=candidate.spl_provenance.source,
        run_id=run_id,
        operator_path=operator_path,
        timestamp=candidate.spl_provenance.timestamp,
    )
    return Claim(
        content=candidate.content,
        method=candidate.method,
        state=ClaimState.PROPOSED,
        confidence=max(0.0, min(1.0, candidate.confidence)),
        provenance=prov,
    )


__all__ = [
    "ClaimCandidate",
    "LEGAL_METHODS",
    "candidate_to_claim",
]
