"""DESi v3.67 — minimal predictor.

Compares four named models (distance only, coverage
only, distance + coverage, all features) on the v3.65
train/test split and identifies the most parsimonious
near-optimum.
"""
from __future__ import annotations

from .comparison import (
    best_model, evaluate_all_models, evaluate_model,
    marginal_gains,
)
from .models import (
    ModelEvaluation, ModelKind, complexity_of,
    features_for,
)
from .report import (
    V367Report,
    build_minimal_predictor_artifact, build_report,
)


__all__ = [
    "ModelEvaluation", "ModelKind", "V367Report",
    "best_model",
    "build_minimal_predictor_artifact",
    "build_report", "complexity_of",
    "evaluate_all_models", "evaluate_model",
    "features_for", "marginal_gains",
]
