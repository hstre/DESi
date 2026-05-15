"""Tests for v2.2 depth mutation (Aufgabe 2)."""
from __future__ import annotations

import pytest

from desi.sandbox import (
    DEFAULT_START_DEPTH,
    DEPTH_MAX,
    DEPTH_MIN,
    DepthMutationProposal,
)
from desi.sandbox.depth_mutation import MUTABLE_PARAMETER


def test_default_start_depth_is_three() -> None:
    assert DEFAULT_START_DEPTH == 3


def test_depth_range_is_one_to_six() -> None:
    assert DEPTH_MIN == 1
    assert DEPTH_MAX == 6


def test_only_one_mutable_parameter() -> None:
    assert MUTABLE_PARAMETER == "RecursiveResolver.max_depth"


def test_single_knob_invariant() -> None:
    p = DepthMutationProposal.build(
        step_id=1, parent_hash="abc", parent_depth=3,
    )
    assert len(p.mutated_parameters) == 1
    assert p.mutated_parameters == (MUTABLE_PARAMETER,)


def test_step_changes_by_exactly_one() -> None:
    """Hard invariant: abs(new - old) <= 1."""
    for step in range(1, 31):
        p = DepthMutationProposal.build(
            step_id=step, parent_hash="parent_a", parent_depth=3,
        )
        assert abs(p.proposed_depth - p.parent_depth) <= 1


def test_proposed_depth_in_legal_range() -> None:
    for step in range(1, 31):
        for parent in range(DEPTH_MIN, DEPTH_MAX + 1):
            p = DepthMutationProposal.build(
                step_id=step, parent_hash="x", parent_depth=parent,
            )
            assert DEPTH_MIN <= p.proposed_depth <= DEPTH_MAX


def test_lower_bound_clamps() -> None:
    """At depth=1, a -1 direction clamps to 1."""
    p = DepthMutationProposal.build(
        step_id=99, parent_hash="seed_lo", parent_depth=DEPTH_MIN,
    )
    assert p.proposed_depth >= DEPTH_MIN
    if p.direction == -1:
        assert p.proposed_depth == DEPTH_MIN
        assert p.clamped is True


def test_upper_bound_clamps() -> None:
    p = DepthMutationProposal.build(
        step_id=99, parent_hash="seed_hi", parent_depth=DEPTH_MAX,
    )
    assert p.proposed_depth <= DEPTH_MAX
    if p.direction == +1:
        assert p.proposed_depth == DEPTH_MAX
        assert p.clamped is True


def test_two_builds_with_identical_inputs_are_identical() -> None:
    a = DepthMutationProposal.build(
        step_id=7, parent_hash="zz", parent_depth=4,
    )
    b = DepthMutationProposal.build(
        step_id=7, parent_hash="zz", parent_depth=4,
    )
    assert a.proposed_depth == b.proposed_depth
    assert a.direction == b.direction


def test_jump_greater_than_one_rejected() -> None:
    """Constructing a proposal manually with a 2-step jump fails."""
    with pytest.raises(ValueError):
        DepthMutationProposal(
            step_id=1, parent_hash="x", parameter=MUTABLE_PARAMETER,
            parent_depth=3, proposed_depth=5,   # +2 jump
            direction=+1, clamped=False,
            mutated_parameters=(MUTABLE_PARAMETER,),
        )


def test_zero_step_difference_allowed_only_via_clamp() -> None:
    """At MIN -1 (clamp) the proposed equals parent; that's fine."""
    p = DepthMutationProposal(
        step_id=1, parent_hash="x", parameter=MUTABLE_PARAMETER,
        parent_depth=DEPTH_MIN, proposed_depth=DEPTH_MIN,
        direction=-1, clamped=True,
        mutated_parameters=(MUTABLE_PARAMETER,),
    )
    assert p.proposed_depth == DEPTH_MIN


def test_unknown_parameter_rejected() -> None:
    with pytest.raises(ValueError):
        DepthMutationProposal(
            step_id=1, parent_hash="x", parameter="some_other_knob",
            parent_depth=3, proposed_depth=4,
            direction=+1, clamped=False,
            mutated_parameters=("some_other_knob",),
        )


def test_out_of_range_parent_rejected() -> None:
    with pytest.raises(ValueError):
        DepthMutationProposal.build(
            step_id=1, parent_hash="x", parent_depth=0,
        )
    with pytest.raises(ValueError):
        DepthMutationProposal.build(
            step_id=1, parent_hash="x", parent_depth=99,
        )


def test_to_dict_carries_all_observables() -> None:
    p = DepthMutationProposal.build(
        step_id=1, parent_hash="x", parent_depth=3,
    )
    d = p.to_dict()
    for k in (
        "step_id", "parent_hash", "parameter",
        "parent_depth", "proposed_depth", "direction",
        "clamped", "mutated_parameters",
    ):
        assert k in d
