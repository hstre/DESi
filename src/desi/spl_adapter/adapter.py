"""SPLGateway + SPLAdapter — v1.0 entry point for natural-language input.

The :class:`SPLAdapter` is the **only** path by which free-form text
becomes a DESi Claim. Direct text → Claim construction is not
forbidden by Python's type system (callers can still construct
:class:`desi.memory.claim.Claim` by hand), but the v1.0 contract is:

* every Claim originating from natural-language input must come out of
  :meth:`SPLAdapter.project_text`;
* the adapter routes the input through a backend, then through the
  gateway, then through the candidate-to-claim mapping;
* the gateway is the load-bearing arbiter: it rejects ambiguous
  claims, hallucinated relations, and any LLM output that exceeds the
  cost-guard budget.

The adapter never writes to memory. It returns a tuple of Claim
objects; downstream code (e.g. a MemoryRecorder) decides whether and
how to persist them. The adapter never decides merge, never decides
contradiction, never decides promotion.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from ..memory.claim import Claim
from .backend import (
    DeterministicSemanticBackend,
    SemanticBackend,
    SemanticUnit,
)
from .errors import BackendError, CostGuardError, GatewayRejection
from .mapping import ClaimCandidate, candidate_to_claim
from .parser import DocumentParser, ParseResult
from .source import SourceDocument


# v1.0 directive: an LLM backend may produce at most 20 projections
# per run. After that the cost guard fail-closes: subsequent
# project_text calls return zero claims and log a ledger event.
LLM_PROJECTION_BUDGET: int = 20

# v1.1 directive: each document gets its own slice of the per-adapter
# budget so a single noisy document cannot exhaust the run.
PER_DOCUMENT_PROJECTION_BUDGET: int = 5


@dataclass
class SPLProjectionResult:
    """Return shape of :meth:`SPLAdapter.project_text`.

    The primary payload is ``claims`` (a tuple of DESi Claim objects).
    The rest of the fields are for audit / inspection.
    """

    claims: tuple[Claim, ...]
    rejected: tuple[tuple[ClaimCandidate, str], ...] = field(
        default_factory=tuple,
    )
    candidates_seen: int = 0
    backend_error: str = ""
    cost_guarded: bool = False


class SPLGateway:
    """The only place where a ClaimCandidate becomes a Claim.

    Rejection rules (closed set):

    * ``ambiguous_claim``         — candidate flagged ``ambiguous=True``
                                    by the backend, *or* confidence
                                    below 0.5.
    * ``hallucinated_relation``    — candidate carries a non-empty
                                    ``proposed_relations`` tuple.
                                    Relations are DESi's job, not the
                                    SPL's.
    * ``empty_content``            — content string is empty.
    * ``invalid_method``           — method is not in the closed set
                                    :data:`desi.spl_adapter.LEGAL_METHODS`.

    Every rejection is observable: callers receive a list of
    ``(candidate, reason)`` pairs alongside the accepted claims, and
    each rejection emits a ``SEMANTIC_PROJECTION_REJECTED`` ledger
    event when a ledger is wired in.
    """

    AMBIGUITY_FLOOR: float = 0.5

    def admit(
        self,
        candidates: tuple[ClaimCandidate, ...],
        *,
        run_id: str,
    ) -> tuple[
        tuple[Claim, ...],
        tuple[tuple[ClaimCandidate, str], ...],
    ]:
        """Filter ``candidates`` into (admitted claims, rejected pairs)."""
        admitted: list[Claim] = []
        rejected: list[tuple[ClaimCandidate, str]] = []
        for c in candidates:
            reason = self._first_rejection_reason(c)
            if reason is not None:
                rejected.append((c, reason))
                continue
            try:
                claim = candidate_to_claim(c, run_id=run_id)
            except GatewayRejection as exc:
                rejected.append((c, exc.reason))
                continue
            admitted.append(claim)
        return tuple(admitted), tuple(rejected)

    def _first_rejection_reason(self, c: ClaimCandidate) -> str | None:
        if not c.content:
            return "empty_content"
        if c.proposed_relations:
            return "hallucinated_relation"
        if c.ambiguous:
            return "ambiguous_claim"
        if c.confidence < self.AMBIGUITY_FLOOR:
            return "ambiguous_claim"
        return None


class SPLAdapter:
    """The v1.0 natural-language entry point.

    Construction::

        adapter = SPLAdapter()                          # deterministic backend
        adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=fn))

    The optional ``ledger`` keyword accepts a
    :class:`desi.evolution.EvolutionLedger` (or compatible) so that
    every projection emits three audit events:

    1. ``SEMANTIC_PROJECTION_STARTED`` — on entry,
    2. one ``SEMANTIC_CANDIDATE_EMITTED`` per backend candidate,
    3. ``SEMANTIC_PROJECTION_REJECTED`` per gateway rejection.
    """

    def __init__(
        self,
        *,
        backend: SemanticBackend | None = None,
        ledger: Any | None = None,
        gateway: SPLGateway | None = None,
        llm_projection_budget: int = LLM_PROJECTION_BUDGET,
        per_document_budget: int = PER_DOCUMENT_PROJECTION_BUDGET,
        parser: DocumentParser | None = None,
    ) -> None:
        self._backend: SemanticBackend = (
            backend if backend is not None else DeterministicSemanticBackend()
        )
        self._gateway = gateway if gateway is not None else SPLGateway()
        self._ledger = ledger
        self._budget = int(llm_projection_budget)
        self._per_doc_budget = int(per_document_budget)
        self._llm_calls_made = 0
        self._calls_per_document: dict[str, int] = {}
        self._parser = parser if parser is not None else DocumentParser()

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------

    @property
    def backend(self) -> SemanticBackend:
        return self._backend

    @property
    def gateway(self) -> SPLGateway:
        return self._gateway

    @property
    def llm_calls_made(self) -> int:
        return self._llm_calls_made

    @property
    def llm_calls_remaining(self) -> int:
        return max(0, self._budget - self._llm_calls_made)

    def project_text(
        self,
        text: str,
        *,
        run_id: str | None = None,
        language: str = "",
        source: str = "",
        author: str = "",
        document_id: str = "",
        _source_provenance: dict[str, str] | None = None,
    ) -> SPLProjectionResult:
        """Run text through the backend → gateway → mapping pipeline.

        ``_source_provenance`` is an internal kwarg used by
        :meth:`project_document` to thread the parser's
        ``(content_type, parser_version, parser_hash)`` triple into
        the candidate's :class:`SPLProvenance`. Direct callers
        should not pass it.
        """
        if run_id is None:
            run_id = "spl_" + uuid.uuid4().hex[:12]
        backend_label = self._backend.method_label
        self._log("SEMANTIC_PROJECTION_STARTED", {
            "run_id": run_id,
            "source_type": source or "free_text",
            "backend": backend_label,
            "document_id": document_id,
        })
        is_llm = backend_label == "llm_semantic_projection"
        # Cost guard #1: per-adapter LLM budget.
        if is_llm and self._llm_calls_made >= self._budget:
            self._log("SEMANTIC_PROJECTION_REJECTED", {
                "run_id": run_id,
                "reason": "cost_guard_exhausted",
                "calls_made": self._llm_calls_made,
                "budget": self._budget,
            })
            return SPLProjectionResult(
                claims=(),
                rejected=(),
                candidates_seen=0,
                backend_error="",
                cost_guarded=True,
            )
        # Cost guard #2: per-document LLM budget (v1.1).
        if (is_llm and document_id
                and self._calls_per_document.get(document_id, 0)
                >= self._per_doc_budget):
            self._log("SEMANTIC_PROJECTION_REJECTED", {
                "run_id": run_id,
                "reason": "per_document_budget_exhausted",
                "document_id": document_id,
                "calls_for_document":
                    self._calls_per_document[document_id],
                "per_document_budget": self._per_doc_budget,
            })
            return SPLProjectionResult(
                claims=(),
                rejected=(),
                candidates_seen=0,
                backend_error="",
                cost_guarded=True,
            )

        if is_llm:
            self._log("LLM_REQUEST_STARTED", {
                "run_id": run_id,
                "model_name": getattr(self._backend, "model_name",
                                       "unknown"),
                "document_id": document_id,
            })

        # Fail-closed: any BackendError on extract_units → zero claims.
        try:
            units = self._backend.extract_units(text)
            candidates = self._backend.project_units(
                units,
                document_id=document_id, author=author, language=language,
            )
        except BackendError as exc:
            event_name = (
                "LLM_RESPONSE_REJECTED" if (is_llm and exc.category == "response")
                else "LLM_REQUEST_FAILED" if is_llm
                else "SEMANTIC_PROJECTION_REJECTED"
            )
            payload: dict[str, Any] = {
                "run_id": run_id,
                "reason": exc.kind,
            }
            if is_llm:
                payload["retry_count"] = 0
            else:
                payload["reason"] = f"backend_error:{exc.kind}"
                payload["message"] = str(exc)
            self._log(event_name, payload)
            if is_llm:
                self._llm_calls_made += 1
                if document_id:
                    self._calls_per_document[document_id] = (
                        self._calls_per_document.get(document_id, 0) + 1
                    )
            return SPLProjectionResult(
                claims=(),
                rejected=(),
                candidates_seen=0,
                backend_error=exc.kind,
                cost_guarded=False,
            )

        if is_llm:
            self._llm_calls_made += 1
            if document_id:
                self._calls_per_document[document_id] = (
                    self._calls_per_document.get(document_id, 0) + 1
                )
            raw_out = getattr(self._backend, "_last_raw_output", "")
            self._log("LLM_RESPONSE_ACCEPTED", {
                "run_id": run_id,
                "output_hash": (
                    candidates[0].spl_provenance.output_hash
                    if candidates else ""
                ),
                "size_bytes": len(raw_out.encode("utf-8")),
            })

        # v1.1: attach source-document audit fields to every candidate's
        # provenance, when a document is in play.
        if _source_provenance:
            candidates = tuple(
                _attach_source_provenance(c, _source_provenance)
                for c in candidates
            )

        # Backend produced zero usable units → fail closed, ledger
        # event but no exception.
        if not candidates:
            self._log("SEMANTIC_PROJECTION_REJECTED", {
                "run_id": run_id,
                "reason": "no_backend_output",
            })
            return SPLProjectionResult(
                claims=(),
                rejected=(),
                candidates_seen=0,
                backend_error="",
                cost_guarded=False,
            )

        # Log each candidate that the backend emitted (pre-gateway).
        for c in candidates:
            self._log("SEMANTIC_CANDIDATE_EMITTED", {
                "run_id": run_id,
                "candidate_id": "cnd_" + uuid.uuid4().hex[:12],
                "method": c.method,
                "output_hash": c.spl_provenance.output_hash,
                "ambiguous": c.ambiguous,
                "proposed_relations": [list(r) for r in c.proposed_relations],
            })

        admitted, rejected = self._gateway.admit(candidates, run_id=run_id)

        for (cand, reason) in rejected:
            self._log("SEMANTIC_PROJECTION_REJECTED", {
                "run_id": run_id,
                "reason": reason,
                "method": cand.method,
                "content_preview": cand.content[:80],
            })

        return SPLProjectionResult(
            claims=admitted,
            rejected=rejected,
            candidates_seen=len(candidates),
            backend_error="",
            cost_guarded=False,
        )

    # ------------------------------------------------------------------
    # v1.1 — project_document entry point
    # ------------------------------------------------------------------

    def project_document(
        self,
        doc: SourceDocument,
        *,
        run_id: str | None = None,
    ) -> SPLProjectionResult:
        """Parse ``doc`` to normalised text, then run the v1.0 pipeline.

        Fail-closed on every parser error: an unsupported MIME type,
        an empty document, or any other ``BackendError`` from the
        parser yields zero claims and a
        ``SEMANTIC_PROJECTION_REJECTED`` ledger entry.

        The per-document cost guard (5 LLM projections per
        ``document_id``) applies on top of the per-adapter
        :data:`LLM_PROJECTION_BUDGET` (20 total).
        """
        if run_id is None:
            run_id = "spl_" + uuid.uuid4().hex[:12]
        try:
            parsed = self._parser.parse(doc)
        except BackendError as exc:
            self._log("SEMANTIC_PROJECTION_REJECTED", {
                "run_id": run_id,
                "reason": exc.kind,
                "document_id": doc.document_id,
                "content_type": doc.content_type,
            })
            return SPLProjectionResult(
                claims=(),
                rejected=(),
                candidates_seen=0,
                backend_error=exc.kind,
                cost_guarded=False,
            )

        self._log("SOURCE_DOCUMENT_PARSED", {
            "run_id": run_id,
            "document_id": doc.document_id,
            "content_type": doc.content_type,
            "text_length": len(parsed.normalized_text),
            "parser_version": parsed.parser_version,
            "parser_hash": parsed.parser_hash,
        })

        return self.project_text(
            parsed.normalized_text,
            run_id=run_id,
            language=doc.language,
            source="source_document",
            author=doc.author,
            document_id=doc.document_id,
            _source_provenance={
                "content_type": parsed.content_type,
                "parser_version": parsed.parser_version,
                "parser_hash": parsed.parser_hash,
            },
        )

    def projections_for_document(self, document_id: str) -> int:
        """How many LLM projections this adapter has made for ``document_id``."""
        return self._calls_per_document.get(document_id, 0)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _log(self, event_name: str, payload: dict[str, Any]) -> None:
        if self._ledger is None:
            return
        # Import here so unit tests that don't use the ledger don't pay
        # the import cost.
        from ..evolution.ledger import LedgerEventType
        event_map = {
            "SEMANTIC_PROJECTION_STARTED":
                LedgerEventType.SEMANTIC_PROJECTION_STARTED,
            "SEMANTIC_CANDIDATE_EMITTED":
                LedgerEventType.SEMANTIC_CANDIDATE_EMITTED,
            "SEMANTIC_PROJECTION_REJECTED":
                LedgerEventType.SEMANTIC_PROJECTION_REJECTED,
            "SOURCE_DOCUMENT_PARSED":
                LedgerEventType.SOURCE_DOCUMENT_PARSED,
            "LLM_REQUEST_STARTED":
                LedgerEventType.LLM_REQUEST_STARTED,
            "LLM_REQUEST_FAILED":
                LedgerEventType.LLM_REQUEST_FAILED,
            "LLM_RESPONSE_ACCEPTED":
                LedgerEventType.LLM_RESPONSE_ACCEPTED,
            "LLM_RESPONSE_REJECTED":
                LedgerEventType.LLM_RESPONSE_REJECTED,
        }
        event_type = event_map[event_name]
        self._ledger.append(event_type, payload)


def _attach_source_provenance(
    candidate: ClaimCandidate,
    source_fields: dict[str, str],
) -> ClaimCandidate:
    new_prov = candidate.spl_provenance.with_source_fields(
        content_type=source_fields.get("content_type", ""),
        parser_version=source_fields.get("parser_version", ""),
        parser_hash=source_fields.get("parser_hash", ""),
    )
    return ClaimCandidate(
        content=candidate.content,
        method=candidate.method,
        spl_provenance=new_prov,
        raw_text=candidate.raw_text,
        confidence=candidate.confidence,
        ambiguous=candidate.ambiguous,
        proposed_relations=candidate.proposed_relations,
    )


__all__ = [
    "LLM_PROJECTION_BUDGET",
    "SPLAdapter",
    "SPLGateway",
    "SPLProjectionResult",
]
