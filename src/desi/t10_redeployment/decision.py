"""v3.116 — three closed redeployment strategies.

* ``CANONICAL_9D``       - keep the canonical
  StateVector unchanged. Recovery = 0 on the
  v3.105 entanglements (the v3.93 verdict
  stands).
* ``PROXY_ALPHABET``     - v3.108's three-dim
  alphabet (contradiction_type + corpus_hash +
  letter_prefix_hash). Recovery = 1.0 but two
  of three dims are proxies (v3.112).
* ``STRUCTURAL_ALPHABET`` - v3.115's best
  structural subset. Recovery = 0 per v3.115;
  zero proxy contamination but no rescue.

Each strategy is scored by
``(recovery_score, complexity_score,
proxy_score, historical_score)`` and an
``architecture_roi``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..t10_structural_vocab.vocab import (
    minimal_vocab_size as v3115_vocab_size,
    vocab_recovery as v3115_recovery,
)
from ..t10_verdict.verdict import (
    epistemic_dims, proxy_dims,
)


class RedeployStrategy(str, Enum):
    CANONICAL_9D        = "canonical_9d"
    PROXY_ALPHABET      = "proxy_alphabet"
    STRUCTURAL_ALPHABET = (
        "structural_alphabet"
    )


REDEPLOY_STRATEGIES: tuple[str, ...] = tuple(
    s.value for s in RedeployStrategy
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _recovery_score(strategy: str) -> float:
    if strategy == (
        RedeployStrategy.PROXY_ALPHABET.value
    ):
        return 1.0
    return 0.0


def _complexity_score(strategy: str) -> float:
    """Fraction of additional dims relative to
    canonical 9. 0 = no added cost; 1 = a full
    extra alphabet's worth."""
    if strategy == (
        RedeployStrategy.CANONICAL_9D.value
    ):
        return 0.0
    if strategy == (
        RedeployStrategy.PROXY_ALPHABET.value
    ):
        return _round(3 / 12)
    return _round(v3115_vocab_size() / 12)


def _proxy_score(strategy: str) -> float:
    """Fraction of strategy dims that are
    classified as PROXY. Lower is better."""
    if strategy == (
        RedeployStrategy.CANONICAL_9D.value
    ):
        return 0.0
    if strategy == (
        RedeployStrategy.PROXY_ALPHABET.value
    ):
        proxy = len(proxy_dims())
        total = (
            len(proxy_dims()) + len(epistemic_dims())
        )
        if total == 0:
            return 0.0
        return _round(proxy / total)
    # STRUCTURAL_ALPHABET: zero proxy contamination
    # by construction (every candidate is text-
    # independent of metadata).
    return 0.0


def _historical_score(strategy: str) -> float:
    """v3.103 / v3.104a found 0 adverse flips for
    contradiction_type; for any strategy the
    canonical historical sprints (mozart,
    plateau, leakage, etc.) are unchanged because
    none of them consult the +1 dim. Score is
    1.0 for every strategy."""
    _ = strategy
    return 1.0


@dataclass(frozen=True)
class StrategyOutcome:
    strategy: str
    dims: tuple[str, ...]
    recovery_score: float
    complexity_score: float
    proxy_score: float
    historical_score: float
    architecture_roi: float

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "dims": list(self.dims),
            "recovery_score":
                self.recovery_score,
            "complexity_score":
                self.complexity_score,
            "proxy_score": self.proxy_score,
            "historical_score":
                self.historical_score,
            "architecture_roi":
                self.architecture_roi,
        }


def _strategy_dims(strategy: str) -> tuple[str, ...]:
    if strategy == (
        RedeployStrategy.CANONICAL_9D.value
    ):
        return ()
    if strategy == (
        RedeployStrategy.PROXY_ALPHABET.value
    ):
        return (
            "contradiction_type",
            "corpus_hash",
            "letter_prefix_hash",
        )
    # STRUCTURAL_ALPHABET
    from ..t10_structural_vocab.search import (
        best_subset,
    )
    return tuple(best_subset().subset)


def _architecture_roi(strategy: str) -> float:
    rec = _recovery_score(strategy)
    cost = _complexity_score(strategy)
    proxy = _proxy_score(strategy)
    # ROI penalises proxy contamination: divide
    # recovery by (cost + proxy + epsilon).
    denom = cost + proxy + 0.01
    if denom <= 0.0:
        return 0.0
    return _round(rec / denom)


def all_strategy_outcomes() -> tuple[
    StrategyOutcome, ...,
]:
    return tuple(
        StrategyOutcome(
            strategy=s,
            dims=_strategy_dims(s),
            recovery_score=_recovery_score(s),
            complexity_score=_complexity_score(s),
            proxy_score=_proxy_score(s),
            historical_score=_historical_score(s),
            architecture_roi=_architecture_roi(s),
        )
        for s in REDEPLOY_STRATEGIES
    )


_STRATEGY_PREFERENCE: dict[str, int] = {
    # Prefer the proxy-free canonical 9D when
    # everything else ties; never the proxy
    # alphabet unless it strictly wins ROI.
    RedeployStrategy.CANONICAL_9D.value:       2,
    RedeployStrategy.STRUCTURAL_ALPHABET.value: 1,
    RedeployStrategy.PROXY_ALPHABET.value:      0,
}


def best_strategy() -> StrategyOutcome:
    outs = all_strategy_outcomes()
    return max(
        outs,
        key=lambda s: (
            s.architecture_roi,
            s.recovery_score,
            -s.complexity_score,
            -s.proxy_score,
            _STRATEGY_PREFERENCE.get(
                s.strategy, 0,
            ),
        ),
    )


__all__ = [
    "REDEPLOY_STRATEGIES",
    "RedeployStrategy",
    "StrategyOutcome",
    "all_strategy_outcomes",
    "best_strategy",
]
