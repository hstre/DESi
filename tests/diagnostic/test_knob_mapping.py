"""Tests for v2.1 candidate-knob mapping (Aufgabe 7)."""
from __future__ import annotations

import pytest

from desi.diagnostic import (
    DEFAULT_INVENTORY,
    DeficitCategory,
    DeficitRecord,
    EMPIRICALLY_DEAD_KNOBS,
    EXISTING_KNOBS,
)


def test_existing_knobs_is_a_frozenset_of_strings() -> None:
    assert isinstance(EXISTING_KNOBS, frozenset)
    for k in EXISTING_KNOBS:
        assert isinstance(k, str)


def test_empirically_dead_subset_of_existing() -> None:
    assert EMPIRICALLY_DEAD_KNOBS <= EXISTING_KNOBS


def test_branch_open_evidence_min_is_dead() -> None:
    """v2.0 empirically proved this knob is decoupled."""
    assert "branch_open_evidence_min" in EMPIRICALLY_DEAD_KNOBS


def test_recursive_resolver_max_depth_is_known() -> None:
    assert "RecursiveResolver.max_depth" in EXISTING_KNOBS


def test_tool_gate_constants_are_known() -> None:
    assert "ToolGate.HARD_TIMEOUT_SECONDS" in EXISTING_KNOBS
    assert "ToolGate.MAX_INPUT_BYTES" in EXISTING_KNOBS


def test_forbidden_phrases_are_not_knobs() -> None:
    """The directive forbade 'new operator', 'new model', 'more data',
    'bigger llm' — they must never appear as knobs."""
    for forbidden in (
        "new operator", "new model", "more data", "bigger llm",
        "more compute", "bigger context",
    ):
        assert forbidden not in EXISTING_KNOBS


def test_deficit_record_refuses_unknown_knob() -> None:
    with pytest.raises(ValueError):
        DeficitRecord.build(
            category=DeficitCategory.UNKNOWN,
            source_module="x", source_case_ids=(),
            frequency=0, severity_score=0.0, confidence_score=0.0,
            is_actionable=False,
            candidate_knobs=("more data",),
            rationale="should fail",
        )


def test_candidate_knobs_subset_of_existing_parameters() -> None:
    """Hard invariant of Aufgabe 7."""
    rec = DeficitRecord.build(
        category=DeficitCategory.RECURSION_CONFIGURATION,
        source_module="desi.recursive", source_case_ids=("c1",),
        frequency=1, severity_score=0.5, confidence_score=0.5,
        is_actionable=True,
        candidate_knobs=("RecursiveResolver.max_depth",),
        rationale="ok",
    )
    assert set(rec.candidate_knobs) <= EXISTING_KNOBS


def test_default_inventory_live_dead_partition() -> None:
    live = DEFAULT_INVENTORY.live_knobs()
    dead = DEFAULT_INVENTORY.dead_knobs()
    assert live & dead == set()
    assert live | dead == EXISTING_KNOBS
