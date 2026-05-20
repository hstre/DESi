"""Multi-seed paired evaluation + statistical aggregation (v0.8).

v0.7 introduced :class:`PairedMutationEvaluation`, which compares a
stable run against a clone run on a closed scenario set — but on
*one* seed. v0.8 promotes the same closed set to ``N`` seeds (default
five) and produces per-scenario aggregate statistics
(mean / median / std of the per-seed deltas).

Design rules (per v0.8 directive):

* The seed list is **deterministic and fixed**: ``(42, 43, 44, 45, 46)``.
  v0.8 explicitly forbids random seeds.
* A run never decides promotion on a single seed. The
  :class:`MultiSeedEvaluationReport` is the unit consumed by
  :class:`desi.evolution.SignificanceGate`, which gates promotion on
  ``≥4 of 5`` improved on the evolution candidate *and* ``5 of 5``
  neutral-or-improved on every regression guard.
* The optional stress seed ``999`` may be added for ``ADV_BRANCH_EXPLOSION``
  only and is **never** promotion-relevant; its outcome is recorded
  for forensics.

This module is additive. The v0.7 :class:`PairedMutationEvaluation`
remains untouched and its tests stay green.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from ..eval.seeded import (
    GenerationMetadata,
    InstantiatedScenario,
    SeededScenarioEngine,
    seed_variant_scenarios,
)
from .paired_evaluation import (
    PairedEvaluationReport,
    PairedMutationEvaluation,
    PairedScenarioOutcome,
    _ConfiguredHarness,
    EVOLUTION_CANDIDATE_SCENARIOS,
    PFLICHT_ADVERSARIAL,
    REGRESSION_GUARDS,
)
from .sandbox import CloneSandbox


# v0.8 directive: the five mandatory seeds. Fixed; never randomised.
DEFAULT_SEEDS: tuple[int, ...] = (42, 43, 44, 45, 46)

# Optional stress seed — only logged for ADV_BRANCH_EXPLOSION, not
# fed into the SignificanceGate.
STRESS_SEED: int = 999


# ---------------------------------------------------------------------------
# Per-scenario aggregates
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioAggregate:
    """Per-scenario statistical summary over the seed set.

    Aggregates are computed over the per-seed
    :class:`desi.evolution.MetricsDelta` values. The fields are
    deterministic given identical inputs.
    """

    scenario_id: str
    n_seeds: int
    # Branch counter — primary promotion signal.
    mean_branch_delta: float
    median_branch_delta: float
    std_branch_delta: float
    # Timeline length — secondary signal.
    mean_timeline_delta: float
    median_timeline_delta: float
    std_timeline_delta: float
    # Guard-blocked counter — neutral in v0.7/v0.8 verdict logic but
    # surfaced for transparency (it is the mechanism-of-action signal).
    mean_guard_delta: float
    # Per-seed verdict tallies. Each tuple element corresponds to one
    # seed in ``MultiSeedEvaluationReport.seeds`` (positional).
    per_seed_verdicts: tuple[str, ...] = field(default_factory=tuple)

    @property
    def improved_seed_count(self) -> int:
        return sum(1 for v in self.per_seed_verdicts if v == "improved")

    @property
    def neutral_seed_count(self) -> int:
        return sum(1 for v in self.per_seed_verdicts if v == "neutral")

    @property
    def regressed_seed_count(self) -> int:
        return sum(1 for v in self.per_seed_verdicts if v == "regressed")

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "n_seeds": self.n_seeds,
            "mean_branch_delta": self.mean_branch_delta,
            "median_branch_delta": self.median_branch_delta,
            "std_branch_delta": self.std_branch_delta,
            "mean_timeline_delta": self.mean_timeline_delta,
            "median_timeline_delta": self.median_timeline_delta,
            "std_timeline_delta": self.std_timeline_delta,
            "mean_guard_delta": self.mean_guard_delta,
            "per_seed_verdicts": list(self.per_seed_verdicts),
            "improved_seed_count": self.improved_seed_count,
            "neutral_seed_count": self.neutral_seed_count,
            "regressed_seed_count": self.regressed_seed_count,
        }


def _mean(values: Iterable[float]) -> float:
    vs = list(values)
    if not vs:
        return 0.0
    return statistics.fmean(vs)


def _median(values: Iterable[float]) -> float:
    vs = list(values)
    if not vs:
        return 0.0
    return float(statistics.median(vs))


def _std(values: Iterable[float]) -> float:
    """Population standard deviation. 0.0 for a single sample.

    v0.8 uses population std (not sample std) so that ``n=1`` does not
    raise — multi-seed reports may be inspected one seed at a time
    during development without crashing the aggregate.
    """
    vs = list(values)
    if len(vs) < 2:
        return 0.0
    return float(statistics.pstdev(vs))


def _aggregate_one_scenario(
    scenario_id: str,
    outcomes: list[PairedScenarioOutcome],
) -> ScenarioAggregate:
    """Build a :class:`ScenarioAggregate` from per-seed outcomes."""
    branch_deltas = [o.delta.branch_opened_delta for o in outcomes]
    timeline_deltas = [o.delta.timeline_length_delta for o in outcomes]
    guard_deltas = [o.delta.guard_blocked_delta for o in outcomes]
    verdicts = tuple(o.delta.verdict for o in outcomes)
    return ScenarioAggregate(
        scenario_id=scenario_id,
        n_seeds=len(outcomes),
        mean_branch_delta=_mean(branch_deltas),
        median_branch_delta=_median(branch_deltas),
        std_branch_delta=_std(branch_deltas),
        mean_timeline_delta=_mean(timeline_deltas),
        median_timeline_delta=_median(timeline_deltas),
        std_timeline_delta=_std(timeline_deltas),
        mean_guard_delta=_mean(guard_deltas),
        per_seed_verdicts=verdicts,
    )


# ---------------------------------------------------------------------------
# Full multi-seed report
# ---------------------------------------------------------------------------


@dataclass
class MultiSeedEvaluationReport:
    """Full record of an N-seed paired evaluation.

    The report keeps the raw per-seed paired reports (so any later
    audit can reconstruct exact per-seed metrics) plus per-scenario
    aggregates. The :attr:`aggregate_verdict` collapses the per-seed
    verdicts into one of four labels:

    * ``improved``    — promotion candidate is robustly improved AND no
                        seed regressed on a regression guard
    * ``regressed``   — at least one seed regressed on a regression guard
    * ``inconclusive`` — promotion-candidate signal is not robust enough
                        (fewer than the required number of improved seeds,
                        but no regression either)
    * ``neutral``     — every seed × scenario delta is neutral

    The actual promotion decision lives in
    :class:`SignificanceGate`; ``aggregate_verdict`` is the
    informational summary the ledger records.

    v0.9 fields:

    * ``generation_metadata`` — per-(scenario, seed) ``GenerationMetadata``;
      empty when the static (non-seeded) runner was used.
    * ``permutation_coverage`` — per-scenario count of *distinct*
      permutation_ids that appeared across the seed list. ``1`` for
      static scenarios; ``N`` for fully-covered seed-variant ones.
    * ``unique_path_count`` — per-scenario count of *distinct* clone
      branch_signatures across the seed list. Less than
      ``permutation_coverage`` means "variance generated, but the runs
      converged on the same path".
    """

    mutation_id: str
    clone_id: str
    parent_version: str
    timestamp: datetime
    scenario_ids: tuple[str, ...]
    seeds: tuple[int, ...]
    # Per-seed full paired reports, in seed order.
    per_seed_reports: tuple[PairedEvaluationReport, ...] = field(default_factory=tuple)
    # Per-scenario aggregates, indexed by scenario_id.
    aggregates: dict[str, ScenarioAggregate] = field(default_factory=dict)
    # Optional stress-seed outcome (ADV_BRANCH_EXPLOSION only, never
    # promotion-relevant).
    stress_outcome: PairedScenarioOutcome | None = None
    # v0.9: per-(scenario, seed) generation metadata (empty if static).
    generation_metadata: dict[tuple[str, int], GenerationMetadata] = field(
        default_factory=dict,
    )
    # v0.9: per-scenario permutation coverage + unique-path counts.
    permutation_coverage: dict[str, int] = field(default_factory=dict)
    unique_path_count: dict[str, int] = field(default_factory=dict)

    @property
    def aggregate_verdict(self) -> str:
        any_regression = any(
            a.regressed_seed_count > 0 for a in self.aggregates.values()
        )
        if any_regression:
            return "regressed"
        any_improvement = any(
            a.improved_seed_count > 0 for a in self.aggregates.values()
        )
        if not any_improvement:
            return "neutral"
        # At least one improvement and no regression. Promotion-grade
        # improvement requires SignificanceGate; the report itself
        # reports "improved" when *every* candidate scenario hits the
        # robust threshold (≥4/5). Otherwise it is "inconclusive".
        # We cannot know "which scenarios count as candidates" from
        # this report alone — that's the gate's job — so we use a
        # conservative rule: aggregate is "improved" only if every
        # scenario with any improvement has ≥4/5 improved seeds (and
        # every other scenario is fully neutral). The gate refines
        # this with the explicit candidate / guard partition.
        for agg in self.aggregates.values():
            if agg.improved_seed_count == 0:
                continue
            if agg.improved_seed_count < 4 and agg.n_seeds >= 5:
                return "inconclusive"
        return "improved"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "clone_id": self.clone_id,
            "parent_version": self.parent_version,
            "timestamp": self.timestamp.isoformat(),
            "scenario_ids": list(self.scenario_ids),
            "seeds": list(self.seeds),
            "aggregate_verdict": self.aggregate_verdict,
            "aggregates": {
                sid: agg.to_dict() for sid, agg in self.aggregates.items()
            },
            "stress_outcome": (
                self.stress_outcome.to_dict()
                if self.stress_outcome is not None else None
            ),
        }


# ---------------------------------------------------------------------------
# Multi-seed runner
# ---------------------------------------------------------------------------


class MultiSeedMutationEvaluation:
    """Run the v0.7 paired evaluation across ``N`` deterministic seeds.

    Default behaviour matches the v0.8 directive: five seeds, exactly
    ``(42, 43, 44, 45, 46)``. The optional ``stress_seed=999`` adds a
    sixth run on ``ADV_BRANCH_EXPLOSION`` *only*; that run is logged
    on the report but is **not** used by the
    :class:`SignificanceGate`.

    v0.9: pass an :class:`SeededScenarioEngine` instance to ``engine``
    to switch each (scenario, seed) pair to its seed-variant
    instantiation. Without an engine, behaviour is bit-identical to
    v0.8.
    """

    def __init__(
        self,
        *,
        seeds: tuple[int, ...] = DEFAULT_SEEDS,
        model: str = "claude-opus-4-7",
        include_stress: bool = False,
        engine: SeededScenarioEngine | None = None,
    ) -> None:
        if not seeds:
            raise ValueError("seeds must be non-empty")
        if len(set(seeds)) != len(seeds):
            raise ValueError("seeds must be unique")
        self._seeds = tuple(seeds)
        self._model = model
        self._include_stress = include_stress
        self._engine = engine

    @property
    def seeds(self) -> tuple[int, ...]:
        return self._seeds

    @property
    def engine(self) -> SeededScenarioEngine | None:
        return self._engine

    def run(
        self,
        clone: CloneSandbox,
        mutation_id: str,
    ) -> MultiSeedEvaluationReport:
        """Execute one paired evaluation per seed; aggregate the result."""
        if self._engine is not None:
            return self._run_seeded(clone, mutation_id)
        return self._run_static(clone, mutation_id)

    def _run_static(
        self,
        clone: CloneSandbox,
        mutation_id: str,
    ) -> MultiSeedEvaluationReport:
        """v0.8 path: each seed runs the static scenario set."""
        per_seed_reports: list[PairedEvaluationReport] = []
        for seed in self._seeds:
            paired = PairedMutationEvaluation(
                model=self._model, seed=seed,
            ).run(clone, mutation_id)
            per_seed_reports.append(paired)

        scenario_ids = tuple(o.scenario_id for o in per_seed_reports[0].outcomes)
        aggregates: dict[str, ScenarioAggregate] = {}
        for sid in scenario_ids:
            outcomes_for_sid = [
                next(o for o in rep.outcomes if o.scenario_id == sid)
                for rep in per_seed_reports
            ]
            aggregates[sid] = _aggregate_one_scenario(sid, outcomes_for_sid)

        stress_outcome: PairedScenarioOutcome | None = None
        if self._include_stress:
            from .evaluation import AdversarialPattern
            stress_id = f"ADV_{AdversarialPattern.BRANCH_EXPLOSION.name}"
            paired_stress = PairedMutationEvaluation(
                model=self._model, seed=STRESS_SEED,
            ).run(clone, mutation_id)
            stress_outcome = next(
                (o for o in paired_stress.outcomes if o.scenario_id == stress_id),
                None,
            )

        # Without the engine, every (scenario, seed) shares
        # permutation_id="static" → coverage=1 per scenario.
        permutation_coverage = {sid: 1 for sid in scenario_ids}
        unique_path_count: dict[str, int] = {}
        for sid in scenario_ids:
            sigs = {
                next(o for o in rep.outcomes if o.scenario_id == sid)
                    .clone_metrics.branch_signature
                for rep in per_seed_reports
            }
            unique_path_count[sid] = len(sigs) if any(sigs) else 1

        return MultiSeedEvaluationReport(
            mutation_id=mutation_id,
            clone_id=clone.clone_id,
            parent_version=clone.stable.version,
            timestamp=datetime.now(timezone.utc),
            scenario_ids=scenario_ids,
            seeds=self._seeds,
            per_seed_reports=tuple(per_seed_reports),
            aggregates=aggregates,
            stress_outcome=stress_outcome,
            generation_metadata={},
            permutation_coverage=permutation_coverage,
            unique_path_count=unique_path_count,
        )

    def _run_seeded(
        self,
        clone: CloneSandbox,
        mutation_id: str,
    ) -> MultiSeedEvaluationReport:
        """v0.9 path: each (scenario, seed) is instantiated via the engine."""
        from .metrics import compute_path_quality, MetricsDelta
        scenario_ids = self._seeded_scenario_ids()
        per_seed_reports: list[PairedEvaluationReport] = []
        generation_metadata: dict[tuple[str, int], GenerationMetadata] = {}

        for seed in self._seeds:
            outcomes: list[PairedScenarioOutcome] = []
            for sid in scenario_ids:
                inst = self._engine.instantiate(sid, seed)
                generation_metadata[(sid, seed)] = inst.generation_metadata
                stable_result = _ConfiguredHarness(
                    model=self._model, seed=seed,
                    config=clone.stable.as_dict,
                ).run_scenario(inst)
                clone_result = _ConfiguredHarness(
                    model=self._model, seed=seed,
                    config=clone.config,
                ).run_scenario(inst)
                stable_metrics = compute_path_quality(stable_result)
                clone_metrics = compute_path_quality(clone_result)
                outcomes.append(PairedScenarioOutcome(
                    scenario_id=sid,
                    stable_result=stable_result,
                    clone_result=clone_result,
                    stable_metrics=stable_metrics,
                    clone_metrics=clone_metrics,
                    delta=MetricsDelta(
                        stable=stable_metrics, clone=clone_metrics,
                    ),
                ))
            per_seed_reports.append(PairedEvaluationReport(
                mutation_id=mutation_id,
                clone_id=clone.clone_id,
                stable_version=clone.stable.version,
                timestamp=datetime.now(timezone.utc),
                stable_config=dict(clone.stable.as_dict),
                clone_config=dict(clone.config),
                outcomes=outcomes,
            ))

        aggregates: dict[str, ScenarioAggregate] = {}
        permutation_coverage: dict[str, int] = {}
        unique_path_count: dict[str, int] = {}
        for sid in scenario_ids:
            outcomes_for_sid = [
                next(o for o in rep.outcomes if o.scenario_id == sid)
                for rep in per_seed_reports
            ]
            aggregates[sid] = _aggregate_one_scenario(sid, outcomes_for_sid)
            perms = {
                generation_metadata[(sid, seed)].permutation_id
                for seed in self._seeds
            }
            permutation_coverage[sid] = len(perms)
            sigs = {o.clone_metrics.branch_signature for o in outcomes_for_sid}
            unique_path_count[sid] = len(sigs)

        stress_outcome: PairedScenarioOutcome | None = None
        if self._include_stress:
            from .evaluation import AdversarialPattern
            stress_id = f"ADV_{AdversarialPattern.BRANCH_EXPLOSION.name}"
            inst = self._engine.instantiate(stress_id, STRESS_SEED)
            generation_metadata[(stress_id, STRESS_SEED)] = inst.generation_metadata
            stable_result = _ConfiguredHarness(
                model=self._model, seed=STRESS_SEED,
                config=clone.stable.as_dict,
            ).run_scenario(inst)
            clone_result = _ConfiguredHarness(
                model=self._model, seed=STRESS_SEED,
                config=clone.config,
            ).run_scenario(inst)
            sm = compute_path_quality(stable_result)
            cm = compute_path_quality(clone_result)
            stress_outcome = PairedScenarioOutcome(
                scenario_id=stress_id,
                stable_result=stable_result,
                clone_result=clone_result,
                stable_metrics=sm,
                clone_metrics=cm,
                delta=MetricsDelta(stable=sm, clone=cm),
            )

        return MultiSeedEvaluationReport(
            mutation_id=mutation_id,
            clone_id=clone.clone_id,
            parent_version=clone.stable.version,
            timestamp=datetime.now(timezone.utc),
            scenario_ids=scenario_ids,
            seeds=self._seeds,
            per_seed_reports=tuple(per_seed_reports),
            aggregates=aggregates,
            stress_outcome=stress_outcome,
            generation_metadata=generation_metadata,
            permutation_coverage=permutation_coverage,
            unique_path_count=unique_path_count,
        )

    def _seeded_scenario_ids(self) -> tuple[str, ...]:
        """Closed scenario id list used in the seeded (v0.9) path."""
        from .evaluation import AdversarialPattern
        ids: list[str] = []
        for sid in EVOLUTION_CANDIDATE_SCENARIOS:
            ids.append(sid)
        for pat in PFLICHT_ADVERSARIAL:
            ids.append(f"ADV_{pat.name}")
        for sid in REGRESSION_GUARDS:
            ids.append(sid)
        return tuple(ids)


__all__ = [
    "DEFAULT_SEEDS",
    "STRESS_SEED",
    "MultiSeedEvaluationReport",
    "MultiSeedMutationEvaluation",
    "ScenarioAggregate",
]
