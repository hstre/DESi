"""v30.1 - risk ecology (observation only).

A deterministic view of how risk occurrences distribute across
the proposing agents and invariants. The ecology only observes;
it never feeds back into a policy, never blocks an idea, and
never changes governance.
"""
from __future__ import annotations

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .risk_memory import risk_occurrences
from .unsafe_patterns import auto_blocks_future_ideas


def risk_by_agent() -> dict[str, int]:
    out: dict[str, int] = {}
    for o in risk_occurrences():
        out[o.agent] = out.get(o.agent, 0) + 1
    return {k: out[k] for k in sorted(out)}


def risk_by_invariant() -> dict[str, int]:
    out: dict[str, int] = {}
    for o in risk_occurrences():
        out[o.invariant] = out.get(o.invariant, 0) + 1
    return {k: out[k] for k in sorted(out)}


def risks_are_descriptive_only() -> bool:
    """Risks are surfaced descriptively; no auto-blocking exists
    and human approval remains mandatory for any change."""
    return (not auto_blocks_future_ideas()) and HUMAN_APPROVAL_REQUIRED


def governance_neutrality() -> float:
    """1.0 iff risk memory neither auto-blocks future ideas nor
    alters governance - it only observes."""
    checks = [
        not auto_blocks_future_ideas(),
        risks_are_descriptive_only(),
        HUMAN_APPROVAL_REQUIRED,
    ]
    return round(sum(1 for c in checks if c) / len(checks), 6)


__all__ = [
    "governance_neutrality",
    "risk_by_agent",
    "risk_by_invariant",
    "risks_are_descriptive_only",
]
