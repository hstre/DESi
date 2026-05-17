"""v3.65 — pure-Python Fisher-style linear predictor.

Each plateau pair gets a feature vector

    (distance, coverage_gain, heterogeneity, diversity)

with closed mappings

* ``distance``      — 1.0 if high_d bucket else 0.0
* ``coverage_gain`` — integer cast to float
* ``heterogeneity`` — 1.0 if diff_fam else 0.0
* ``diversity``     — failure-profile diversity score

The model fits per-feature means on the training fold,
derives a linear discriminant
``score(x) = sum_f (mean_res_f - mean_non_f) * x_f``,
and uses raw score as a continuous classifier. ROC
sweep over training-set score thresholds yields the
test-set AUC; a single threshold (the median of the
training scores) defines precision/recall/false-
positive-rate.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..causal_complementarity.ablation import (
    PairFactors,
)


FEATURE_NAMES: tuple[str, ...] = (
    "distance", "coverage_gain",
    "heterogeneity", "diversity",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def features(p: PairFactors) -> dict[str, float]:
    return {
        "distance": (
            1.0 if p.distance_bucket == "high_d"
            else 0.0
        ),
        "coverage_gain": float(p.coverage_gain),
        "heterogeneity": (
            0.0 if p.same_family else 1.0
        ),
        "diversity": float(p.diversity_score),
    }


@dataclass(frozen=True)
class LinearModel:
    feature_names: tuple[str, ...]
    weights: dict[str, float]
    threshold: float

    def score(self, p: PairFactors) -> float:
        x = features(p)
        return sum(
            self.weights[f] * x[f]
            for f in self.feature_names
        )

    def predict(self, p: PairFactors) -> bool:
        return self.score(p) >= self.threshold

    def to_dict(self) -> dict[str, object]:
        return {
            "feature_names":
                list(self.feature_names),
            "weights": dict(self.weights),
            "threshold": self.threshold,
        }


def fit(
    train: tuple[PairFactors, ...],
    feature_names: tuple[str, ...] = FEATURE_NAMES,
) -> LinearModel:
    pos = [p for p in train if p.is_resonant]
    neg = [p for p in train if not p.is_resonant]
    weights: dict[str, float] = {}
    for f in feature_names:
        if pos:
            m_p = sum(
                features(p)[f] for p in pos
            ) / len(pos)
        else:
            m_p = 0.0
        if neg:
            m_n = sum(
                features(p)[f] for p in neg
            ) / len(neg)
        else:
            m_n = 0.0
        weights[f] = _round(m_p - m_n)
    # Threshold = midpoint between mean train scores
    # of the two classes
    if pos and neg:
        mean_pos_score = sum(
            sum(weights[f] * features(p)[f]
                for f in feature_names)
            for p in pos
        ) / len(pos)
        mean_neg_score = sum(
            sum(weights[f] * features(p)[f]
                for f in feature_names)
            for p in neg
        ) / len(neg)
        threshold = _round(
            (mean_pos_score + mean_neg_score) / 2.0,
        )
    else:
        threshold = 0.0
    return LinearModel(
        feature_names=feature_names,
        weights=weights, threshold=threshold,
    )


@dataclass(frozen=True)
class EvaluationResult:
    auc: float
    precision: float
    recall: float
    false_positive_rate: float
    true_positive_count: int
    false_positive_count: int
    true_negative_count: int
    false_negative_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "auc": self.auc,
            "precision": self.precision,
            "recall": self.recall,
            "false_positive_rate":
                self.false_positive_rate,
            "true_positive_count":
                self.true_positive_count,
            "false_positive_count":
                self.false_positive_count,
            "true_negative_count":
                self.true_negative_count,
            "false_negative_count":
                self.false_negative_count,
        }


def _roc_auc(
    scores: list[tuple[float, bool]],
) -> float:
    """Compute AUC by ranking pairs (positive,
    negative). For every positive-negative pair, the
    positive's score should exceed the negative's;
    AUC = P(score_pos > score_neg) + 0.5 *
    P(score_pos == score_neg)."""
    pos = [s for s, y in scores if y]
    neg = [s for s, y in scores if not y]
    if not pos or not neg:
        return 0.5
    wins = 0
    ties = 0
    total = len(pos) * len(neg)
    for sp in pos:
        for sn in neg:
            if sp > sn:
                wins += 1
            elif sp == sn:
                ties += 1
    return _round((wins + 0.5 * ties) / total)


def evaluate(
    model: LinearModel,
    test: tuple[PairFactors, ...],
) -> EvaluationResult:
    scored = [
        (model.score(p), p.is_resonant)
        for p in test
    ]
    auc = _roc_auc(scored)
    tp = sum(
        1 for s, y in scored
        if y and s >= model.threshold
    )
    fp = sum(
        1 for s, y in scored
        if not y and s >= model.threshold
    )
    tn = sum(
        1 for s, y in scored
        if not y and s < model.threshold
    )
    fn = sum(
        1 for s, y in scored
        if y and s < model.threshold
    )
    precision = (
        _round(tp / (tp + fp))
        if (tp + fp) > 0 else 0.0
    )
    recall = (
        _round(tp / (tp + fn))
        if (tp + fn) > 0 else 0.0
    )
    fpr = (
        _round(fp / (fp + tn))
        if (fp + tn) > 0 else 0.0
    )
    return EvaluationResult(
        auc=auc, precision=precision, recall=recall,
        false_positive_rate=fpr,
        true_positive_count=tp,
        false_positive_count=fp,
        true_negative_count=tn,
        false_negative_count=fn,
    )


__all__ = [
    "EvaluationResult", "FEATURE_NAMES",
    "LinearModel", "evaluate", "features", "fit",
]
