"""Shared fixtures for evolution-layer tests."""
from __future__ import annotations

import pytest

from desi.eval import EvaluationHarness, scenario_by_id
from desi.evolution import (
    CloneSandbox,
    MutationEvaluation,
    MutationProposal,
    MutationTarget,
    ReflectionEngine,
)
from desi.evolution.sandbox import default_stable


@pytest.fixture()
def stable():
    return default_stable()


@pytest.fixture()
def clone(stable) -> CloneSandbox:
    return CloneSandbox(stable)


@pytest.fixture()
def proposal_with_delta(stable) -> MutationProposal:
    return MutationProposal(
        parent_version=stable.version,
        problem="Branches open too eagerly on weak evidence.",
        hypothesis="Raising branch_open_evidence_min from 0.30 to 0.45 "
                   "should suppress speculative branches.",
        target=MutationTarget.BRANCH_HEURISTICS,
        config_delta={
            "guard_thresholds.branch_open_evidence_min": 0.45,
        },
        expected_improvement="At least 30% fewer branch_opened events on "
                             "S5 under seed=42.",
        rollback_conditions=(
            "revert if branch_opened events on S2 fall below 1",
            "revert if guard_blocked rate on S6 drops to 0",
        ),
        motivating_findings=("rf_branch_overopen",),
    )


@pytest.fixture()
def evaluation_report(clone, proposal_with_delta):
    clone.apply(proposal_with_delta)
    evaluator = MutationEvaluation(seed=11)
    return evaluator.run(clone, proposal_with_delta.mutation_id)


@pytest.fixture()
def reflection_report():
    harness = EvaluationHarness(model="m")
    result = harness.run_scenario(scenario_by_id("S5"), seed=11)
    return ReflectionEngine().reflect(result)
