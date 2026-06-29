"""The ontology probe + its deterministic, SEPARATE-ONLY consumer rules.

The probe runs a (pluggable, fail-open) adapter and returns an :class:`OntologyHint`. The consumer
rules turn a hint into router-facing signals — and they are deliberately ASYMMETRIC:

    An ontology hint may only SEPARATE scopes (mark them uncertain / distinct), never ASSERT that two
    claims share a scope, are the same subject, or are in genuine conflict.

That asymmetry is what makes the channel safe. ``scope_uncertain`` can only ever *withhold* a
``same_scope`` / supersession flag (reducing over-fire — the exact failure #5 showed on real data);
it can never *add* a flag. So in the worst case a wrong ontology hint makes the router slightly more
cautious (asks to disambiguate), never wrongly confident. No knowledge ⇒ no separation: an empty or
unavailable hint asserts nothing. Deterministic, no LLM, replay-stable.
"""
from __future__ import annotations

from desi_router.ontology_probe.base import (
    PROBE_ONLY,
    UNAVAILABLE,
    UNKNOWN_TERM,
    OntologyAdapter,
    OntologyHint,
    Sense,
)


def top_type(s: Sense) -> str:
    return s.type_path[0] if s.type_path else ""


def top_types(h: OntologyHint) -> frozenset[str]:
    """The distinct most-general types across a hint's senses (the 'kinds' it might be)."""
    return frozenset(top_type(s) for s in h.candidate_senses if s.type_path)


def requires_disambiguation(h: OntologyHint) -> bool:
    """The term itself is polysemous across KINDS (e.g. 'operator' = math object vs. person). Marks
    the term as ambiguous; never gates."""
    return len(top_types(h)) > 1


def type_incompatible(a: OntologyHint, b: OntologyHint) -> bool:
    """The ontology POSITIVELY suggests two terms are different kinds: both carry typed senses and
    their top-type sets are disjoint. Conservative — if either side is empty/unknown, or any kind is
    shared, this is False. Absence of knowledge never asserts separation."""
    ta, tb = top_types(a), top_types(b)
    if not ta or not tb:
        return False
    return ta.isdisjoint(tb)


def scope_uncertain(a: OntologyHint, b: OntologyHint) -> bool:
    """The single SAFE, separate-only signal the router may consume: are these two terms' scopes
    uncertain enough that a ``same_scope`` / supersession flag should be WITHHELD? True iff the
    ontology suggests different kinds, or either term is itself ambiguous across kinds. It never
    asserts sameness — same-kind terms return False (the probe stays silent and the router's own
    deterministic scope/subject logic decides), so this can only ever reduce a flag, never add one."""
    return type_incompatible(a, b) or requires_disambiguation(a) or requires_disambiguation(b)


class OntologyProbe:
    """Runs a pluggable corpus adapter, fail-open. With no adapter, or on any adapter error, every
    probe returns an ``unavailable`` hint — the channel simply goes silent, the router is unchanged."""

    def __init__(self, adapter: OntologyAdapter | None = None) -> None:
        self._adapter = adapter

    @property
    def source(self) -> str:
        return getattr(self._adapter, "source", UNAVAILABLE) if self._adapter else UNAVAILABLE

    def probe(self, term: str) -> OntologyHint:
        if self._adapter is None:
            return OntologyHint(term=term or "", source=UNAVAILABLE, status=UNAVAILABLE,
                                note="no ontology adapter configured")
        try:
            senses = tuple(self._adapter.senses(term))
        except Exception as exc:  # noqa: BLE001 — fail-open by contract; the channel never raises
            return OntologyHint(term=term or "", source=self.source, status=UNAVAILABLE,
                                note=f"adapter unavailable: {type(exc).__name__}")
        if not senses:
            return OntologyHint(term=term or "", source=self.source, status=UNKNOWN_TERM)
        return OntologyHint(term=term or "", source=self.source, candidate_senses=senses,
                            status=PROBE_ONLY)
