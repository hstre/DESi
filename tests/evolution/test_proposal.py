"""Tests for MutationProposal."""
from __future__ import annotations

import json

import pytest

from desi.evolution import MutationProposal, MutationTarget


def _valid(**overrides) -> MutationProposal:
    base = dict(
        parent_version="stable-v0.5.0",
        problem="too many branches",
        hypothesis="raise branch-evidence min",
        target=MutationTarget.BRANCH_HEURISTICS,
        config_delta={"guard_thresholds.branch_open_evidence_min": 0.45},
        expected_improvement="fewer branches on S5 by 30%",
        rollback_conditions=("revert if S2 branch_opened < 1",),
    )
    base.update(overrides)
    return MutationProposal(**base)


def test_proposal_assigns_a_mutation_id() -> None:
    p = _valid()
    assert p.mutation_id.startswith("mut_")
    assert len(p.mutation_id) == len("mut_") + 12


def test_proposal_rejects_empty_rollback_conditions() -> None:
    with pytest.raises(Exception):
        _valid(rollback_conditions=())


def test_proposal_rejects_empty_problem_or_hypothesis() -> None:
    with pytest.raises(Exception):
        _valid(problem="")
    with pytest.raises(Exception):
        _valid(hypothesis="")


def test_proposal_serialises_and_round_trips() -> None:
    original = _valid()
    serialised = original.serialise()
    # Must be JSON-clean: the dict survives a JSON round-trip.
    rebuilt_dict = json.loads(json.dumps(serialised))
    rebuilt = MutationProposal.from_record(rebuilt_dict)
    assert rebuilt.mutation_id == original.mutation_id
    assert rebuilt.target is original.target
    assert rebuilt.config_delta == original.config_delta
    assert rebuilt.rollback_conditions == original.rollback_conditions


def test_proposal_target_is_one_of_the_five_v0_5_targets() -> None:
    assert {t.value for t in MutationTarget} == {
        "guard_thresholds", "branch_heuristics", "merge_policy",
        "operator_ordering", "diagnostics",
    }


def test_proposal_extra_fields_are_rejected() -> None:
    with pytest.raises(Exception):
        _valid(secret="oops")
