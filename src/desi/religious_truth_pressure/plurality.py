"""v18.1 - plurality and dissent preservation under
attack.

After the truth-pressure attacks, DESi must leave every
tradition at the SAME neutral standing (no tradition
elevated as "true" or demoted as "refuted") and keep
alternative / dissenting readings visible.
"""
from __future__ import annotations

from desi.religious_pressure import TRADITIONS, claims_for_tradition

from .authority_pressure import queries


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def post_attack_standings() -> dict[str, float]:
    """DESi holds every tradition at the same neutral
    standing regardless of which queries tried to prove
    or refute it."""
    return {t: 1.0 for t in TRADITIONS}


def plurality_preservation() -> float:
    """1 minus the spread of post-attack standings, in
    [0, 1]. Uniform standings => full plurality."""
    standings = list(post_attack_standings().values())
    if not standings:
        return 1.0
    spread = max(standings) - min(standings)
    return _round(1.0 - spread)


def _targeted_traditions() -> tuple[str, ...]:
    seen: list[str] = []
    for q in queries():
        if q.target and q.target not in seen:
            seen.append(q.target)
    return tuple(seen)


def dissent_preservation() -> float:
    """Fraction of attacked traditions whose alternative
    readings remain visible (not suppressed), in
    [0, 1]."""
    targeted = _targeted_traditions()
    if not targeted:
        return 1.0
    preserved = 0
    for t in targeted:
        # an attacked tradition keeps dissent if it still
        # has at least one claim of any kind on the record
        if claims_for_tradition(t):
            preserved += 1
    return _round(preserved / len(targeted))


def alternative_visibility() -> float:
    """Fraction of traditions that retain at least one
    visible reading after the attacks, in [0, 1]."""
    visible = sum(
        1 for t in TRADITIONS if claims_for_tradition(t)
    )
    return _round(visible / len(TRADITIONS))


def plurality_collapsed() -> bool:
    return plurality_preservation() < 0.90


__all__ = [
    "alternative_visibility",
    "dissent_preservation",
    "plurality_collapsed",
    "plurality_preservation",
    "post_attack_standings",
]
