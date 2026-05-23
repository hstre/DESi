"""Tests for DeterministicSemanticBackend — reproducible, no APIs."""
from __future__ import annotations

from desi.spl_adapter import (
    DeterministicSemanticBackend,
    SemanticUnit,
)


def _backend() -> DeterministicSemanticBackend:
    return DeterministicSemanticBackend()


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_same_text_yields_same_units() -> None:
    b = _backend()
    a_units = b.extract_units("Water boils at 100C.")
    b_units = b.extract_units("Water boils at 100C.")
    assert a_units == b_units


def test_units_do_not_depend_on_call_order() -> None:
    b1 = _backend()
    b2 = _backend()
    b1.extract_units("Random other text first.")
    b1.extract_units("Water boils at 100C.")
    direct = b2.extract_units("Water boils at 100C.")
    indirect = b1.extract_units("Water boils at 100C.")
    assert direct == indirect


def test_method_label_is_deterministic_semantic_projection() -> None:
    assert _backend().method_label == "deterministic_semantic_projection"


# ---------------------------------------------------------------------------
# Paraphrase canonicalisation (P1 base case)
# ---------------------------------------------------------------------------


def test_two_paraphrases_map_to_the_same_canonical() -> None:
    b = _backend()
    a = b.extract_units("Water boils at 100C.")
    c = b.extract_units(
        "At one atmosphere water reaches boiling point at 100 degrees."
    )
    assert a[0].canonical_content == c[0].canonical_content


def test_canonical_includes_temperature_value() -> None:
    units = _backend().extract_units("Water boils at 100C.")
    assert "100" in units[0].canonical_content


# ---------------------------------------------------------------------------
# Ambiguity flag (P3 base case)
# ---------------------------------------------------------------------------


def test_hedged_text_is_flagged_ambiguous() -> None:
    units = _backend().extract_units(
        "Water might possibly boil somewhere around 100 degrees."
    )
    assert len(units) == 1
    assert units[0].ambiguous is True
    assert units[0].confidence < 0.5


def test_non_hedged_text_is_not_flagged_ambiguous() -> None:
    units = _backend().extract_units("Water boils at 100C.")
    assert units[0].ambiguous is False


# ---------------------------------------------------------------------------
# Backend never proposes relations
# ---------------------------------------------------------------------------


def test_deterministic_backend_never_proposes_relations() -> None:
    units = _backend().extract_units("Water boils at 100C.")
    assert units[0].proposed_relations == ()


# ---------------------------------------------------------------------------
# Empty / unparseable inputs
# ---------------------------------------------------------------------------


def test_empty_text_yields_no_units() -> None:
    assert _backend().extract_units("") == ()


def test_unrelated_non_ambiguous_text_yields_no_units() -> None:
    """Text the phrase library does not recognise produces nothing.
    The backend stays silent rather than hallucinate a canonical."""
    assert _backend().extract_units("The cat sat on the mat.") == ()
