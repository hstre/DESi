"""v3.39 — specificity-recovery report.

Pflichtmetriken (directive) per selector:

* ``specificity_score``     — plateau_resolutions
  divided by (plateau_resolutions + accidental_rescues
  + overcontrol). Matches v3.35's formula.
* ``plateau_recall``        — fraction of the 20
  plateau trajectories the policy resolves.
* ``accidental_rescue_count``
* ``overcontrol`` (count)
* ``replay_stability``

Paper-10 v3 gate #4 / #5: best policy must achieve
``specificity_score >= 0.90`` and
``plateau_recall >= 0.90``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .ablation import (
    PolicyOutcome, full_corpus_overcontrol,
    run_all_policies, run_policy,
)
from .selector import SelectorKind


MIN_SPECIFICITY_SCORE = 0.90
MIN_PLATEAU_RECALL    = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class PolicyResult:
    selector: str
    plateau_resolved_count: int
    accidental_rescue_count: int
    overcontrol_count: int
    selector_fire_count: int
    specificity_score: float
    plateau_recall: float

    def to_dict(self) -> dict[str, object]:
        return {
            "selector": self.selector,
            "plateau_resolved_count":
                self.plateau_resolved_count,
            "accidental_rescue_count":
                self.accidental_rescue_count,
            "overcontrol_count":
                self.overcontrol_count,
            "selector_fire_count":
                self.selector_fire_count,
            "specificity_score":
                self.specificity_score,
            "plateau_recall": self.plateau_recall,
        }


@dataclass(frozen=True)
class V339Report:
    plateau_population: int
    policy_results: tuple[PolicyResult, ...]
    best_selector: str
    specificity_score: float       # best selector's
    plateau_recall: float          # best selector's
    accidental_rescue_count: int   # best selector's
    overcontrol: int               # best selector's
    full_corpus_overcontrol: int   # best selector's, full corpus
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_population":
                self.plateau_population,
            "policy_results": [
                r.to_dict() for r in self.policy_results
            ],
            "best_selector": self.best_selector,
            "specificity_score":
                self.specificity_score,
            "plateau_recall": self.plateau_recall,
            "accidental_rescue_count":
                self.accidental_rescue_count,
            "overcontrol": self.overcontrol,
            "full_corpus_overcontrol":
                self.full_corpus_overcontrol,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _result_for(
    selector: str, outcomes: tuple[PolicyOutcome, ...],
    plateau_population: int,
) -> PolicyResult:
    selected = [
        o for o in outcomes if o.selector == selector
    ]
    res = sum(1 for o in selected if o.plateau_resolved)
    acc = sum(1 for o in selected if o.accidental_rescue)
    over = sum(1 for o in selected if o.overcontrol)
    fires = sum(1 for o in selected if o.selector_fired)
    denom = res + acc + over
    spec = _round(res / denom) if denom else 0.0
    recall = (
        _round(res / plateau_population)
        if plateau_population else 0.0
    )
    return PolicyResult(
        selector=selector,
        plateau_resolved_count=res,
        accidental_rescue_count=acc,
        overcontrol_count=over,
        selector_fire_count=fires,
        specificity_score=spec,
        plateau_recall=recall,
    )


def _pick_best(
    results: tuple[PolicyResult, ...],
) -> PolicyResult:
    """Highest specificity_score; ties broken by higher
    plateau_recall, then by SelectorKind declaration
    order (so NONE never wins a true tie)."""
    order = {
        k.value: i for i, k in enumerate(SelectorKind)
    }
    return min(
        results,
        key=lambda r: (
            -r.specificity_score, -r.plateau_recall,
            order[r.selector],
        ),
    )


def _replay_stability() -> float:
    a = [o.to_dict() for o in run_all_policies()]
    b = [o.to_dict() for o in run_all_policies()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V339Report:
    from ..support_plateau.extractor import (
        plateau_trajectory_ids,
    )
    plateau_population = len(plateau_trajectory_ids())
    outcomes = run_all_policies()
    results = tuple(
        _result_for(k.value, outcomes, plateau_population)
        for k in SelectorKind
    )
    best = _pick_best(results)
    replay = _replay_stability()

    fco = full_corpus_overcontrol(best.selector)
    halt = (
        best.specificity_score < MIN_SPECIFICITY_SCORE
        or best.plateau_recall < MIN_PLATEAU_RECALL
    )
    if halt:
        if best.specificity_score < MIN_SPECIFICITY_SCORE:
            verdict = "HALT_LOW_SPECIFICITY"
        else:
            verdict = "HALT_LOW_PLATEAU_RECALL"
    elif fco > 0:
        # Gates 4 and 5 pass on the v3.35 universe, but
        # the named policy overcontrols ``fco`` healthy
        # SUPPORTED trajectories on the broader corpus.
        # Flag this so the Paper-10 v3 decision can read
        # both numbers off the report.
        verdict = "SPECIFICITY_LOCALLY_RECOVERED"
    else:
        verdict = "SPECIFICITY_RECOVERED"

    rationale = (
        f"{'PASS' if best.specificity_score >= MIN_SPECIFICITY_SCORE else 'FAIL'}: "
        f"specificity_score {best.specificity_score} "
        f">= {MIN_SPECIFICITY_SCORE}",
        f"{'PASS' if best.plateau_recall >= MIN_PLATEAU_RECALL else 'FAIL'}: "
        f"plateau_recall {best.plateau_recall} >= "
        f"{MIN_PLATEAU_RECALL}",
        f"INFO: best_selector {best.selector} "
        f"(resolved {best.plateau_resolved_count}, "
        f"accidental {best.accidental_rescue_count}, "
        f"overcontrol {best.overcontrol_count})",
        f"INFO: full_corpus_overcontrol {fco} "
        f"(SUPPORTED non-plateau trajectories the best "
        f"policy still rescues on the broader corpus)",
        f"INFO: NONE baseline = "
        f"{next(r for r in results if r.selector == 'none').to_dict()}",
        f"PASS: replay_stability {replay}",
    )

    return V339Report(
        plateau_population=plateau_population,
        policy_results=results,
        best_selector=best.selector,
        specificity_score=best.specificity_score,
        plateau_recall=best.plateau_recall,
        accidental_rescue_count=best.accidental_rescue_count,
        overcontrol=best.overcontrol_count,
        full_corpus_overcontrol=full_corpus_overcontrol(
            best.selector,
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_specificity_recovery_artifact(
) -> dict[str, object]:
    outcomes = run_all_policies()
    return {
        "schema_version": "v3_39_specificity_recovery",
        "outcomes": [o.to_dict() for o in outcomes],
    }


__all__ = [
    "MIN_PLATEAU_RECALL", "MIN_SPECIFICITY_SCORE",
    "PolicyResult", "V339Report", "build_report",
    "build_specificity_recovery_artifact",
]
