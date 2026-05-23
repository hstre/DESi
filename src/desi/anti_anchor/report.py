"""v3.51 — anti-anchor report.

Pflichtmetriken (directive § v3.51):

* ``anti_anchor_effect``    — leakage reduction
  produced by the best non-self-suppressing anti
  cohort (i.e. the suppressive arm that keeps
  plateau_recall high).
* ``leakage_reduction``     — fractional drop from
  baseline leakage to the chosen anti kind.
* ``repulsion_count``       — count of trajectories
  repelled (would have fired but for the anti).
* ``suppression_stability`` — deterministic replay.

Concept Gate #3: ``anti_anchor_effect > 0``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .ablation import (
    AntiOutcome, PLATEAU_RADIUS, run_all_anti_kinds,
    run_under_anti,
)
from .anchors import (
    ANTI_COUNT, ANTI_RADIUS, AntiAnchorKind,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class AntiKindResult:
    anti_kind: str
    leakage_count: int
    plateau_resolved_count: int
    repulsion_count: int
    plateau_recall: float
    leakage_reduction: float

    def to_dict(self) -> dict[str, object]:
        return {
            "anti_kind": self.anti_kind,
            "leakage_count": self.leakage_count,
            "plateau_resolved_count":
                self.plateau_resolved_count,
            "repulsion_count":
                self.repulsion_count,
            "plateau_recall": self.plateau_recall,
            "leakage_reduction":
                self.leakage_reduction,
        }


@dataclass(frozen=True)
class V351Report:
    plateau_population: int
    plateau_radius: float
    anti_radius: float
    anti_count: int
    baseline_leakage: int
    kind_results: tuple[AntiKindResult, ...]
    best_anti_kind: str
    anti_anchor_effect: int
    leakage_reduction: float
    repulsion_count: int
    plateau_recall_at_best: float
    suppression_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_population":
                self.plateau_population,
            "plateau_radius": self.plateau_radius,
            "anti_radius": self.anti_radius,
            "anti_count": self.anti_count,
            "baseline_leakage":
                self.baseline_leakage,
            "kind_results": [
                r.to_dict() for r in self.kind_results
            ],
            "best_anti_kind": self.best_anti_kind,
            "anti_anchor_effect":
                self.anti_anchor_effect,
            "leakage_reduction":
                self.leakage_reduction,
            "repulsion_count":
                self.repulsion_count,
            "plateau_recall_at_best":
                self.plateau_recall_at_best,
            "suppression_stability":
                self.suppression_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _summarise(
    kind: str, outcomes: tuple[AntiOutcome, ...],
    baseline_leakage: int, plateau_population: int,
) -> AntiKindResult:
    leak = sum(1 for o in outcomes if o.leakage)
    res = sum(1 for o in outcomes if o.plateau_resolved)
    rep = sum(1 for o in outcomes if o.repelled)
    recall = (
        _round(res / plateau_population)
        if plateau_population else 0.0
    )
    reduction = (
        _round(1.0 - leak / baseline_leakage)
        if baseline_leakage else 0.0
    )
    return AntiKindResult(
        anti_kind=kind, leakage_count=leak,
        plateau_resolved_count=res,
        repulsion_count=rep,
        plateau_recall=recall,
        leakage_reduction=reduction,
    )


def _pick_best(
    results: tuple[AntiKindResult, ...],
    plateau_population: int,
) -> AntiKindResult:
    """Best non-baseline anti kind that preserves full
    plateau recall AND maximises leakage reduction.
    Falls back to the lowest leakage if no kind
    preserves recall."""
    eligible = [
        r for r in results
        if r.anti_kind != AntiAnchorKind.NONE.value
        and r.plateau_resolved_count == plateau_population
    ]
    if eligible:
        return max(
            eligible,
            key=lambda r: (
                r.leakage_reduction, -r.repulsion_count,
            ),
        )
    non_baseline = [
        r for r in results
        if r.anti_kind != AntiAnchorKind.NONE.value
    ]
    if not non_baseline:
        return results[0]
    return min(non_baseline, key=lambda r: r.leakage_count)


def _replay_stability() -> float:
    a = [o.to_dict() for o in run_all_anti_kinds()]
    b = [o.to_dict() for o in run_all_anti_kinds()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V351Report:
    pop = len(plateau_trajectory_ids())
    all_outs = run_all_anti_kinds()
    by_kind: dict[str, list[AntiOutcome]] = {}
    for o in all_outs:
        by_kind.setdefault(o.anti_kind, []).append(o)
    baseline = sum(
        1 for o in by_kind.get(
            AntiAnchorKind.NONE.value, [],
        ) if o.leakage
    )
    results = tuple(
        _summarise(
            k.value, tuple(by_kind.get(k.value, ())),
            baseline, pop,
        )
        for k in AntiAnchorKind
    )
    best = _pick_best(results, pop)
    replay = _replay_stability()

    effect = baseline - best.leakage_count

    halt = replay < 1.0
    if halt:
        verdict = "HALT_SUPPRESSION_DRIFT"
    elif effect > 0 and best.plateau_recall == 1.0:
        verdict = "ANTI_ANCHOR_SUPPRESSES_LEAKAGE"
    elif effect > 0:
        verdict = "ANTI_ANCHOR_PARTIAL"
    else:
        verdict = "ANTI_ANCHOR_INERT"

    rationale = (
        f"INFO: plateau_radius {PLATEAU_RADIUS}, "
        f"anti_radius {ANTI_RADIUS}, "
        f"anti_count {ANTI_COUNT}",
        f"INFO: baseline_leakage {baseline}",
        f"INFO: per-kind results "
        f"{[r.to_dict() for r in results]}",
        f"INFO: best_anti_kind {best.anti_kind} "
        f"(leakage {best.leakage_count}, recall "
        f"{best.plateau_recall}, repulsion "
        f"{best.repulsion_count})",
        f"INFO: anti_anchor_effect {effect}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"suppression_stability {replay}",
    )

    return V351Report(
        plateau_population=pop,
        plateau_radius=PLATEAU_RADIUS,
        anti_radius=ANTI_RADIUS,
        anti_count=ANTI_COUNT,
        baseline_leakage=baseline,
        kind_results=results,
        best_anti_kind=best.anti_kind,
        anti_anchor_effect=effect,
        leakage_reduction=best.leakage_reduction,
        repulsion_count=best.repulsion_count,
        plateau_recall_at_best=best.plateau_recall,
        suppression_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_anti_anchor_effects_artifact(
) -> dict[str, object]:
    outs = run_all_anti_kinds()
    return {
        "schema_version": "v3_51_anti_anchor_effects",
        "plateau_radius": PLATEAU_RADIUS,
        "anti_radius": ANTI_RADIUS,
        "anti_count": ANTI_COUNT,
        "outcomes": [o.to_dict() for o in outs],
    }


__all__ = [
    "AntiKindResult", "V351Report",
    "build_anti_anchor_effects_artifact",
    "build_report",
]
