"""v1.7 negation support — narrow extension of the premise extractor.

The 9 directive-listed negation forms must all parse as PARTICULAR
with the predicate canonicalised to "not <pred>" so the existing
contradiction logic and inflection table keep working uniformly.
"""
from __future__ import annotations

import pytest

from desi.logic import PremiseExtractor, PremiseKind


@pytest.mark.parametrize("text, subj, pred", [
    # BE-verb negation
    ("The car is not running.", "the car", "not running"),
    ("The lights are not on.", "the lights", "not on"),
    ("He was not at home.", "he", "not at home"),
    ("They were not invited.", "they", "not invited"),
    # Auxiliary negation
    ("She did not study.", "she", "not study"),
    ("He does not drive.", "he", "not drive"),
    ("They do not agree.", "they", "not agree"),
    ("The engine will not start.", "the engine", "not start"),
    # Cannot
    ("The plant cannot photosynthesise.", "the plant",
     "not photosynthesise"),
    ("She can not swim.", "she", "not swim"),
])
def test_negation_parses_as_particular_with_not_prefix(
    text, subj, pred,
) -> None:
    props = PremiseExtractor().extract(text)
    assert len(props.premises) == 1
    p = props.premises[0]
    assert p.kind is PremiseKind.PARTICULAR, (
        f"text {text!r} parsed as {p.kind.value}, not PARTICULAR"
    )
    assert p.subject == subj, f"subject mismatch on {text!r}"
    assert p.predicate == pred, f"predicate mismatch on {text!r}"


# ---------------------------------------------------------------------------
# Universal-conclusion syllogism
# ---------------------------------------------------------------------------


def test_universal_conclusion_syllogism_audits_as_supported() -> None:
    """Aufgabe 3: All A are B. All B are C. Therefore all A are C."""
    from desi.logic import InferenceRule, LogicalAuditor, LogicalState
    r = LogicalAuditor().audit(
        "All A are B. All B are C. Therefore all A are C."
    )
    assert r.state is LogicalState.LOGICALLY_SUPPORTED
    assert r.rule is InferenceRule.SYLLOGISM


def test_universal_conclusion_uses_two_universal_premises() -> None:
    from desi.logic import LogicalAuditor
    r = LogicalAuditor().audit(
        "All A are B. All B are C. Therefore all A are C."
    )
    assert r.proof_chain is not None
    assert len(r.proof_chain.premise_ids) == 2


def test_universal_conclusion_rejects_non_chaining_premises() -> None:
    """Middle term must match: All A are B + All X are C → no match."""
    from desi.logic import LogicalAuditor, LogicalState
    r = LogicalAuditor().audit(
        "All A are B. All X are C. Therefore all A are C."
    )
    assert r.state is not LogicalState.LOGICALLY_SUPPORTED


# ---------------------------------------------------------------------------
# v1.7 directive examples
# ---------------------------------------------------------------------------


def test_engine_will_not_start_parses_as_negation_particular() -> None:
    """Directive example: 'The engine will not start.'"""
    p = PremiseExtractor().extract("The engine will not start.").premises[0]
    assert p.kind is PremiseKind.PARTICULAR
    assert p.predicate.startswith("not ")


def test_he_did_not_study_parses_as_negation_particular() -> None:
    """Directive example: 'He did not study.'"""
    p = PremiseExtractor().extract("He did not study.").premises[0]
    assert p.kind is PremiseKind.PARTICULAR
    assert p.predicate.startswith("not ")


def test_plant_is_not_watered_parses_as_negation_particular() -> None:
    """Directive example: 'The plant is not watered.'"""
    p = PremiseExtractor().extract("The plant is not watered.").premises[0]
    assert p.kind is PremiseKind.PARTICULAR
    assert p.predicate.startswith("not ")
