"""Tests for v1.2 PremiseExtractor — typed extraction, deterministic ids."""
from __future__ import annotations

import pytest

from desi.logic import (
    PremiseExtractor,
    PremiseKind,
)


def _ext() -> PremiseExtractor:
    return PremiseExtractor()


# ---------------------------------------------------------------------------
# Universal premises
# ---------------------------------------------------------------------------


def test_universal_premise_recognised() -> None:
    props = _ext().extract("All men are mortal.")
    assert len(props.premises) == 1
    p = props.premises[0]
    assert p.kind == PremiseKind.UNIVERSAL
    assert p.subject == "man"          # inflection normalised
    assert p.predicate == "mortal"


def test_universal_premise_id_is_deterministic() -> None:
    a = _ext().extract("All men are mortal.").premises[0]
    b = _ext().extract("All men are mortal.").premises[0]
    assert a.premise_id == b.premise_id


# ---------------------------------------------------------------------------
# Particular premises
# ---------------------------------------------------------------------------


def test_particular_premise_with_article() -> None:
    p = _ext().extract("Socrates is a man.").premises[0]
    assert p.kind == PremiseKind.PARTICULAR
    assert p.subject == "socrates"
    assert p.predicate == "man"


def test_particular_premise_without_article() -> None:
    p = _ext().extract("Socrates is mortal.").premises[0]
    assert p.kind == PremiseKind.PARTICULAR
    assert p.subject == "socrates"
    assert p.predicate == "mortal"


# ---------------------------------------------------------------------------
# Conditional / implication
# ---------------------------------------------------------------------------


def test_conditional_premise() -> None:
    p = _ext().extract("If it rains then the street is wet.").premises[0]
    assert p.kind == PremiseKind.CONDITIONAL
    assert p.antecedent == "it rains"
    assert p.consequent == "the street is wet"


def test_implication_premise_arrow() -> None:
    p = _ext().extract("a -> b").premises[0]
    assert p.kind == PremiseKind.IMPLICATION
    assert p.antecedent == "a"
    assert p.consequent == "b"


# ---------------------------------------------------------------------------
# Authority premises
# ---------------------------------------------------------------------------


def test_authority_premise() -> None:
    p = _ext().extract("Professor X says quantum gravity is solved.").premises[0]
    assert p.kind == PremiseKind.AUTHORITY
    assert "professor x" in p.speaker
    assert "quantum gravity is solved" in p.predicate


# ---------------------------------------------------------------------------
# Therefore-split
# ---------------------------------------------------------------------------


def test_therefore_splits_premises_from_conclusion() -> None:
    props = _ext().extract(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is mortal."
    )
    assert props.has_explicit_chain
    assert len(props.premises) == 2
    assert props.conclusion is not None
    assert props.conclusion.kind == PremiseKind.PARTICULAR


def test_no_therefore_means_no_explicit_chain() -> None:
    props = _ext().extract("All men are mortal. Socrates is a man.")
    assert not props.has_explicit_chain
    assert props.conclusion is None
    assert len(props.premises) == 2


# ---------------------------------------------------------------------------
# Inflection normalisation
# ---------------------------------------------------------------------------


def test_men_and_man_canonicalise_to_same_token() -> None:
    p1 = _ext().extract("All men are mortal.").premises[0]
    p2 = _ext().extract("Socrates is a man.").premises[0]
    assert p1.subject == p2.predicate == "man"


# ---------------------------------------------------------------------------
# Empty / non-string input
# ---------------------------------------------------------------------------


def test_empty_text_yields_empty_propositions() -> None:
    props = _ext().extract("")
    assert props.premises == ()
    assert props.conclusion is None


def test_non_str_input_raises() -> None:
    with pytest.raises(TypeError):
        _ext().extract(42)  # type: ignore
