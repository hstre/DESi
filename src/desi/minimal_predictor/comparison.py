"""v3.67 — minimal-predictor harness.

Runs each ModelKind through the v3.65 train/test
split, records per-model AUC and marginal gain over
the previous complexity tier, and returns the
best_model verdict.
"""
from __future__ import annotations

from ..predictive.blind_split import (
    test_pairs, train_pairs,
)
from ..predictive.predictor import (
    EvaluationResult, evaluate, fit,
)
from .models import (
    ModelEvaluation, ModelKind, complexity_of,
    features_for,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def evaluate_model(kind: str) -> ModelEvaluation:
    features = features_for(kind)
    train = train_pairs()
    test = test_pairs()
    model = fit(train, feature_names=features)
    result = evaluate(model, test)
    return ModelEvaluation(
        model_kind=kind,
        feature_names=features,
        complexity=complexity_of(kind),
        auc=result.auc, precision=result.precision,
        recall=result.recall,
        false_positive_rate=(
            result.false_positive_rate
        ),
    )


def evaluate_all_models() -> tuple[
    ModelEvaluation, ...,
]:
    return tuple(
        evaluate_model(k.value)
        for k in ModelKind
    )


def marginal_gains(
    results: tuple[ModelEvaluation, ...],
) -> tuple[dict, ...]:
    """For each (current, baseline) pair where baseline
    is the immediately less-complex evaluation, compute
    auc(current) - auc(baseline). Sorted by current
    complexity ascending."""
    by_complexity = sorted(
        results, key=lambda r: r.complexity,
    )
    out: list[dict] = []
    for i, r in enumerate(by_complexity):
        if i == 0:
            gain = 0.0
            baseline_kind = None
        else:
            baseline = by_complexity[i - 1]
            gain = _round(r.auc - baseline.auc)
            baseline_kind = baseline.model_kind
        out.append({
            "model_kind": r.model_kind,
            "complexity": r.complexity,
            "auc": r.auc,
            "baseline_kind": baseline_kind,
            "marginal_gain": gain,
        })
    return tuple(out)


def best_model(
    results: tuple[ModelEvaluation, ...],
    auc_tolerance: float = 0.01,
) -> str:
    """The simplest model whose AUC is within
    ``auc_tolerance`` of the maximum AUC across all
    evaluations. This favours parsimony at equal-AUC
    ties."""
    max_auc = max(r.auc for r in results)
    eligible = [
        r for r in results
        if r.auc >= max_auc - auc_tolerance
    ]
    return min(
        eligible,
        key=lambda r: (
            r.complexity, r.model_kind,
        ),
    ).model_kind


__all__ = [
    "best_model", "evaluate_all_models",
    "evaluate_model", "marginal_gains",
]
