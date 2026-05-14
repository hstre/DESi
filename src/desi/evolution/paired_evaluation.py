"""Stable-vs-clone paired evaluation (v0.7).

v0.7 introduces the first *behaviour-effective* clone evaluation: the
same scenarios are run twice, once with the stable config and once
with the clone's config_delta applied, and a :class:`MetricsDelta` is
computed per scenario. Promotion gates on the per-scenario verdicts.

The v0.6 :class:`MutationEvaluation` stays untouched. v0.7 adds
:class:`PairedMutationEvaluation` as a sibling that callers opt into.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..eval import EvaluationHarness, EvaluationResult, scenario_by_id
from ..runner import run_desi
from .evaluation import (
    AdversarialPattern,
    adversarial_scenario,
)
from .metrics import MetricsDelta, PathQualityMetrics, compute_path_quality
from .sandbox import CloneSandbox


# v0.7 directive: the evolution candidate plus the regression / pflicht
# guards must all be evaluated. The set is closed by design.
EVOLUTION_CANDIDATE_SCENARIOS: tuple[str, ...] = ("S5",)
PFLICHT_ADVERSARIAL: tuple[AdversarialPattern, ...] = (
    AdversarialPattern.BRANCH_EXPLOSION,
)
REGRESSION_GUARDS: tuple[str, ...] = ("S2", "S6")


@dataclass
class PairedScenarioOutcome:
    """One scenario evaluated under stable AND clone config."""

    scenario_id: str
    stable_result: EvaluationResult
    clone_result: EvaluationResult
    stable_metrics: PathQualityMetrics
    clone_metrics: PathQualityMetrics
    delta: MetricsDelta

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "stable_metrics": self.stable_metrics.to_dict(),
            "clone_metrics": self.clone_metrics.to_dict(),
            "delta": self.delta.to_dict(),
        }


@dataclass
class PairedEvaluationReport:
    """Aggregate report of a paired evaluation across the v0.7 scenario set."""

    mutation_id: str
    clone_id: str
    stable_version: str
    timestamp: datetime
    stable_config: dict[str, Any]
    clone_config: dict[str, Any]
    outcomes: list[PairedScenarioOutcome] = field(default_factory=list)

    @property
    def all_verdicts(self) -> list[str]:
        return [o.delta.verdict for o in self.outcomes]

    @property
    def has_regression(self) -> bool:
        return any(o.delta.verdict == "regressed" for o in self.outcomes)

    @property
    def has_improvement(self) -> bool:
        return any(o.delta.verdict == "improved" for o in self.outcomes)

    @property
    def passed_evolution_candidate(self) -> bool:
        """At least one candidate scenario improved without regression."""
        for o in self.outcomes:
            if (o.scenario_id in EVOLUTION_CANDIDATE_SCENARIOS
                    and o.delta.verdict == "improved"):
                return True
        # Adversarial pattern ADV_BRANCH_EXPLOSION also qualifies as a
        # candidate per the v0.7 directive (it is the load-bearing
        # explosion target).
        for o in self.outcomes:
            if (o.scenario_id == f"ADV_{AdversarialPattern.BRANCH_EXPLOSION.name}"
                    and o.delta.verdict == "improved"):
                return True
        return False

    @property
    def passed_regression_guards(self) -> bool:
        for o in self.outcomes:
            if o.scenario_id in REGRESSION_GUARDS:
                if o.delta.verdict == "regressed":
                    return False
        return True

    @property
    def aggregate_verdict(self) -> str:
        """Three-state aggregate matching MetricsDelta.verdict."""
        if self.has_regression:
            return "regressed"
        if self.has_improvement:
            return "improved"
        return "neutral"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "clone_id": self.clone_id,
            "stable_version": self.stable_version,
            "timestamp": self.timestamp.isoformat(),
            "stable_config": dict(self.stable_config),
            "clone_config": dict(self.clone_config),
            "aggregate_verdict": self.aggregate_verdict,
            "passed_evolution_candidate": self.passed_evolution_candidate,
            "passed_regression_guards": self.passed_regression_guards,
            "outcomes": [o.to_dict() for o in self.outcomes],
        }


class PairedMutationEvaluation:
    """Runs each scenario twice — once under stable, once under clone."""

    def __init__(
        self,
        *,
        model: str = "claude-opus-4-7",
        seed: int = 42,
    ) -> None:
        self._model = model
        self._seed = seed

    def run(
        self,
        clone: CloneSandbox,
        mutation_id: str,
    ) -> PairedEvaluationReport:
        stable_config = clone.stable.as_dict
        clone_config = clone.config
        scenarios = self._scenario_list()
        outcomes: list[PairedScenarioOutcome] = []
        from ..eval import EvaluationHarness  # avoid cycle
        for sc in scenarios:
            stable_result = self._evaluate_under_config(sc, stable_config)
            clone_result = self._evaluate_under_config(sc, clone_config)
            stable_metrics = compute_path_quality(stable_result)
            clone_metrics = compute_path_quality(clone_result)
            outcomes.append(PairedScenarioOutcome(
                scenario_id=sc.scenario_id,
                stable_result=stable_result,
                clone_result=clone_result,
                stable_metrics=stable_metrics,
                clone_metrics=clone_metrics,
                delta=MetricsDelta(
                    stable=stable_metrics, clone=clone_metrics,
                ),
            ))
        return PairedEvaluationReport(
            mutation_id=mutation_id,
            clone_id=clone.clone_id,
            stable_version=clone.stable.version,
            timestamp=datetime.now(timezone.utc),
            stable_config=dict(stable_config),
            clone_config=dict(clone_config),
            outcomes=outcomes,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _scenario_list(self):
        scs = []
        for sid in EVOLUTION_CANDIDATE_SCENARIOS:
            scs.append(scenario_by_id(sid))
        for pat in PFLICHT_ADVERSARIAL:
            scs.append(adversarial_scenario(pat))
        for sid in REGRESSION_GUARDS:
            scs.append(scenario_by_id(sid))
        return scs

    def _evaluate_under_config(
        self,
        scenario,
        config: dict[str, Any],
    ) -> EvaluationResult:
        """Run scenario through harness while forwarding the v0.7 config."""
        return _ConfiguredHarness(
            model=self._model,
            seed=self._seed,
            config=config,
        ).run_scenario(scenario)


class _ConfiguredHarness:
    """Tiny EvaluationHarness shim that forwards config to run_desi.

    The v0.4 EvaluationHarness pre-dates v0.7's config parameter; this
    shim reproduces its lifecycle while passing ``config`` through.
    """

    def __init__(
        self, *,
        model: str = "claude-opus-4-7",
        seed: int = 0,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._model = model
        self._seed = seed
        self._config = dict(config or {})

    def run_scenario(self, scenario) -> EvaluationResult:
        from ..diagnostics import compute_all
        from ..memory.recorder import MemoryRecorder
        from ..memory.store import InMemoryStore
        from ..observe.session import ObservationSession
        from .. import eval as eval_pkg
        from ..eval.harness import EvaluationResult as _ER, config_hash, _new_evaluation_id
        from ..eval.harness import EvaluationHarness  # for type
        # Replicate EvaluationHarness.run_scenario but with config-aware
        # run_desi.
        store = InMemoryStore()
        recorder = MemoryRecorder(store)
        session = ObservationSession(
            recorder=recorder, model=self._model, seed=self._seed,
            config={**self._config, "scenario_id": scenario.scenario_id,
                    "seed": self._seed},
        )
        if scenario.pre_run is not None:
            scenario.pre_run(session)
        trajectory = scenario.trajectory_factory()
        # Inline the run_desi lifecycle so post_run can write inside
        # the run window (matches v0.4 harness behaviour).
        if self._config:
            session.hook.set_active_config(self._config)
        session.hook.on_run_start(trajectory)
        for step in trajectory.steps:
            session.hook.on_step(step)
        report = compute_all(trajectory)
        if scenario.post_run is not None:
            scenario.post_run(session)
        session.hook.on_run_end(report)
        from ..eval.harness import EvaluationHarness as _Harness
        # Manually build the expectations check using harness internals.
        harness = _Harness(model=self._model, config={
            "version": "v0.7",
            **{f"knob.{k}": str(v) for k, v in self._config.items()},
        })
        expectations_met, expectations_detail = harness._check_expectations(
            scenario, session, store,
        )
        hook_errors = [
            f"{e.stage}: {type(e.exception).__name__}: {e.exception}"
            for e in session.hook.errors
        ]
        return _ER(
            evaluation_id=_new_evaluation_id(scenario.scenario_id, self._seed),
            scenario_id=scenario.scenario_id,
            seed=self._seed,
            timestamp=datetime.now(timezone.utc),
            model=self._model,
            config_hash=config_hash(self._config),
            report=report,
            timeline=session.timeline(),
            snapshots=list(session.snapshots),
            expectations_met=expectations_met,
            expectations_detail=expectations_detail,
            hook_errors=hook_errors,
        )


__all__ = [
    "EVOLUTION_CANDIDATE_SCENARIOS",
    "PFLICHT_ADVERSARIAL",
    "PairedEvaluationReport",
    "PairedMutationEvaluation",
    "PairedScenarioOutcome",
    "REGRESSION_GUARDS",
]
