"""Ontology Probe — a non-authoritative type/scope measurement channel for the router pipeline.

Shape (mirrors CLSP): the adapter + probe PRODUCE structured hints; the deterministic, separate-only
consumer rules turn them into ``scope_uncertain`` / ``requires_disambiguation`` signals; the router
consumes only finished fields and the Layer-9 gate stays the sole authority. Ontologies type and flag
ambiguity — they never confirm truth, sameness, or conflict. ``may_gate`` is always ``False``.
"""
from desi_router.ontology_probe.base import (
    NONE,
    PROBE_ONLY,
    UNAVAILABLE,
    UNKNOWN_TERM,
    WEAK,
    OntologyAdapter,
    OntologyHint,
    Sense,
)
from desi_router.ontology_probe.probe import (
    OntologyProbe,
    requires_disambiguation,
    scope_uncertain,
    top_type,
    top_types,
    type_incompatible,
)
from desi_router.ontology_probe.static_adapter import StaticOntologyAdapter
from desi_router.ontology_probe.wordnet_adapter import OntologyUnavailable, WordNetAdapter

__all__ = [
    "OntologyHint", "Sense", "OntologyAdapter",
    "PROBE_ONLY", "UNKNOWN_TERM", "UNAVAILABLE", "WEAK", "NONE",
    "OntologyProbe", "top_type", "top_types", "requires_disambiguation",
    "type_incompatible", "scope_uncertain",
    "StaticOntologyAdapter", "WordNetAdapter", "OntologyUnavailable",
]
