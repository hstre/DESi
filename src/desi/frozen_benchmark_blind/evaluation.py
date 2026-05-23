"""v32.2 - the blind evaluation decision.

The evaluator ranks the anonymous observations by the measured
metric (lower recompute count is better) and names a blind winner -
all without any access to version identity. Only afterwards is the
sealed map used to verify that the blind winner happens to be the
mutated version.
"""
from __future__ import annotations

from .anonymous_versions import TRUE_MUTATED, sealed_map
from .blind_runner import run_blind


def blind_winner() -> str:
    """The anonymous label with the fewest recomputes."""
    return min(run_blind(), key=lambda o: o.recomputes).anon_label


def blind_ranking() -> tuple[str, ...]:
    """Anon labels ordered best (fewest recomputes) to worst."""
    return tuple(
        o.anon_label
        for o in sorted(run_blind(), key=lambda o: o.recomputes)
    )


def blind_winner_is_mutated() -> bool:
    """Post-hoc unsealing: is the blind winner the mutated version?
    The evaluation decision itself never used identity."""
    return sealed_map().get(blind_winner()) == TRUE_MUTATED


def margin() -> int:
    """Recompute margin between the worst and the best version."""
    recs = sorted(o.recomputes for o in run_blind())
    return recs[-1] - recs[0]


__all__ = [
    "blind_ranking",
    "blind_winner",
    "blind_winner_is_mutated",
    "margin",
]
