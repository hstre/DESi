"""v9.3 — institutional-capture detection."""
from __future__ import annotations

from .pressure_ecology import trajectory


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def captured_actor_share() -> float:
    """Of the ACTOR_ECOLOGY steps, the fraction
    whose detected verdict ended up assigning
    HIGH trust to a strategic actor (PROPAGANDIST
    or REPLAY_ATTACKER). Should be 0."""
    actor_steps = [
        s for s in trajectory()
        if s.stream == "actor_ecology"
    ]
    if not actor_steps:
        return 0.0
    bad = sum(
        1 for s in actor_steps
        if s.trust >= 0.90
        and s.verdict in {
            "propagandist",
            "replay_attacker",
        }
    )
    return _round(bad / len(actor_steps))


def gaming_let_through_share() -> float:
    """Fraction of GAMING steps that exited with
    HIGH trust despite the verdict being a
    gaming kind."""
    gaming_steps = [
        s for s in trajectory()
        if s.stream == "gaming"
    ]
    if not gaming_steps:
        return 0.0
    bad = sum(
        1 for s in gaming_steps
        if s.trust >= 0.90
        and s.verdict not in {"normal"}
    )
    return _round(bad / len(gaming_steps))


__all__ = [
    "captured_actor_share",
    "gaming_let_through_share",
]
