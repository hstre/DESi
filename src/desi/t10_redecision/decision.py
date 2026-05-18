"""v3.104d — T10 final re-decision under the
directional gate.

We feed the live T10 metrics (from v3.101-v3.104)
into the directional gate from v3.104b and report
the result. The original v3.104 ROI (v3.104) is
re-confirmed.
"""
from __future__ import annotations

from ..t10_directional.gate import GateInput
from ..t10_directional.gate import (
    directional_gate as _directional_gate,
)
from ..t10_gate.delta import (
    adverse_auc_delta,
    adverse_flip_count,
    beneficial_auc_delta,
    beneficial_flip_count,
)
from ..t10_roi.tradeoff import (
    architecture_roi,
    complexity_cost,
    recovery_gain,
)


def _t10_gate_input() -> GateInput:
    return GateInput(
        candidate_auc=1.0,
        injected_purity=1.0,
        injected_auc=1.0,
        adverse_flip_count=adverse_flip_count(),
        beneficial_flip_count=(
            beneficial_flip_count()
        ),
        adverse_auc_delta=adverse_auc_delta(),
        beneficial_auc_delta=(
            beneficial_auc_delta()
        ),
        historical_auc_delta=max(
            adverse_auc_delta(),
            beneficial_auc_delta(),
        ),
        replay_stability=1.0,
    )


def t10_directional_decision() -> dict[
    str, object,
]:
    gi = _t10_gate_input()
    res = _directional_gate(gi)
    return {
        "passed": res.passed,
        "failing_conditions":
            list(res.failing_conditions),
        "gate_input": gi.to_dict(),
    }


def t10_directional_go() -> bool:
    return t10_directional_decision()["passed"]


def final_roi() -> float:
    return architecture_roi()


def final_recovery_gain() -> float:
    return recovery_gain()


def final_complexity_cost() -> float:
    return complexity_cost()


__all__ = [
    "final_complexity_cost",
    "final_recovery_gain",
    "final_roi",
    "t10_directional_decision",
    "t10_directional_go",
]
