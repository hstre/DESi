"""v38.3 - governance router.

Routing changes only which model produces the observed evidence; it
never changes governance. Quality preservation checks that routing a
task to the cheaper model did not lose quality versus DeepSeek.
"""
from __future__ import annotations

from desi.live_llm_validation import governance_identity

from .routing_engine import routed_tasks


def quality_preservation() -> float:
    """Fraction of tasks where the routed model's quality is at least
    the DeepSeek quality (routing did not sacrifice quality)."""
    tasks = routed_tasks()
    if not tasks:
        return 0.0
    ok = sum(
        1 for t in tasks if t.routed_quality >= t.deepseek_quality
    )
    return round(ok / len(tasks), 6)


def governance_stability() -> float:
    return governance_identity()


__all__ = [
    "governance_stability",
    "quality_preservation",
]
