"""Targeted tests for the corrected-FEVER true-solver-failure extraction/classification."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "benchmarks" / "hf_answering"))

from fever_true_failures import (  # noqa: E402
    DIRECTIONS, MECHANISMS, direction, is_true_failure_candidate, mechanism,
)


def test_label_sets():
    assert set(DIRECTIONS) == {"FALSE_NEI", "FALSE_SUPPORT", "FALSE_REFUTE"}
    assert len(MECHANISMS) == 7 and "ENTITY_ROLE_CONFUSION" in MECHANISMS


def test_candidate_filter_high_precision():
    # retained: not empty, band high, gold determinate
    assert is_true_failure_candidate(False, "high", "SUPPORTS") is True
    assert is_true_failure_candidate(False, "high", "REFUTES") is True
    # excluded: empty evidence
    assert is_true_failure_candidate(True, "high", "SUPPORTS") is False
    # excluded: gold NEI (questionable label, not a solver miss)
    assert is_true_failure_candidate(False, "high", "NOT_ENOUGH_INFO") is False
    # excluded: partial / low overlap (underdetermined / ambiguity)
    assert is_true_failure_candidate(False, "partial", "SUPPORTS") is False
    assert is_true_failure_candidate(False, "low", "REFUTES") is False


def test_direction_false_nei():
    assert direction("SUPPORTS", ["NOT_ENOUGH_INFO", "NOT_ENOUGH_INFO"]) == "FALSE_NEI"
    assert direction("REFUTES", ["NOT_ENOUGH_INFO"]) == "FALSE_NEI"


def test_direction_false_support_and_refute():
    assert direction("REFUTES", ["SUPPORTS", "SUPPORTS"]) == "FALSE_SUPPORT"
    assert direction("SUPPORTS", ["REFUTES"]) == "FALSE_REFUTE"


def test_mechanism_role():
    assert mechanism("The film was reviewed by Ron Underwood.",
                     "The film was directed by Ron Underwood.") == "ENTITY_ROLE_CONFUSION"


def test_mechanism_temporal():
    # claim cites a year the evidence does not match -> temporal mechanism
    assert mechanism("The album was released in 1971.",
                     "The album was released in 1968 and reissued in 1969.") == "TEMPORAL_REASONING_FAILURE"


def test_mechanism_numeric():
    assert mechanism("The tower has 50 floors.", "The tower has 30 floors.") == "NUMERIC_BOUND_FAILURE"


def test_mechanism_negation():
    assert mechanism("The treaty was not signed.", "The treaty was signed by both nations.") == "NEGATION_FAILURE"


def test_mechanism_distractor_default():
    # no role/temporal/numeric/negation signal, evidence lexically near -> distractor
    assert mechanism("Tool has won three Oscars.",
                     "Tool has won three Grammy Awards and toured worldwide.") == "DISTRACTOR_SALIENCE"
