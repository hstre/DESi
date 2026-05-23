"""v3.67 — minimal predictor report.

Pflichtmetriken (directive § v3.67):

* ``model_auc``         — per-model AUC
* ``model_complexity``  — per-model feature count
* ``marginal_gain``     — AUC gain over the previous
  complexity tier
* ``best_model``        — most parsimonious
  near-optimum

Paper-11 final gate #4: ``best_model includes
distance + coverage``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .comparison import (
    best_model, evaluate_all_models, marginal_gains,
)
from .models import ModelKind


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V367Report:
    evaluations: tuple[dict, ...]
    model_auc: dict[str, float]
    model_complexity: dict[str, int]
    marginal_gain: tuple[dict, ...]
    best_model: str
    best_model_features: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "evaluations": list(self.evaluations),
            "model_auc": dict(self.model_auc),
            "model_complexity":
                dict(self.model_complexity),
            "marginal_gain":
                list(self.marginal_gain),
            "best_model": self.best_model,
            "best_model_features":
                list(self.best_model_features),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = [r.to_dict() for r in evaluate_all_models()]
    b = [r.to_dict() for r in evaluate_all_models()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V367Report:
    results = evaluate_all_models()
    aucs = {r.model_kind: r.auc for r in results}
    comps = {
        r.model_kind: r.complexity for r in results
    }
    gains = marginal_gains(results)
    best = best_model(results)
    best_feats = next(
        tuple(r.feature_names)
        for r in results if r.model_kind == best
    )
    replay = _replay_stability()

    halt = replay < 1.0
    needs = {"distance", "coverage_gain"}
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif needs <= set(best_feats):
        verdict = "MINIMAL_PREDICTOR_INCLUDES_BOTH"
    else:
        verdict = "MINIMAL_PREDICTOR_MISSING_REQUIRED"

    rationale = (
        f"INFO: per-model AUC "
        f"{sorted(aucs.items())}",
        f"INFO: per-model complexity "
        f"{sorted(comps.items())}",
        f"INFO: marginal_gain {list(gains)}",
        f"INFO: best_model {best} "
        f"(features {list(best_feats)})",
        f"{'PASS' if needs <= set(best_feats) else 'FAIL'}: "
        f"best_model includes distance + "
        f"coverage_gain",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V367Report(
        evaluations=tuple(
            r.to_dict() for r in results
        ),
        model_auc=aucs,
        model_complexity=comps,
        marginal_gain=gains,
        best_model=best,
        best_model_features=best_feats,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_minimal_predictor_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_67_minimal_predictor",
        "evaluations": [
            r.to_dict()
            for r in evaluate_all_models()
        ],
        "marginal_gain": list(
            marginal_gains(evaluate_all_models()),
        ),
    }


__all__ = [
    "V367Report",
    "build_minimal_predictor_artifact",
    "build_report",
]
