"""v3.124 — deployment decision across three
candidate strategies.

We compare three closed strategies for whether to
deploy a pre-T10 check, and on which rule:

* ``STRATEGY_NO_PRECHECK`` - allow every pool
  through to T10 (the v3.119 baseline).
* ``STRATEGY_SINGLE_THRESHOLD`` - the v3.120
  rule (text_variance only). Experimentally
  validated but blocked at gate (FAR > ceiling).
* ``STRATEGY_MULTI_SIGNAL`` - the v3.123 rule
  (text_variance + members_per_family). Adds
  one threshold and one orthogonal axis.

Each strategy is scored on (far, tpr,
complexity) against the v3.119 ground truth.
``best_strategy()`` picks the simplest strategy
that satisfies FAR <= FAR_CEILING and
TPR >= TPR_FLOOR. ``architecture_roi`` measures
the per-complexity reduction in false-activation
rate relative to the no-precheck baseline.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..pre_t10_rule.decision import (
    allowed_pool_count as single_allowed,
    blocked_pool_count as single_blocked,
    false_activation_rate as single_far,
    true_case_recall as single_tpr,
)
from ..pre_t10_v2.rule import (
    allowed_pool_count as multi_allowed,
    blocked_pool_count as multi_blocked,
    final_far as multi_far,
    final_tpr as multi_tpr,
)
from ..t10_boundary.boundary import (
    all_pool_recoverability,
)


_FAR_CEILING: float = 0.10
_TPR_FLOOR: float = 1.0


class Strategy(str, Enum):
    NO_PRECHECK        = "no_precheck"
    SINGLE_THRESHOLD   = "single_threshold"
    MULTI_SIGNAL       = "multi_signal"


STRATEGIES: tuple[str, ...] = tuple(
    s.value for s in Strategy
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _baseline_far() -> float:
    rec = list(all_pool_recoverability())
    total = len(rec)
    if total == 0:
        return 0.0
    neg = sum(1 for r in rec if not r.rescuable)
    return _round(neg / total)


@lru_cache(maxsize=1)
def _baseline_tpr() -> float:
    rec = list(all_pool_recoverability())
    pos = sum(1 for r in rec if r.rescuable)
    if pos == 0:
        return 0.0
    return 1.0


@lru_cache(maxsize=1)
def _baseline_allowed() -> int:
    return len(list(all_pool_recoverability()))


@dataclass(frozen=True)
class StrategyMetrics:
    strategy: str
    false_activation_rate: float
    true_case_recall: float
    rule_complexity: int
    allowed_count: int
    blocked_count: int
    architecture_roi: float
    far_ok: bool
    tpr_ok: bool
    qualifies: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "false_activation_rate":
                self.false_activation_rate,
            "true_case_recall":
                self.true_case_recall,
            "rule_complexity":
                self.rule_complexity,
            "allowed_count":
                self.allowed_count,
            "blocked_count":
                self.blocked_count,
            "architecture_roi":
                self.architecture_roi,
            "far_ok": self.far_ok,
            "tpr_ok": self.tpr_ok,
            "qualifies": self.qualifies,
        }


def _architecture_roi(
    far: float, complexity: int,
) -> float:
    """Per-complexity reduction in FAR vs
    the no-precheck baseline.

    The baseline is treated as complexity 0 (no
    rule) and gets ROI 0 by definition. Higher
    is better; negative would mean the rule made
    things worse than no rule at all."""
    baseline = _baseline_far()
    saved = baseline - far
    denom = max(complexity, 1)
    return _round(saved / denom)


@lru_cache(maxsize=1)
def metrics_no_precheck() -> StrategyMetrics:
    far = _baseline_far()
    tpr = _baseline_tpr()
    allowed = _baseline_allowed()
    far_ok = far <= _FAR_CEILING
    tpr_ok = tpr >= _TPR_FLOOR
    return StrategyMetrics(
        strategy=Strategy.NO_PRECHECK.value,
        false_activation_rate=far,
        true_case_recall=tpr,
        rule_complexity=0,
        allowed_count=allowed,
        blocked_count=0,
        architecture_roi=_architecture_roi(
            far, 0,
        ),
        far_ok=far_ok, tpr_ok=tpr_ok,
        qualifies=far_ok and tpr_ok,
    )


@lru_cache(maxsize=1)
def metrics_single_threshold() -> StrategyMetrics:
    far = single_far()
    tpr = single_tpr()
    far_ok = far <= _FAR_CEILING
    tpr_ok = tpr >= _TPR_FLOOR
    return StrategyMetrics(
        strategy=Strategy.SINGLE_THRESHOLD.value,
        false_activation_rate=far,
        true_case_recall=tpr,
        rule_complexity=1,
        allowed_count=single_allowed(),
        blocked_count=single_blocked(),
        architecture_roi=_architecture_roi(
            far, 1,
        ),
        far_ok=far_ok, tpr_ok=tpr_ok,
        qualifies=far_ok and tpr_ok,
    )


@lru_cache(maxsize=1)
def metrics_multi_signal() -> StrategyMetrics:
    far = multi_far()
    tpr = multi_tpr()
    far_ok = far <= _FAR_CEILING
    tpr_ok = tpr >= _TPR_FLOOR
    return StrategyMetrics(
        strategy=Strategy.MULTI_SIGNAL.value,
        false_activation_rate=far,
        true_case_recall=tpr,
        rule_complexity=2,
        allowed_count=multi_allowed(),
        blocked_count=multi_blocked(),
        architecture_roi=_architecture_roi(
            far, 2,
        ),
        far_ok=far_ok, tpr_ok=tpr_ok,
        qualifies=far_ok and tpr_ok,
    )


@lru_cache(maxsize=1)
def all_strategy_metrics() -> tuple[
    StrategyMetrics, ...,
]:
    return (
        metrics_no_precheck(),
        metrics_single_threshold(),
        metrics_multi_signal(),
    )


@lru_cache(maxsize=1)
def best_strategy() -> str:
    """Pick the simplest strategy that satisfies
    FAR <= ceiling and TPR >= floor. Ties on
    complexity break by higher architecture_roi.
    If no strategy qualifies, return
    ``BEST_STRATEGY_NONE``."""
    qualifying = [
        m for m in all_strategy_metrics()
        if m.qualifies
    ]
    if not qualifying:
        return "BEST_STRATEGY_NONE"
    qualifying.sort(
        key=lambda m: (
            m.rule_complexity,
            -m.architecture_roi,
            m.strategy,
        ),
    )
    return qualifying[0].strategy


def disqualified_strategies() -> tuple[str, ...]:
    return tuple(
        m.strategy
        for m in all_strategy_metrics()
        if not m.qualifies
    )


__all__ = [
    "STRATEGIES",
    "Strategy",
    "StrategyMetrics",
    "all_strategy_metrics",
    "best_strategy",
    "disqualified_strategies",
    "metrics_multi_signal",
    "metrics_no_precheck",
    "metrics_single_threshold",
]
