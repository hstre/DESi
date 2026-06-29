"""Ontology Probe — the may_gate invariant, fail-open behaviour, and the separate-only consumer rules.

The load-bearing guarantee: a probe can only ever SEPARATE scopes (mark uncertain), never assert
sameness or conflict, and never gate. These tests pin exactly that.
"""
from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from desi_router.ontology_probe import (
    OntologyHint,
    OntologyProbe,
    Sense,
    StaticOntologyAdapter,
    WordNetAdapter,
    requires_disambiguation,
    scope_uncertain,
    type_incompatible,
)
from desi_router.ontology_probe.base import PROBE_ONLY, UNAVAILABLE, UNKNOWN_TERM

# a small deterministic ontology mirroring the proposal's examples
_ONT = StaticOntologyAdapter({
    "operator": (Sense("mathematical_operator", ("abstract", "mathematical_object")),
                 Sense("human_operator", ("person", "worker"))),          # ambiguous across kinds
    "cat": (Sense("feline", ("animal", "organism")),),
    "python": (Sense("software_tool", ("artifact", "program")),),
    "dog": (Sense("canine", ("animal", "organism")),),
    "kernel": (Sense("os_kernel", ("artifact", "software")),
               Sense("seed_kernel", ("plant_part", "seed"))),             # ambiguous across kinds
}, source="static_demo")
_PROBE = OntologyProbe(_ONT)


# --- the hard invariant: a hint can never gate -----------------------------------------------------
def test_hint_may_gate_is_always_false_and_not_settable():
    h = _PROBE.probe("operator")
    assert h.may_gate is False
    # may_gate is a property, not a field -> it cannot be constructed True
    import dataclasses
    assert "may_gate" not in {f.name for f in dataclasses.fields(OntologyHint)}
    assert h.to_dict()["may_gate"] is False


def test_sense_confidence_is_capped_to_weak_never_strong():
    s = Sense("x", ("animal",), confidence="strong")
    assert s.confidence == "weak"                      # a probe sense is never authoritative


# --- fail-open: no corpus / errors degrade to a silent channel, never raise ------------------------
def test_probe_with_no_adapter_is_unavailable_not_an_error():
    h = OntologyProbe(None).probe("operator")
    assert h.status == UNAVAILABLE and h.candidate_senses == ()


def test_probe_swallows_adapter_errors_fail_open():
    class _Boom:
        source = "boom"
        def senses(self, term):
            raise RuntimeError("corpus exploded")
    h = OntologyProbe(_Boom()).probe("operator")
    assert h.status == UNAVAILABLE                     # never propagates the error to the caller


def test_unknown_term_is_distinct_from_unavailable():
    h = _PROBE.probe("nonexistent-term-xyz")
    assert h.status == UNKNOWN_TERM and h.candidate_senses == ()


def test_real_wordnet_adapter_is_fail_open_when_corpus_absent():
    # neither nltk nor wn corpus is installed here -> the channel goes silent, it does not raise
    h = OntologyProbe(WordNetAdapter()).probe("operator")
    assert h.status in (UNAVAILABLE, PROBE_ONLY)       # unavailable here; PROBE_ONLY if a corpus exists


# --- the separate-only consumer rules --------------------------------------------------------------
def test_polysemous_term_requires_disambiguation():
    assert requires_disambiguation(_PROBE.probe("operator")) is True   # math vs person
    assert requires_disambiguation(_PROBE.probe("cat")) is False        # single kind


def test_disjoint_kinds_are_type_incompatible():
    assert type_incompatible(_PROBE.probe("cat"), _PROBE.probe("python")) is True   # animal vs artifact
    assert type_incompatible(_PROBE.probe("cat"), _PROBE.probe("dog")) is False     # both animal


def test_absence_of_knowledge_never_asserts_separation():
    unknown = _PROBE.probe("nonexistent-term-xyz")
    assert type_incompatible(unknown, _PROBE.probe("cat")) is False
    assert type_incompatible(OntologyProbe(None).probe("a"), OntologyProbe(None).probe("b")) is False


def test_scope_uncertain_is_separate_only_never_asserts_sameness():
    # different kinds -> uncertain (separate); same kind -> NOT asserted same, just silent (False)
    assert scope_uncertain(_PROBE.probe("cat"), _PROBE.probe("python")) is True
    assert scope_uncertain(_PROBE.probe("cat"), _PROBE.probe("dog")) is False
    # an ambiguous term alone makes the pair uncertain
    assert scope_uncertain(_PROBE.probe("kernel"), _PROBE.probe("cat")) is True


# --- properties: the rules are symmetric and monotone (Hypothesis) ---------------------------------
_KIND = st.sampled_from(["animal", "artifact", "person", "abstract", "process", "plant_part"])
_HINTS = st.builds(
    lambda kinds: OntologyHint("t", "static",
                               tuple(Sense(f"s{i}", (k,)) for i, k in enumerate(kinds))),
    st.lists(_KIND, max_size=4))


@given(_HINTS, _HINTS)
def test_type_incompatible_is_symmetric(a, b):
    assert type_incompatible(a, b) == type_incompatible(b, a)


@given(_HINTS, _HINTS)
def test_incompatible_implies_scope_uncertain(a, b):
    # separation is a sufficient condition for uncertainty (never the other way into 'same')
    if type_incompatible(a, b):
        assert scope_uncertain(a, b) is True


@given(_HINTS)
def test_scope_uncertain_of_same_hint_only_when_self_ambiguous(h):
    # a hint vs itself can never be 'type_incompatible' (kinds are identical); uncertainty then comes
    # ONLY from the term being ambiguous across kinds — never an assertion that it differs from itself
    assert type_incompatible(h, h) is False
    assert scope_uncertain(h, h) == requires_disambiguation(h)
