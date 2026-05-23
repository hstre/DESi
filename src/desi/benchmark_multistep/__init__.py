"""DESi v2.3 multi-step gap benchmark — read-only over stable-v1.9.0."""
from __future__ import annotations

from .case import MultiStepCase, MultiStepCategory
from .cases import (
    ALL_MULTISTEP_CASES,
    R1_CASES, R2_CASES, R3_CASES, R4_CASES, R5_CASES,
    cases_by_category,
)
from .constraints import ConstraintReport, check_hard_constraints
from .metrics import MultiStepMetrics, compute_multistep_metrics
from .runner import (
    MultiStepBenchmarkRunner,
    MultiStepResult,
    MultiStepRun,
)

__all__ = [
    "ALL_MULTISTEP_CASES",
    "ConstraintReport",
    "MultiStepBenchmarkRunner",
    "MultiStepCase",
    "MultiStepCategory",
    "MultiStepMetrics",
    "MultiStepResult",
    "MultiStepRun",
    "R1_CASES", "R2_CASES", "R3_CASES", "R4_CASES", "R5_CASES",
    "cases_by_category",
    "check_hard_constraints",
    "compute_multistep_metrics",
]
