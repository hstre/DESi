"""Ontology-probe data model — a probe, never an authority.

An ontology (OpenCyc, WordNet, …) is treated as one MEASUREMENT CHANNEL among others: it offers
structured type / sense / hypernym hints about a term, never a truth. The contract is fixed and
enforced structurally here:

  * ``OntologyHint.may_gate`` is a constant ``False`` — it is not a settable field. No probe output
    can ever authorise a hard router/Layer-9 decision. The router may read a hint only to mark
    ``scope_uncertain`` / ``requires_disambiguation`` (see ``probe.py``); the deterministic gate
    stays the sole authority.
  * A hint is structural metadata, never evidence. It carries its own ``source`` (e.g.
    ``wordnet`` / ``opencyc_2012_owl``) and must never be laundered into the claim graph as a fact —
    the same epistemic boundary patient-generated input has.
  * Confidence is ``weak`` or ``none`` only. A probe never claims ``strong``.

Adapters are archival/offline by contract: no network in any hard path. An unavailable corpus
degrades to an empty hint (``status='unavailable'``), it never raises into the caller.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

# hint lifecycle status — all are "probe only"; none ever gates.
PROBE_ONLY = "probe_only"        # senses found; a usable typing hint
UNKNOWN_TERM = "unknown_term"    # the corpus was queried but holds no sense for this term
UNAVAILABLE = "unavailable"      # no corpus/adapter configured, or it failed to load (fail-open)

# confidence is deliberately capped — a probe is never authoritative.
WEAK, NONE = "weak", "none"


@dataclass(frozen=True)
class Sense:
    """One candidate sense of a term. ``type_path`` runs general -> specific, so ``type_path[0]`` is
    the most general type (the 'kind' used for compatibility checks)."""
    sense: str
    type_path: tuple[str, ...] = ()
    confidence: str = WEAK

    def __post_init__(self) -> None:
        if self.confidence not in (WEAK, NONE):
            # structural cap: a probe sense may never be 'strong'/'certain'.
            object.__setattr__(self, "confidence", WEAK)


@dataclass(frozen=True)
class OntologyHint:
    """A read-only typing hint for one term. ``may_gate`` is a constant property, NOT a field — it
    cannot be constructed ``True``, so no hint can ever authorise a hard decision."""
    term: str
    source: str
    candidate_senses: tuple[Sense, ...] = ()
    status: str = PROBE_ONLY
    note: str = ""
    _reserved: tuple = field(default=(), repr=False, compare=False)

    @property
    def may_gate(self) -> bool:
        return False

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "term": self.term,
            "candidate_senses": [
                {"sense": s.sense, "type_path": list(s.type_path), "confidence": s.confidence}
                for s in self.candidate_senses
            ],
            "status": self.status,
            "may_gate": self.may_gate,
        }


@runtime_checkable
class OntologyAdapter(Protocol):
    """A pluggable corpus backend. ``senses(term)`` returns the candidate senses (possibly empty);
    it may raise if the corpus is unavailable — the probe catches that and degrades, fail-open."""

    source: str

    def senses(self, term: str) -> tuple[Sense, ...]:
        ...
