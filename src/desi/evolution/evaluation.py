"""MutationEvaluation — runs a clone against the three required suites.

Per v0.5 directive:

* Pflichtsuite      — S2, S6, S7 (always)
* Adversarial-Suite — five named patterns (always)
* Regression-Suite  — every existing scenario from
                       :func:`desi.eval.list_scenarios`

Adversarial patterns are synthesised here as short trajectories that
hit a specific failure mode. Promoting a mutation requires every
suite to remain green and no measurable regression on the path-
quality / performance metrics.

v0.5 cannot change DESi behaviour, so a "clone evaluation" in this
release is observation-only: the clone's config_delta is recorded
and surfaced in the evaluation report, but the underlying
:func:`desi.runner.run_desi` invocation is unchanged. The signal a
jury looks for is therefore "did anything regress" rather than "did
anything improve" — which matches v0.5's safety-over-progress
posture.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..eval import (
    EvaluationHarness,
    EvaluationResult,
    Scenario,
    ScenarioExpectation,
    scenario_by_id,
)
from ..models import Trajectory, TrajectoryStep
from .sandbox import CloneSandbox


# ---------------------------------------------------------------------------
# Adversarial patterns
# ---------------------------------------------------------------------------


class AdversarialPattern(str, Enum):
    """The five v0.5 adversarial scenarios."""

    BRANCH_EXPLOSION = "branch_explosion"
    FALSE_PENULTIMATE = "false_penultimate_candidate"
    OSCILLATING_NOVELTY = "oscillating_novelty"
    RANDOM_WALK = "random_walk"
    LATE_RECOVERY = "late_recovery"


def _adv_branch_explosion() -> Trajectory:
    # Six distinct focus claims in seven steps → branch explosion.
    steps = [
        TrajectoryStep(loop_index=i, operator="T6",
                       focus_claim_id=f"E{i:02d}")
        for i in range(6)
    ]
    steps.append(TrajectoryStep(loop_index=6, operator="T2",
                                focus_claim_id="E05"))
    return Trajectory(trajectory_id="adv_branch_explosion",
                      steps=steps, en_events=[])


def _adv_false_penultimate() -> Trajectory:
    # The would-be "penultimate" claim is tampered with at the last
    # step.
    return Trajectory(
        trajectory_id="adv_false_penultimate_candidate",
        steps=[
            TrajectoryStep(loop_index=0, operator="T6", focus_claim_id="P1"),
            TrajectoryStep(loop_index=1, operator="T6", focus_claim_id="P2"),
            TrajectoryStep(loop_index=2, operator="T1", focus_claim_id="P2"),
            # Late switch back to a stale claim.
            TrajectoryStep(loop_index=3, operator="T8", focus_claim_id="P1"),
        ],
        en_events=[],
    )


def _adv_oscillating_novelty() -> Trajectory:
    # Strict alternation between two foci — destabilising.
    return Trajectory(
        trajectory_id="adv_oscillating_novelty",
        steps=[
            TrajectoryStep(loop_index=0, operator="T6", focus_claim_id="A"),
            TrajectoryStep(loop_index=1, operator="T6", focus_claim_id="B"),
            TrajectoryStep(loop_index=2, operator="T6", focus_claim_id="A"),
            TrajectoryStep(loop_index=3, operator="T6", focus_claim_id="B"),
            TrajectoryStep(loop_index=4, operator="T6", focus_claim_id="A"),
            TrajectoryStep(loop_index=5, operator="T6", focus_claim_id="B"),
        ],
        en_events=[],
    )


def _adv_random_walk() -> Trajectory:
    # Eight operators with no closing seal.
    return Trajectory(
        trajectory_id="adv_random_walk",
        steps=[
            TrajectoryStep(loop_index=0, operator="T1", focus_claim_id="W1"),
            TrajectoryStep(loop_index=1, operator="T3", focus_claim_id="W2"),
            TrajectoryStep(loop_index=2, operator="T6", focus_claim_id="W3"),
            TrajectoryStep(loop_index=3, operator="T2", focus_claim_id="W2"),
            TrajectoryStep(loop_index=4, operator="T1", focus_claim_id="W4"),
            TrajectoryStep(loop_index=5, operator="T3", focus_claim_id="W3"),
            TrajectoryStep(loop_index=6, operator="T2", focus_claim_id="W1"),
            TrajectoryStep(loop_index=7, operator="T6", focus_claim_id="W5"),
        ],
        en_events=[],
    )


def _adv_late_recovery() -> Trajectory:
    # Almost-failure path that recovers at the last step.
    return Trajectory(
        trajectory_id="adv_late_recovery",
        steps=[
            TrajectoryStep(loop_index=0, operator="T1", focus_claim_id="L1"),
            TrajectoryStep(loop_index=1, operator="T1", focus_claim_id="L2"),
            TrajectoryStep(loop_index=2, operator="T1", focus_claim_id="L3"),
            TrajectoryStep(loop_index=3, operator="T1", focus_claim_id="L4"),
            TrajectoryStep(loop_index=4, operator="T6", focus_claim_id="L5"),
            TrajectoryStep(loop_index=5, operator="T8", focus_claim_id="L5"),
        ],
        en_events=[],
    )


ADVERSARIAL_BUILDERS: dict[AdversarialPattern, Any] = {
    AdversarialPattern.BRANCH_EXPLOSION: _adv_branch_explosion,
    AdversarialPattern.FALSE_PENULTIMATE: _adv_false_penultimate,
    AdversarialPattern.OSCILLATING_NOVELTY: _adv_oscillating_novelty,
    AdversarialPattern.RANDOM_WALK: _adv_random_walk,
    AdversarialPattern.LATE_RECOVERY: _adv_late_recovery,
}


def adversarial_scenario(pattern: AdversarialPattern) -> Scenario:
    builder = ADVERSARIAL_BUILDERS[pattern]
    # Adversarial scenarios just need to *run without crash* and not
    # produce hook errors; we keep the expectation block minimal.
    return Scenario(
        scenario_id=f"ADV_{pattern.name}",
        name=pattern.value,
        description=f"Adversarial pattern: {pattern.value}",
        trajectory_factory=builder,
        expectation=ScenarioExpectation(
            min_event_counts={"run_started": 1, "run_ended": 1},
            notes="Adversarial probe — must not crash the runner.",
        ),
    )


# ---------------------------------------------------------------------------
# Evaluation report
# ---------------------------------------------------------------------------


@dataclass
class MutationEvaluationReport:
    """Outcome of a clone evaluation across all three suites."""

    mutation_id: str
    clone_id: str
    stable_version: str
    timestamp: datetime
    pflicht_results: list[EvaluationResult] = field(default_factory=list)
    adversarial_results: list[EvaluationResult] = field(default_factory=list)
    regression_results: list[EvaluationResult] = field(default_factory=list)

    @property
    def passed_pflicht(self) -> bool:
        return all(r.passed for r in self.pflicht_results)

    @property
    def passed_adversarial(self) -> bool:
        # Adversarial scenarios pass if the runner completed and the
        # hook recorded no errors. The expectation block already
        # enforces run_started + run_ended.
        return all(r.passed and not r.hook_errors
                   for r in self.adversarial_results)

    @property
    def passed_regression(self) -> bool:
        return all(r.passed for r in self.regression_results)

    @property
    def all_green(self) -> bool:
        return (
            self.passed_pflicht
            and self.passed_adversarial
            and self.passed_regression
        )

    @property
    def regressions_detected(self) -> list[str]:
        out: list[str] = []
        for r in (self.pflicht_results + self.adversarial_results
                  + self.regression_results):
            if not r.passed:
                detail = "; ".join(
                    f"{k}: {v}" for k, v in r.expectations_detail.items()
                    if not r.expectations_met.get(k, True)
                )
                out.append(f"{r.scenario_id}: {detail or 'failed'}")
        return out

    @property
    def performance_delta(self) -> float:
        """Heuristic: difference in mean timeline length, clone vs stable.

        v0.5 stub: the clone is not yet wired into DESi behaviour, so
        the delta is zero by construction. The field exists so that
        downstream governance can audit *that* it was measured.
        """
        return 0.0

    @property
    def path_quality_delta(self) -> float:
        """Heuristic: difference in mean branches opened per run.

        Same v0.5 stub note as :attr:`performance_delta`.
        """
        return 0.0


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


PFLICHT_SCENARIO_IDS: tuple[str, ...] = ("S2", "S6", "S7")
REGRESSION_SCENARIO_IDS: tuple[str, ...] = (
    "S1", "S2", "S3", "S4", "S5", "S6", "S7",
)


class MutationEvaluation:
    """Evaluates a clone sandbox against the three suites."""

    def __init__(self, *, model: str = "claude-opus-4-7",
                 seed: int = 42) -> None:
        self._model = model
        self._seed = seed

    def run(
        self,
        clone: CloneSandbox,
        mutation_id: str,
    ) -> MutationEvaluationReport:
        harness = EvaluationHarness(
            model=self._model,
            config={
                "version": "v0.5",
                "clone_id": clone.clone_id,
                **{f"knob.{k}": str(v) for k, v in clone.config.items()},
            },
        )
        pflicht = [
            harness.run_scenario(scenario_by_id(sid), seed=self._seed)
            for sid in PFLICHT_SCENARIO_IDS
        ]
        adversarial = [
            harness.run_scenario(
                adversarial_scenario(pat), seed=self._seed,
            )
            for pat in AdversarialPattern
        ]
        regression = [
            harness.run_scenario(scenario_by_id(sid), seed=self._seed)
            for sid in REGRESSION_SCENARIO_IDS
        ]
        return MutationEvaluationReport(
            mutation_id=mutation_id,
            clone_id=clone.clone_id,
            stable_version=clone.stable.version,
            timestamp=datetime.now(timezone.utc),
            pflicht_results=pflicht,
            adversarial_results=adversarial,
            regression_results=regression,
        )
