"""v3.108 — strategy scoring and ROI."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..t10_adaptive.adaptive import (
    ALL_CANDIDATES,
)
from ..t10_adaptive.search import (
    all_adaptive_outcomes,
)
from ..t10_inject.recover import (
    injected_auc as ge_injected_auc,
)
from .vocabulary import (
    ExpansionStrategy,
    strategy_dims,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _ge_auc_under(dims: tuple[str, ...]) -> float:
    """G/E AUC if the strategy uses
    contradiction_type; else the v3.99 baseline
    of 0.491."""
    if "contradiction_type" in dims:
        return ge_injected_auc()
    return 0.491


def recovery_score(strategy: str) -> float:
    """Mean AUC across G/E (v3.93) plus the
    v3.105 hidden entanglements, evaluating each
    instance under the candidate the strategy
    would select for it."""
    dims = set(strategy_dims(strategy))
    aucs: list[float] = []
    # G/E
    aucs.append(_ge_auc_under(tuple(sorted(dims))))
    # v3.107 instances
    for o in all_adaptive_outcomes():
        best = o.best_candidate
        if not best:
            aucs.append(o.baseline_auc)
            continue
        if strategy == (
            ExpansionStrategy
            .SINGLE_UNIVERSAL.value
        ):
            # No matching dim ⇒ baseline AUC
            aucs.append(0.5)
        elif strategy == (
            ExpansionStrategy.SMALL_VOCAB.value
        ):
            if best in dims:
                aucs.append(o.best_auc)
            else:
                aucs.append(0.5)
        else:  # CASE_SPECIFIC
            if best in dims:
                aucs.append(o.best_auc)
            else:
                aucs.append(o.baseline_auc)
    if not aucs:
        return 0.0
    return _round(sum(aucs) / len(aucs))


def complexity_score(strategy: str) -> float:
    """Fraction of the closed taxonomy used."""
    used = strategy_dims(strategy)
    total = len(ALL_CANDIDATES)
    if total <= 0:
        return 0.0
    return _round(len(used) / total)


def stability_score(strategy: str) -> float:
    """v3.103/v3.104a found 0 adverse flips for
    contradiction_type; the adaptive enrichments
    only fire on cross-family instances, so they
    introduce no plateau-anchor change.
    Stability is therefore 1.0 by construction
    for every strategy."""
    _ = strategy  # closed-shape invariant
    return 1.0


def architecture_roi(strategy: str) -> float:
    rec = recovery_score(strategy)
    cost = complexity_score(strategy)
    if cost <= 0.0:
        return 0.0
    return _round(rec / cost)


@dataclass(frozen=True)
class StrategyOutcome:
    strategy: str
    dims: tuple[str, ...]
    recovery_score: float
    complexity_score: float
    stability_score: float
    architecture_roi: float

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "dims": list(self.dims),
            "recovery_score":
                self.recovery_score,
            "complexity_score":
                self.complexity_score,
            "stability_score":
                self.stability_score,
            "architecture_roi":
                self.architecture_roi,
        }


@lru_cache(maxsize=1)
def all_strategy_outcomes() -> tuple[
    StrategyOutcome, ...,
]:
    out: list[StrategyOutcome] = []
    for s in ExpansionStrategy:
        out.append(StrategyOutcome(
            strategy=s.value,
            dims=strategy_dims(s.value),
            recovery_score=recovery_score(s.value),
            complexity_score=(
                complexity_score(s.value)
            ),
            stability_score=(
                stability_score(s.value)
            ),
            architecture_roi=(
                architecture_roi(s.value)
            ),
        ))
    return tuple(out)


_STRATEGY_PREFERENCE: dict[str, int] = {
    # When recovery + complexity tie, prefer
    # the simpler fixed alphabet over a
    # per-case lookup.
    "small_vocab":      2,
    "case_specific":    1,
    "single_universal": 0,
}


def best_strategy() -> StrategyOutcome:
    """Pick by (recovery_score desc,
    complexity_score asc, preference desc).

    Recovery wins over ROI because a strategy
    that barely rescues anything but is cheap
    would maximise ROI without solving the
    problem."""
    outs = all_strategy_outcomes()
    return max(
        outs,
        key=lambda s: (
            s.recovery_score,
            -s.complexity_score,
            _STRATEGY_PREFERENCE.get(
                s.strategy, 0,
            ),
        ),
    )


__all__ = [
    "StrategyOutcome",
    "all_strategy_outcomes",
    "architecture_roi",
    "best_strategy",
    "complexity_score",
    "recovery_score",
    "stability_score",
]
