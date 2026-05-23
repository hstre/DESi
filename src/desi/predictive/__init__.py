"""DESi v3.65 — blind predictive complementarity.

Train a pure-Python linear discriminant on a
deterministic 67% subset of plateau-anchor pairs and
test on the held-out 33%. The four features
(distance, coverage_gain, heterogeneity, diversity)
are the v3.61-v3.64 audit's explanatory variables;
this sprint asks whether those variables are also
predictive when the test pairs are blind.
"""
from __future__ import annotations

from .blind_split import (
    FoldedPair, TEST_STRIDE, folded_pairs,
    test_pairs, train_pairs,
)
from .predictor import (
    EvaluationResult, FEATURE_NAMES, LinearModel,
    evaluate, features, fit,
)
from .report import (
    PAPER11_FINAL_AUC_FLOOR, V365Report,
    build_predictive_activation_artifact,
    build_report,
)


__all__ = [
    "EvaluationResult", "FEATURE_NAMES",
    "FoldedPair", "LinearModel",
    "PAPER11_FINAL_AUC_FLOOR", "TEST_STRIDE",
    "V365Report",
    "build_predictive_activation_artifact",
    "build_report", "evaluate", "features", "fit",
    "folded_pairs", "test_pairs", "train_pairs",
]
