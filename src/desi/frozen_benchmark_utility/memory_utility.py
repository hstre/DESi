"""v32.3 - utility of the mutation / evolution memory.

The evolution memory does not reduce runtime; its utility is
epistemic - it makes mutation lineage, decisions and rejections
fully visible and traceable (read-only). Its utility is measured by
the real visibility metrics of the v30 evolution-memory layer.
"""
from __future__ import annotations

from desi.evolution_memory import (
    decision_visibility, evolution_traceability, lineage_visibility,
    rejection_visibility,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def memory_utility() -> float:
    """Epistemic utility of the evolution memory: the minimum of the
    lineage, decision, rejection and traceability visibilities."""
    return _round(min(
        lineage_visibility(), decision_visibility(),
        rejection_visibility(), evolution_traceability(),
    ))


def is_runtime_benefit() -> bool:
    """The evolution memory is a read-only epistemic structure; it
    provides no runtime recompute reduction."""
    return False


__all__ = [
    "is_runtime_benefit",
    "memory_utility",
]
