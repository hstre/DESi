"""DESi v3.16 — Causal-Chain Suspension Gate audit module."""
from __future__ import annotations

from .leap_classes import LEAP_TO_GUARD, LeapClass, classify
from .report import (
    CausalSuspensionReport,
    GateOutcome,
    build_suspension_report,
)
from .runner import (
    AdversarialOutcome,
    BenchmarkSnapshot,
    V315Result,
    run_all_benchmarks,
    run_v315_adversarial,
)

__all__ = [
    "AdversarialOutcome",
    "BenchmarkSnapshot",
    "CausalSuspensionReport",
    "GateOutcome",
    "LEAP_TO_GUARD",
    "LeapClass",
    "V315Result",
    "build_suspension_report",
    "classify",
    "run_all_benchmarks",
    "run_v315_adversarial",
]
