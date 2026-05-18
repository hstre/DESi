"""v3.104b — gate evaluators.

Two closed gate variants:

* ``old_gate(*)``           - the directive's
  original five conditions, with the
  ``historical_auc_delta <= 0.05`` clause
  treating any AUC drift as failure.
* ``directional_gate(*)``   - the proposed
  refinement: only ADVERSE flips and ADVERSE
  AUC drift count against the gate; beneficial
  deltas are documented but allowed.

Both evaluators are deterministic functions of
their input metrics so they can be applied to
both the actual T10 result and the synthetic
adverse fixtures used in v3.104b's false-block /
false-pass tests.
"""
from __future__ import annotations

from dataclasses import dataclass


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class GateInput:
    candidate_auc: float
    injected_purity: float
    injected_auc: float
    adverse_flip_count: int
    beneficial_flip_count: int
    adverse_auc_delta: float
    beneficial_auc_delta: float
    historical_auc_delta: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_auc": self.candidate_auc,
            "injected_purity":
                self.injected_purity,
            "injected_auc": self.injected_auc,
            "adverse_flip_count":
                self.adverse_flip_count,
            "beneficial_flip_count":
                self.beneficial_flip_count,
            "adverse_auc_delta":
                self.adverse_auc_delta,
            "beneficial_auc_delta":
                self.beneficial_auc_delta,
            "historical_auc_delta":
                self.historical_auc_delta,
            "replay_stability":
                self.replay_stability,
        }


@dataclass(frozen=True)
class GateResult:
    passed: bool
    failing_conditions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "failing_conditions":
                list(self.failing_conditions),
        }


_AUC_THRESHOLD: float = 0.70
_PURITY_THRESHOLD: float = 0.70
_AUC_DRIFT_TOLERANCE: float = 0.05


def old_gate(g: GateInput) -> GateResult:
    """The original v3.104 gate. Fails on any
    historical_auc_delta exceeding the
    tolerance, regardless of direction."""
    fails: list[str] = []
    if g.candidate_auc < _AUC_THRESHOLD:
        fails.append("candidate_auc")
    if g.injected_purity < _PURITY_THRESHOLD:
        fails.append("injected_purity")
    if g.injected_auc < _AUC_THRESHOLD:
        fails.append("injected_auc")
    if g.adverse_flip_count > 0:
        fails.append("gate_flip_count")
    if g.historical_auc_delta > (
        _AUC_DRIFT_TOLERANCE
    ):
        fails.append("historical_auc_delta")
    if g.replay_stability < 1.0:
        fails.append("replay_stability")
    return GateResult(
        passed=(len(fails) == 0),
        failing_conditions=tuple(fails),
    )


def directional_gate(g: GateInput) -> GateResult:
    """The proposed refinement. Replaces
    historical_auc_delta with adverse_auc_delta
    so beneficial AUC gains do not block."""
    fails: list[str] = []
    if g.candidate_auc < _AUC_THRESHOLD:
        fails.append("candidate_auc")
    if g.injected_purity < _PURITY_THRESHOLD:
        fails.append("injected_purity")
    if g.injected_auc < _AUC_THRESHOLD:
        fails.append("injected_auc")
    if g.adverse_flip_count > 0:
        fails.append("adverse_flip_count")
    if g.adverse_auc_delta > (
        _AUC_DRIFT_TOLERANCE
    ):
        fails.append("adverse_auc_delta")
    if g.replay_stability < 1.0:
        fails.append("replay_stability")
    return GateResult(
        passed=(len(fails) == 0),
        failing_conditions=tuple(fails),
    )


__all__ = [
    "GateInput",
    "GateResult",
    "directional_gate",
    "old_gate",
]
