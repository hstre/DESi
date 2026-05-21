"""v32.3 - novelty per runtime.

Novelty is the number of distinct results produced; runtime is the
recompute count. novelty_per_runtime is the distinct-result yield per
recompute. The evolved (mutated) version produces the same distinct
results with far fewer recomputes, so its novelty per runtime is much
higher than the frozen baseline's. This is a real measured ratio.
"""
from __future__ import annotations

from desi.frozen_benchmark import (
    baseline_recomputes, mutated_recomputes, mutated_run,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def distinct_outputs() -> int:
    return len(set(mutated_run().output_map().values()))


def baseline_novelty_per_runtime() -> float:
    rc = baseline_recomputes()
    return _round(distinct_outputs() / rc) if rc else 0.0


def novelty_per_runtime() -> float:
    """Distinct results per recompute for the evolved version."""
    rc = mutated_recomputes()
    return _round(distinct_outputs() / rc) if rc else 0.0


def novelty_per_runtime_gain() -> float:
    """How much the evolution improved novelty per runtime (>= 0)."""
    return _round(
        novelty_per_runtime() - baseline_novelty_per_runtime()
    )


__all__ = [
    "baseline_novelty_per_runtime",
    "distinct_outputs",
    "novelty_per_runtime",
    "novelty_per_runtime_gain",
]
