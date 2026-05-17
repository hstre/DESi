"""v3.65 — blind prediction report.

Pflichtmetriken (directive § v3.65):

* ``auc``
* ``precision``
* ``recall``
* ``false_positive_rate``
* ``replay_stability``
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .blind_split import (
    TEST_STRIDE, folded_pairs, test_pairs,
    train_pairs,
)
from .predictor import (
    EvaluationResult, FEATURE_NAMES, LinearModel,
    evaluate, fit,
)


PAPER11_FINAL_AUC_FLOOR: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V365Report:
    train_size: int
    test_size: int
    feature_names: tuple[str, ...]
    model: dict
    evaluation: dict
    auc: float
    precision: float
    recall: float
    false_positive_rate: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "train_size": self.train_size,
            "test_size": self.test_size,
            "feature_names":
                list(self.feature_names),
            "model": self.model,
            "evaluation": self.evaluation,
            "auc": self.auc,
            "precision": self.precision,
            "recall": self.recall,
            "false_positive_rate":
                self.false_positive_rate,
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
    a = fit(train_pairs()).to_dict()
    b = fit(train_pairs()).to_dict()
    if a == b:
        return 1.0
    return 0.0


def build_report() -> V365Report:
    train = train_pairs()
    test = test_pairs()
    model = fit(train)
    result = evaluate(model, test)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif result.auc >= PAPER11_FINAL_AUC_FLOOR:
        verdict = "BLIND_PREDICTION_PASSES"
    elif result.auc >= 0.50:
        verdict = "BLIND_PREDICTION_WEAK"
    else:
        verdict = "BLIND_PREDICTION_FAILED"

    rationale = (
        f"INFO: train_size {len(train)}, test_size "
        f"{len(test)} (TEST_STRIDE = {TEST_STRIDE})",
        f"INFO: feature_names {list(FEATURE_NAMES)}",
        f"INFO: model weights {model.weights}, "
        f"threshold {model.threshold}",
        f"INFO: evaluation {result.to_dict()}",
        f"{'PASS' if result.auc >= PAPER11_FINAL_AUC_FLOOR else 'FAIL'}: "
        f"auc {result.auc} >= "
        f"{PAPER11_FINAL_AUC_FLOOR}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V365Report(
        train_size=len(train),
        test_size=len(test),
        feature_names=FEATURE_NAMES,
        model=model.to_dict(),
        evaluation=result.to_dict(),
        auc=result.auc,
        precision=result.precision,
        recall=result.recall,
        false_positive_rate=(
            result.false_positive_rate
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_predictive_activation_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_65_predictive_activation",
        "fold_records": [
            {
                "a": fp.pair.a, "b": fp.pair.b,
                "fold": fp.fold,
                "is_resonant":
                    fp.pair.is_resonant,
            }
            for fp in folded_pairs()
        ],
    }


__all__ = [
    "PAPER11_FINAL_AUC_FLOOR", "V365Report",
    "build_predictive_activation_artifact",
    "build_report",
]
