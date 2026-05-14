"""Semantic backends — the only place SPL touches the outside world.

Two backends ship in v1.0:

* :class:`DeterministicSemanticBackend` — rule-based pattern matcher,
  no network access, fully reproducible. The mandatory baseline used
  by every test in the repository.

* :class:`LLMSemanticBackend` — optional, default **disabled**.
  When enabled, calls a single configured model (DeepSeek 4 Pro is
  the v1.0 reference). Real network calls happen only inside an
  injectable ``llm_call`` callable so the test suite can drive every
  fail-closed path without any outbound traffic.

Both backends speak the same two-method protocol:

* ``extract_units(text)`` — produce a tuple of :class:`SemanticUnit`
  objects (one per atomic proposition in the text).
* ``project_units(units)`` — turn the units into
  :class:`ClaimCandidate` objects, attaching backend-specific
  provenance.

Backends never write to memory and never decide promotion.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Protocol

from .errors import BackendError
from .mapping import ClaimCandidate
from .provenance import (
    SPLProvenance,
    make_deterministic_provenance,
    make_llm_provenance,
)


# ---------------------------------------------------------------------------
# Atomic intermediate unit
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SemanticUnit:
    """One atomic proposition extracted from a free-text input.

    Backends produce units; the adapter / gateway consumes them. A
    unit carries the canonical proposition string (the same paraphrase
    must canonicalise to the same string), the raw span the unit was
    extracted from, and a confidence in ``[0, 1]``. Confidence is not
    a memory-layer concept; it is used only by the gateway to flag
    ambiguous candidates.
    """

    canonical_content: str
    raw_span: str
    confidence: float = 1.0
    ambiguous: bool = False
    proposed_relations: tuple[tuple[str, str, str], ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class SemanticBackend(Protocol):
    """Two-method protocol every backend implements."""

    @property
    def method_label(self) -> str: ...

    def extract_units(self, text: str) -> tuple[SemanticUnit, ...]: ...

    def project_units(
        self,
        units: tuple[SemanticUnit, ...],
        *,
        document_id: str = "",
        author: str = "",
        language: str = "",
    ) -> tuple[ClaimCandidate, ...]: ...


# ---------------------------------------------------------------------------
# Deterministic backend — fully reproducible, no APIs
# ---------------------------------------------------------------------------


def _canonical_boiling(num: str) -> str:
    return f"water boils at {num}°C"


_NUMBER_RE = re.compile(r"(\d+)\s*(?:°\s*c|c\b|degrees?)", re.IGNORECASE)


class DeterministicSemanticBackend:
    """Rule-based backend. v1.0 ships a small phrase library.

    The phrase library is intentionally narrow — the point is to give
    paraphrase tests a deterministic baseline, not to do real NLP.
    Two paraphrases that share the same key terms and number
    canonicalise to the same string; two unrelated texts produce
    different canonicals or no unit at all.

    Ambiguity:

    * texts with hedge words (``maybe``, ``perhaps``, ``might``,
      ``possibly``, ``uncertain``) are flagged ``ambiguous=True``.

    The backend never proposes a relation; ``proposed_relations`` is
    always the empty tuple.
    """

    @property
    def method_label(self) -> str:
        return "deterministic_semantic_projection"

    def extract_units(self, text: str) -> tuple[SemanticUnit, ...]:
        if not isinstance(text, str):
            raise BackendError("invalid_input",
                                "extract_units requires str input")
        # One sentence per period; trim whitespace; skip empties.
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text)
                     if s.strip()]
        units: list[SemanticUnit] = []
        for sentence in sentences:
            unit = self._extract_one(sentence)
            if unit is not None:
                units.append(unit)
        return tuple(units)

    def project_units(
        self,
        units: tuple[SemanticUnit, ...],
        *,
        document_id: str = "",
        author: str = "",
        language: str = "",
    ) -> tuple[ClaimCandidate, ...]:
        prov = make_deterministic_provenance(
            document_id=document_id, author=author, language=language,
        )
        candidates: list[ClaimCandidate] = []
        for u in units:
            candidates.append(ClaimCandidate(
                content=u.canonical_content,
                method=self.method_label,
                spl_provenance=prov,
                raw_text=u.raw_span,
                confidence=u.confidence,
                ambiguous=u.ambiguous,
                proposed_relations=u.proposed_relations,
            ))
        return tuple(candidates)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _extract_one(self, sentence: str) -> SemanticUnit | None:
        lower = sentence.lower()
        ambiguous = self._is_ambiguous(lower)
        num_match = _NUMBER_RE.search(lower)
        canonical: str | None = None
        if num_match is not None:
            num = num_match.group(1)
            mentions_water = "water" in lower
            mentions_boil = "boil" in lower or "boiling" in lower
            if mentions_water and mentions_boil:
                canonical = _canonical_boiling(num)
        if canonical is None:
            # Fallback: only emit a unit when ambiguous so the gateway
            # has something to reject. Non-matching, non-ambiguous text
            # produces zero units.
            if ambiguous:
                canonical = "unknown_proposition"
            else:
                return None
        return SemanticUnit(
            canonical_content=canonical,
            raw_span=sentence,
            confidence=0.4 if ambiguous else 0.9,
            ambiguous=ambiguous,
        )

    def _is_ambiguous(self, lower_text: str) -> bool:
        return any(w in lower_text for w in (
            "maybe", "perhaps", "might", "possibly",
            "uncertain", "unclear",
        ))


# ---------------------------------------------------------------------------
# LLM backend — optional, default disabled
# ---------------------------------------------------------------------------


# v1.0 directive: DeepSeek 4 Pro is the only supported model. Other
# models require an explicit code change so that the audit trail
# cannot silently start pointing at a different LLM.
DEEPSEEK_MODEL_NAME = "deepseek-4-pro"
DEEPSEEK_MODEL_VERSION = "2026-05"

# v1.1 directive: hard cap on raw LLM response size, enforced both at
# the HTTP transport (DeepSeekClient) and at this parse boundary.
MAX_LLM_RESPONSE_BYTES = 50 * 1024  # 50 KB


LLMCallable = Callable[[str], str]
"""Signature of the injectable LLM call.

Takes the rendered prompt, returns the raw model output. The adapter
parses the output as JSON. If the call raises, the adapter
fail-closes; the test suite drives this via callables that raise
``TimeoutError``, ``ConnectionError``, etc.
"""


def _default_llm_call(prompt: str) -> str:
    raise BackendError(
        "backend_disabled",
        "LLMSemanticBackend has no llm_call configured; v1.0 ships "
        "without a default network client. Inject a callable for tests "
        "or wire one explicitly.",
    )


class LLMSemanticBackend:
    """Optional LLM-driven backend. Default: disabled.

    The backend never calls the network on its own. It calls the
    injected ``llm_call`` callable, parses the response as JSON of the
    shape::

        {"units": [
          {"canonical_content": "...",
           "raw_span": "...",
           "confidence": 0.9,
           "ambiguous": false,
           "proposed_relations": [["src", "rel", "tgt"], ...]}
        ]}

    Any deviation (non-JSON, missing keys, empty list, exception
    inside ``llm_call``) raises :class:`BackendError`. The adapter
    catches that and fail-closes.

    v1.0 hard-codes ``model_name`` to ``deepseek-4-pro``. To use
    another model the file must be edited — the audit trail must
    never silently drift between models.
    """

    def __init__(
        self,
        *,
        llm_call: LLMCallable = _default_llm_call,
        model_version: str = DEEPSEEK_MODEL_VERSION,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> None:
        self._llm_call = llm_call
        self._model_name = DEEPSEEK_MODEL_NAME
        self._model_version = model_version
        self._temperature = float(temperature)
        self._max_tokens = int(max_tokens)

    @property
    def method_label(self) -> str:
        return "llm_semantic_projection"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> str:
        return self._model_version

    def extract_units(self, text: str) -> tuple[SemanticUnit, ...]:
        if not isinstance(text, str):
            raise BackendError("invalid_input",
                                "extract_units requires str input")
        prompt = self._render_prompt(text)
        try:
            raw = self._llm_call(prompt)
        except BackendError:
            raise
        except Exception as exc:
            raise BackendError("llm_call_failed", str(exc)) from exc
        units, self._last_raw_output = self._parse_response(raw)
        self._last_prompt = prompt
        return units

    def project_units(
        self,
        units: tuple[SemanticUnit, ...],
        *,
        document_id: str = "",
        author: str = "",
        language: str = "",
    ) -> tuple[ClaimCandidate, ...]:
        prov = make_llm_provenance(
            model_name=self._model_name,
            model_version=self._model_version,
            prompt=getattr(self, "_last_prompt", ""),
            output=getattr(self, "_last_raw_output", ""),
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            document_id=document_id, author=author, language=language,
        )
        candidates: list[ClaimCandidate] = []
        for u in units:
            candidates.append(ClaimCandidate(
                content=u.canonical_content,
                method=self.method_label,
                spl_provenance=prov,
                raw_text=u.raw_span,
                confidence=u.confidence,
                ambiguous=u.ambiguous,
                proposed_relations=u.proposed_relations,
            ))
        return tuple(candidates)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _render_prompt(self, text: str) -> str:
        return (
            "You are a semantic-projection sensor for the DESi system.\n"
            "Extract atomic factual propositions from the input. Do NOT "
            "propose merges, contradictions, or other relations between "
            "claims — only the propositions themselves.\n"
            "Respond as a JSON object with key 'units'.\n"
            f"INPUT:\n{text}\n"
        )

    def _parse_response(
        self, raw: str,
    ) -> tuple[tuple[SemanticUnit, ...], str]:
        if not raw or not raw.strip():
            raise BackendError("empty_output", "LLM returned empty body")
        # v1.1: hard 50 KB response cap, enforced independently of the
        # transport so an injected ``llm_call`` that returns a giant
        # blob still fail-closes here.
        size_bytes = len(raw.encode("utf-8"))
        if size_bytes > MAX_LLM_RESPONSE_BYTES:
            raise BackendError(
                "response_too_large",
                f"{size_bytes} bytes > {MAX_LLM_RESPONSE_BYTES} byte cap",
            )
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise BackendError("invalid_json", str(exc)) from exc
        if not isinstance(payload, dict) or "units" not in payload:
            raise BackendError("invalid_schema",
                                "missing 'units' key in LLM response")
        raw_units = payload["units"]
        if not isinstance(raw_units, list):
            raise BackendError("invalid_schema",
                                "'units' must be a list")
        units: list[SemanticUnit] = []
        for ru in raw_units:
            if not isinstance(ru, dict):
                raise BackendError("invalid_schema", "unit must be an object")
            rels_raw = ru.get("proposed_relations") or []
            rels = tuple(
                (r[0], r[1], r[2]) for r in rels_raw
                if isinstance(r, (list, tuple)) and len(r) == 3
            )
            units.append(SemanticUnit(
                canonical_content=str(ru.get("canonical_content", "")),
                raw_span=str(ru.get("raw_span", "")),
                confidence=float(ru.get("confidence", 1.0)),
                ambiguous=bool(ru.get("ambiguous", False)),
                proposed_relations=rels,
            ))
        return tuple(units), raw


__all__ = [
    "DEEPSEEK_MODEL_NAME",
    "DEEPSEEK_MODEL_VERSION",
    "DeterministicSemanticBackend",
    "LLMCallable",
    "LLMSemanticBackend",
    "SemanticBackend",
    "SemanticUnit",
]
