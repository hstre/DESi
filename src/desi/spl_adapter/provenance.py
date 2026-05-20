"""SPLProvenance — the rich provenance record an SPL candidate carries.

The DESi :class:`desi.memory.claim.Provenance` model has four
mandatory fields (``source``, ``run_id``, ``operator_path``,
``timestamp``). It deliberately does **not** know about LLM-specific
metadata; the memory layer must work for non-LLM sources too.

SPL therefore keeps its own provenance type alongside the DESi
Provenance. When a :class:`desi.spl_adapter.ClaimCandidate` is mapped
to a DESi Claim, the four DESi-required fields are copied into the
Claim's Provenance; the LLM-specific fields are recorded in the
ledger via the SEMANTIC_CANDIDATE_EMITTED event.

This split is the v1.0 contract: every model-specific datum the SPL
saw is preserved in the audit trail, but the memory layer's
properties stay backend-agnostic.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _short_hash(payload: Any) -> str:
    raw = repr(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True)
class SPLProvenance:
    """Per-candidate provenance record for the SPL adapter.

    ``source`` is the only field shared with DESi Provenance; it
    distinguishes the deterministic from the LLM backend
    (``"spl_deterministic"`` vs ``"spl_llm"``). The LLM-specific
    fields are mandatory for ``spl_llm`` and default to empty strings
    / zero values for ``spl_deterministic`` (where they are not
    meaningful).

    v1.1 adds three source-document fields (``content_type``,
    ``parser_version``, ``parser_hash``) that are populated when the
    candidate originated from a :class:`SourceDocument` flowing
    through :meth:`SPLAdapter.project_document`. Empty otherwise.
    """

    source: str
    # LLM-specific metadata (mandatory for source="spl_llm"; empty for
    # source="spl_deterministic" by convention).
    model_name: str = ""
    model_version: str = ""
    prompt_hash: str = ""
    temperature: float = 0.0
    max_tokens: int = 0
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    output_hash: str = ""
    # Optional caller-supplied metadata.
    document_id: str = ""
    author: str = ""
    language: str = ""
    # v1.1: source-document audit fields (set by project_document).
    content_type: str = ""
    parser_version: str = ""
    parser_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prompt_hash": self.prompt_hash,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timestamp": self.timestamp.isoformat(),
            "output_hash": self.output_hash,
            "document_id": self.document_id,
            "author": self.author,
            "language": self.language,
            "content_type": self.content_type,
            "parser_version": self.parser_version,
            "parser_hash": self.parser_hash,
        }

    def with_source_fields(
        self,
        *,
        content_type: str,
        parser_version: str,
        parser_hash: str,
    ) -> "SPLProvenance":
        """Return a copy with v1.1 source-document fields filled in."""
        from dataclasses import replace as _replace
        return _replace(
            self,
            content_type=content_type,
            parser_version=parser_version,
            parser_hash=parser_hash,
        )

    @property
    def is_llm(self) -> bool:
        return self.source == "spl_llm"

    @property
    def is_complete_llm_record(self) -> bool:
        """True iff every mandatory LLM-specific field is populated."""
        if not self.is_llm:
            return False
        return all([
            self.model_name,
            self.model_version,
            self.prompt_hash,
            self.output_hash,
            self.max_tokens > 0,
        ])


def make_llm_provenance(
    *,
    model_name: str,
    model_version: str,
    prompt: str,
    output: str,
    temperature: float,
    max_tokens: int,
    document_id: str = "",
    author: str = "",
    language: str = "",
) -> SPLProvenance:
    """Build an :class:`SPLProvenance` for the LLM backend.

    ``prompt`` and ``output`` are hashed into ``prompt_hash`` /
    ``output_hash`` so the ledger does not store the full text
    bodies. Both hashes are deterministic on the input bytes.
    """
    return SPLProvenance(
        source="spl_llm",
        model_name=model_name,
        model_version=model_version,
        prompt_hash="ph_" + _short_hash(prompt),
        temperature=temperature,
        max_tokens=max_tokens,
        timestamp=datetime.now(timezone.utc),
        output_hash="oh_" + _short_hash(output),
        document_id=document_id,
        author=author,
        language=language,
    )


def make_deterministic_provenance(
    *,
    document_id: str = "",
    author: str = "",
    language: str = "",
) -> SPLProvenance:
    """Build an :class:`SPLProvenance` for the deterministic backend."""
    return SPLProvenance(
        source="spl_deterministic",
        document_id=document_id,
        author=author,
        language=language,
    )


__all__ = [
    "SPLProvenance",
    "make_deterministic_provenance",
    "make_llm_provenance",
]
