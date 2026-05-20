"""v3.67 — minimal-predictor model registry.

Four named models compared on the v3.65 train/test
split. Each model uses a strict subset of the
FEATURE_NAMES tuple from v3.65 and reuses the v3.65
Fisher-style linear discriminant for fitting and
scoring.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModelKind(str, Enum):
    A_DISTANCE_ONLY     = "A_distance_only"
    B_COVERAGE_ONLY     = "B_coverage_only"
    C_DISTANCE_AND_COV  = "C_distance_and_coverage"
    D_ALL_FEATURES      = "D_all_features"


_FEATURE_SETS: dict[str, tuple[str, ...]] = {
    ModelKind.A_DISTANCE_ONLY.value: ("distance",),
    ModelKind.B_COVERAGE_ONLY.value: ("coverage_gain",),
    ModelKind.C_DISTANCE_AND_COV.value: (
        "distance", "coverage_gain",
    ),
    ModelKind.D_ALL_FEATURES.value: (
        "distance", "coverage_gain",
        "heterogeneity", "diversity",
    ),
}


def features_for(kind: str) -> tuple[str, ...]:
    return _FEATURE_SETS[kind]


def complexity_of(kind: str) -> int:
    return len(features_for(kind))


@dataclass(frozen=True)
class ModelEvaluation:
    model_kind: str
    feature_names: tuple[str, ...]
    complexity: int
    auc: float
    precision: float
    recall: float
    false_positive_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "model_kind": self.model_kind,
            "feature_names":
                list(self.feature_names),
            "complexity": self.complexity,
            "auc": self.auc,
            "precision": self.precision,
            "recall": self.recall,
            "false_positive_rate":
                self.false_positive_rate,
        }


__all__ = [
    "ModelEvaluation", "ModelKind", "complexity_of",
    "features_for",
]
