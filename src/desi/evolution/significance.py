"""SignificanceGate — promotion gating on multi-seed evidence (v0.8).

v0.7 promoted on a single-seed paired-evaluation verdict. v0.8
requires that promotion only happen when an improvement is
**reproducible across multiple deterministic seeds**.

Gating contract (per v0.8 directive):

* **Evolution candidate** (``ADV_BRANCH_EXPLOSION`` plus any scenario in
  :data:`desi.evolution.EVOLUTION_CANDIDATE_SCENARIOS`):

    - at least :data:`IMPROVED_THRESHOLD` of :data:`REQUIRED_SEED_COUNT`
      seeds verdict==improved (default 4/5)
    - **zero** seeds verdict==regressed

* **Regression guards** (``S2``, ``S6`` — :data:`REGRESSION_GUARDS`):

    - **all** seeds verdict ∈ {improved, neutral} (5/5)
    - no single regression on any seed is permitted

If both blocks pass → ``improved``.
If any guard regression on any seed → ``regressed``.
Otherwise (improvement signal is not robust *and* nothing regressed)
→ ``inconclusive``. Inconclusive yields ``REVISE`` — never veto —
because the system simply lacks evidence either way.

The gate produces a :class:`SignificanceDecision` record that the
ledger logs verbatim and the v0.8 jury consults in round 2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .evaluation import AdversarialPattern
from .multi_seed import MultiSeedEvaluationReport
from .paired_evaluation import (
    EVOLUTION_CANDIDATE_SCENARIOS,
    REGRESSION_GUARDS,
)


# v0.8 directive: ≥4 of 5 seeds must verdict==improved on the evolution
# candidate. The threshold is a class-level constant so that the v0.9
# revisit (which may make this configurable per mutation) has a single
# point of change.
REQUIRED_SEED_COUNT: int = 5
IMPROVED_THRESHOLD: int = 4


def _evolution_candidate_scenarios() -> tuple[str, ...]:
    """All scenarios that count as evolution candidates in v0.8."""
    return tuple(
        list(EVOLUTION_CANDIDATE_SCENARIOS)
        + [f"ADV_{AdversarialPattern.BRANCH_EXPLOSION.name}"]
    )


@dataclass(frozen=True)
class SignificanceDecision:
    """Output of :class:`SignificanceGate.decide`.

    Frozen so it can be appended to the ledger without further copying.
    """

    mutation_id: str
    verdict: str  # "improved" | "neutral" | "regressed" | "inconclusive"
    # Per-seed support: positional list of seeds whose evolution-
    # candidate outcome verdict==improved.
    supporting_seeds: tuple[int, ...] = field(default_factory=tuple)
    # Per-seed failure: seeds whose evolution-candidate verdict
    # regressed OR whose regression-guard verdict regressed (combined).
    failing_seeds: tuple[int, ...] = field(default_factory=tuple)
    # Free-text reason for the verdict.
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "verdict": self.verdict,
            "supporting_seeds": list(self.supporting_seeds),
            "failing_seeds": list(self.failing_seeds),
            "rationale": self.rationale,
        }


class SignificanceGate:
    """Decide promotion fitness from a :class:`MultiSeedEvaluationReport`."""

    def __init__(
        self,
        *,
        required_seed_count: int = REQUIRED_SEED_COUNT,
        improved_threshold: int = IMPROVED_THRESHOLD,
    ) -> None:
        if required_seed_count < 1:
            raise ValueError("required_seed_count must be >= 1")
        if improved_threshold < 1:
            raise ValueError("improved_threshold must be >= 1")
        if improved_threshold > required_seed_count:
            raise ValueError(
                "improved_threshold cannot exceed required_seed_count"
            )
        self._required = required_seed_count
        self._threshold = improved_threshold

    @property
    def required_seed_count(self) -> int:
        return self._required

    @property
    def improved_threshold(self) -> int:
        return self._threshold

    def decide(
        self,
        report: MultiSeedEvaluationReport,
    ) -> SignificanceDecision:
        """Run the v0.8 gating rules over ``report``."""
        if len(report.seeds) != self._required:
            return SignificanceDecision(
                mutation_id=report.mutation_id,
                verdict="inconclusive",
                supporting_seeds=(),
                failing_seeds=(),
                rationale=(
                    f"multi-seed report has {len(report.seeds)} seeds; "
                    f"gate requires exactly {self._required}."
                ),
            )

        candidate_ids = _evolution_candidate_scenarios()
        guard_ids = REGRESSION_GUARDS

        candidate_aggs = [
            report.aggregates[sid]
            for sid in candidate_ids
            if sid in report.aggregates
        ]
        guard_aggs = [
            report.aggregates[sid]
            for sid in guard_ids
            if sid in report.aggregates
        ]

        # --- Step 1: hard regression on any guard for any seed → regressed.
        guard_failures: list[int] = []
        for agg in guard_aggs:
            for seed, verdict in zip(report.seeds, agg.per_seed_verdicts):
                if verdict == "regressed":
                    guard_failures.append(seed)
        if guard_failures:
            return SignificanceDecision(
                mutation_id=report.mutation_id,
                verdict="regressed",
                supporting_seeds=(),
                failing_seeds=tuple(sorted(set(guard_failures))),
                rationale=(
                    "regression guard verdict='regressed' on seeds "
                    f"{sorted(set(guard_failures))}; promotion blocked."
                ),
            )

        # --- Step 2: hard regression on a candidate for any seed → regressed.
        candidate_failures: list[int] = []
        for agg in candidate_aggs:
            for seed, verdict in zip(report.seeds, agg.per_seed_verdicts):
                if verdict == "regressed":
                    candidate_failures.append(seed)
        if candidate_failures:
            return SignificanceDecision(
                mutation_id=report.mutation_id,
                verdict="regressed",
                supporting_seeds=(),
                failing_seeds=tuple(sorted(set(candidate_failures))),
                rationale=(
                    "evolution candidate verdict='regressed' on seeds "
                    f"{sorted(set(candidate_failures))}; promotion blocked."
                ),
            )

        # --- Step 3: at least one candidate must hit ≥threshold/required
        # improved seeds. (Candidates that are wholly neutral don't
        # block — only candidates that fall *between* "neutral" and
        # "robust improvement" produce the inconclusive verdict.)
        if not candidate_aggs:
            return SignificanceDecision(
                mutation_id=report.mutation_id,
                verdict="neutral",
                supporting_seeds=(),
                failing_seeds=(),
                rationale="no evolution candidate scenario present.",
            )

        # Find the strongest candidate (most improved seeds).
        best_agg = max(
            candidate_aggs,
            key=lambda a: sum(1 for v in a.per_seed_verdicts if v == "improved"),
        )
        best_improved = [
            seed for seed, v in zip(report.seeds, best_agg.per_seed_verdicts)
            if v == "improved"
        ]
        best_not_improved = [
            seed for seed, v in zip(report.seeds, best_agg.per_seed_verdicts)
            if v != "improved"
        ]

        if len(best_improved) == 0:
            # No candidate improved on any seed → neutral, not inconclusive.
            return SignificanceDecision(
                mutation_id=report.mutation_id,
                verdict="neutral",
                supporting_seeds=(),
                failing_seeds=(),
                rationale=(
                    "no evolution candidate scenario verdict='improved' "
                    "on any seed; nothing to promote, nothing to revert."
                ),
            )

        if len(best_improved) < self._threshold:
            return SignificanceDecision(
                mutation_id=report.mutation_id,
                verdict="inconclusive",
                supporting_seeds=tuple(sorted(set(best_improved))),
                failing_seeds=tuple(sorted(set(best_not_improved))),
                rationale=(
                    f"strongest candidate scenario {best_agg.scenario_id} "
                    f"verdict='improved' on only {len(best_improved)}/"
                    f"{self._required} seeds — below threshold "
                    f"{self._threshold}/{self._required}."
                ),
            )
        supporting = list(best_improved)

        # --- Step 4: every guard must be 5/5 neutral-or-improved.
        # (Already guaranteed by step 1, but check defensively for
        # completeness so the rationale is precise.)
        for agg in guard_aggs:
            for seed, verdict in zip(report.seeds, agg.per_seed_verdicts):
                if verdict not in ("neutral", "improved"):
                    return SignificanceDecision(
                        mutation_id=report.mutation_id,
                        verdict="regressed",
                        supporting_seeds=tuple(sorted(set(supporting))),
                        failing_seeds=(seed,),
                        rationale=(
                            f"guard {agg.scenario_id} verdict='{verdict}' "
                            f"on seed {seed}."
                        ),
                    )

        return SignificanceDecision(
            mutation_id=report.mutation_id,
            verdict="improved",
            supporting_seeds=tuple(sorted(set(supporting))),
            failing_seeds=(),
            rationale=(
                f"candidate scenario {best_agg.scenario_id} cleared "
                f"{len(best_improved)}/{self._required} improved seeds "
                f"(threshold {self._threshold}/{self._required}); "
                f"every regression guard 5/5 neutral-or-improved."
            ),
        )


__all__ = [
    "IMPROVED_THRESHOLD",
    "REQUIRED_SEED_COUNT",
    "SignificanceDecision",
    "SignificanceGate",
]
