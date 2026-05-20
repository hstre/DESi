"""v23.1 - explicit sandbox limits.

States, in plain terms, what the synthetic environment is and
is not. Without these statements the numbers could read like
benchmark results from a real RL system; with them every
result stays scoped to the sandbox.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxLimit:
    limit_id: str
    statement: str

    def to_dict(self) -> dict[str, object]:
        return {"limit_id": self.limit_id, "statement": self.statement}


_LIMITS: tuple[SandboxLimit, ...] = (
    SandboxLimit(
        "L1",
        "All trajectories, states and rewards are synthetic "
        "fixtures, not collected from a real environment or a "
        "trained policy."),
    SandboxLimit(
        "L2",
        "The action space and state space are small, closed "
        "and enumerated; they do not approximate a real "
        "variable-action ICRL setting at scale."),
    SandboxLimit(
        "L3",
        "Every number is computed by deterministic arithmetic "
        "over the fixtures (no PRNG, no learned model), so the "
        "values describe the fixtures and not external "
        "performance."),
    SandboxLimit(
        "L4",
        "The Wild Explorer and the governor are rule-based "
        "stand-ins; they illustrate a governance interaction, "
        "they are not the agents of the base paper."),
    SandboxLimit(
        "L5",
        "Results are reported only relative to the DESi-only "
        "baseline within this sandbox; no claim is made about "
        "absolute exploration quality outside it."),
)


def sandbox_limits() -> tuple[SandboxLimit, ...]:
    return _LIMITS


def sandbox_limit_ids() -> tuple[str, ...]:
    return tuple(l.limit_id for l in _LIMITS)


def sandbox_honesty() -> bool:
    """True iff the mandatory sandbox limits are all present
    and non-empty - the conditions are made visible."""
    required = {"L1", "L2", "L3", "L4", "L5"}
    present = {
        l.limit_id for l in _LIMITS if l.statement.strip()
    }
    return required.issubset(present)


__all__ = [
    "SandboxLimit",
    "sandbox_honesty",
    "sandbox_limit_ids",
    "sandbox_limits",
]
