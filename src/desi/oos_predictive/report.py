"""v3.66 — out-of-sample transfer report.

Pflichtmetriken (directive § v3.66):

* ``oos_auc``
* ``oos_precision``
* ``oos_recall``
* ``transfer_gap``       — train_auc - oos_auc
* ``replay_stability``
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..predictive.predictor import (
    EvaluationResult, FEATURE_NAMES, evaluate, fit,
)
from .oos_split import (
    REFERENCE_CORPORA, in_sample_pairs,
    out_of_sample_pairs,
)


PAPER11_FINAL_AUC_FLOOR: float = 0.70
MAX_TRANSFER_GAP: float = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V366Report:
    reference_corpora: tuple[str, ...]
    in_sample_pair_count: int
    oos_pair_count: int
    model: dict
    in_sample_evaluation: dict
    oos_evaluation: dict
    oos_auc: float
    oos_precision: float
    oos_recall: float
    transfer_gap: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "reference_corpora":
                list(self.reference_corpora),
            "in_sample_pair_count":
                self.in_sample_pair_count,
            "oos_pair_count":
                self.oos_pair_count,
            "model": self.model,
            "in_sample_evaluation":
                self.in_sample_evaluation,
            "oos_evaluation":
                self.oos_evaluation,
            "oos_auc": self.oos_auc,
            "oos_precision": self.oos_precision,
            "oos_recall": self.oos_recall,
            "transfer_gap": self.transfer_gap,
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
    a = fit(in_sample_pairs()).to_dict()
    b = fit(in_sample_pairs()).to_dict()
    if a == b:
        return 1.0
    return 0.0


def build_report() -> V366Report:
    train = in_sample_pairs()
    oos = out_of_sample_pairs()
    model = fit(train)
    in_eval = evaluate(model, train)
    oos_eval = evaluate(model, oos)
    gap = _round(in_eval.auc - oos_eval.auc)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        oos_eval.auc >= PAPER11_FINAL_AUC_FLOOR
        and abs(gap) <= MAX_TRANSFER_GAP
    ):
        verdict = "OOS_TRANSFER_HOLDS"
    elif oos_eval.auc >= PAPER11_FINAL_AUC_FLOOR:
        verdict = "OOS_TRANSFER_LARGE_GAP"
    else:
        verdict = "OOS_TRANSFER_FAILS"

    rationale = (
        f"INFO: reference_corpora "
        f"{list(REFERENCE_CORPORA)}",
        f"INFO: in_sample_pair_count {len(train)}, "
        f"oos_pair_count {len(oos)}",
        f"INFO: model weights {model.weights}, "
        f"threshold {model.threshold}",
        f"INFO: in_sample_evaluation "
        f"{in_eval.to_dict()}",
        f"INFO: oos_evaluation "
        f"{oos_eval.to_dict()}",
        f"{'PASS' if oos_eval.auc >= PAPER11_FINAL_AUC_FLOOR else 'FAIL'}: "
        f"oos_auc {oos_eval.auc} >= "
        f"{PAPER11_FINAL_AUC_FLOOR}",
        f"{'PASS' if abs(gap) <= MAX_TRANSFER_GAP else 'FAIL'}: "
        f"|transfer_gap| {abs(gap)} <= "
        f"{MAX_TRANSFER_GAP}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V366Report(
        reference_corpora=REFERENCE_CORPORA,
        in_sample_pair_count=len(train),
        oos_pair_count=len(oos),
        model=model.to_dict(),
        in_sample_evaluation=in_eval.to_dict(),
        oos_evaluation=oos_eval.to_dict(),
        oos_auc=oos_eval.auc,
        oos_precision=oos_eval.precision,
        oos_recall=oos_eval.recall,
        transfer_gap=gap,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_oos_transfer_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_66_oos_transfer",
        "reference_corpora":
            list(REFERENCE_CORPORA),
        "in_sample_pairs": [
            {"a": p.a, "b": p.b,
             "is_resonant": p.is_resonant}
            for p in in_sample_pairs()
        ],
        "oos_pairs": [
            {"a": p.a, "b": p.b,
             "is_resonant": p.is_resonant}
            for p in out_of_sample_pairs()
        ],
    }


__all__ = [
    "MAX_TRANSFER_GAP", "PAPER11_FINAL_AUC_FLOOR",
    "V366Report", "build_oos_transfer_artifact",
    "build_report",
]
