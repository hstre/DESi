"""v16.2 - speculation-chain visibility.

DESi makes every speculation chain visible: each
node carries its attempted standing, the evidence
grade, and the gap. Nothing in a chain is hidden or
silently accepted.
"""
from __future__ import annotations

from .escalation import chains, nodes


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def speculation_chains() -> tuple[dict, ...]:
    return tuple(ch.to_dict() for ch in chains())


def chain_lengths() -> dict[str, int]:
    return {
        ch.chain_id: len(ch.nodes) for ch in chains()
    }


def all_chains_visible() -> bool:
    """Every escalation node is exposed with its gap
    - no node is suppressed or accepted silently."""
    return all(
        n.escalation_gap() >= 0 for n in nodes()
    )


def visible_escalation_count() -> int:
    return sum(1 for n in nodes() if n.is_escalation())


__all__ = [
    "all_chains_visible",
    "chain_lengths",
    "speculation_chains",
    "visible_escalation_count",
]
