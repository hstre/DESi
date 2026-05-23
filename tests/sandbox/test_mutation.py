"""Tests for v2.0 single-knob mutation (Aufgabe 2)."""
from __future__ import annotations

import pytest

from desi.sandbox import (
    BASELINE_VALUE,
    DELTA,
    MAX_VALUE,
    MIN_VALUE,
    MUTABLE_PARAMETER,
    MutationProposal,
)


def test_only_one_mutable_parameter_name() -> None:
    assert MUTABLE_PARAMETER == "branch_open_evidence_min"


def test_baseline_is_v07_production_value() -> None:
    assert BASELINE_VALUE == 0.45


def test_mutated_parameters_length_is_exactly_one() -> None:
    """Hard invariant of Aufgabe 2."""
    p = MutationProposal.build(
        step_id=1, parent_hash="abc", parent_value=0.45,
    )
    assert len(p.mutated_parameters) == 1


def test_mutated_parameters_lists_only_the_allowed_knob() -> None:
    p = MutationProposal.build(
        step_id=7, parent_hash="def", parent_value=0.45,
    )
    assert p.mutated_parameters == (MUTABLE_PARAMETER,)


def test_delta_is_plus_or_minus_two_hundredths() -> None:
    """Forbidden direction: anything other than ±DELTA (modulo clamp)."""
    p = MutationProposal.build(
        step_id=3, parent_hash="abc", parent_value=0.45,
    )
    assert p.proposed_value in (
        round(0.45 + DELTA, 6),
        round(0.45 - DELTA, 6),
    )


def test_direction_is_either_plus_or_minus_one() -> None:
    p = MutationProposal.build(
        step_id=2, parent_hash="abc", parent_value=0.45,
    )
    assert p.direction in (+1, -1)


def test_two_builds_with_identical_inputs_are_identical() -> None:
    a = MutationProposal.build(
        step_id=5, parent_hash="parent_x", parent_value=0.45,
    )
    b = MutationProposal.build(
        step_id=5, parent_hash="parent_x", parent_value=0.45,
    )
    assert a.proposed_value == b.proposed_value
    assert a.direction == b.direction


def test_different_step_ids_produce_independent_directions() -> None:
    seen = set()
    for step_id in range(1, 31):
        p = MutationProposal.build(
            step_id=step_id, parent_hash="parent", parent_value=0.45,
        )
        seen.add(p.direction)
    # Across 30 steps both directions must appear.
    assert seen == {-1, +1}


def test_lower_bound_clamps_at_min_value() -> None:
    """Parent at MIN_VALUE — a -1 step must clamp, not undershoot."""
    # Force direction=-1 by picking a parent_hash known to hit even byte 1.
    # Easier: just check that clamping is in place regardless of direction.
    p_lo = MutationProposal.build(
        step_id=999, parent_hash="seed_clamp_lo", parent_value=MIN_VALUE,
    )
    assert MIN_VALUE <= p_lo.proposed_value <= MAX_VALUE
    if p_lo.direction == -1:
        assert p_lo.proposed_value == MIN_VALUE
        assert p_lo.clamped is True


def test_upper_bound_clamps_at_max_value() -> None:
    p_hi = MutationProposal.build(
        step_id=1000, parent_hash="seed_clamp_hi", parent_value=MAX_VALUE,
    )
    assert MIN_VALUE <= p_hi.proposed_value <= MAX_VALUE
    if p_hi.direction == +1:
        assert p_hi.proposed_value == MAX_VALUE
        assert p_hi.clamped is True


def test_forbidden_parameter_name_rejected() -> None:
    """Construction with a different parameter must error."""
    with pytest.raises(ValueError):
        MutationProposal(
            step_id=1, parent_hash="x", parameter="some_other_knob",
            parent_value=0.45, proposed_value=0.47, delta_applied=0.02,
            direction=+1, clamped=False,
            mutated_parameters=("some_other_knob",),
        )


def test_two_parameters_rejected_by_single_knob_invariant() -> None:
    with pytest.raises(ValueError):
        MutationProposal(
            step_id=1, parent_hash="x", parameter=MUTABLE_PARAMETER,
            parent_value=0.45, proposed_value=0.47, delta_applied=0.02,
            direction=+1, clamped=False,
            mutated_parameters=(MUTABLE_PARAMETER, "another"),
        )


def test_zero_parameters_rejected_by_single_knob_invariant() -> None:
    with pytest.raises(ValueError):
        MutationProposal(
            step_id=1, parent_hash="x", parameter=MUTABLE_PARAMETER,
            parent_value=0.45, proposed_value=0.47, delta_applied=0.02,
            direction=+1, clamped=False, mutated_parameters=(),
        )


def test_to_dict_round_trip_shape() -> None:
    p = MutationProposal.build(
        step_id=10, parent_hash="abc", parent_value=0.45,
    )
    d = p.to_dict()
    for k in (
        "step_id", "parent_hash", "parameter",
        "parent_value", "proposed_value", "delta_applied",
        "direction", "clamped", "mutated_parameters",
    ):
        assert k in d
    assert d["mutated_parameters"] == [MUTABLE_PARAMETER]
