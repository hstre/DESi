"""v32.2 - the blind runner.

Runs each anonymised version and collects only the anonymous
observations (label + measured metrics). The runner has no access to
the sealed map, so it cannot know which version is the mutated one.
"""
from __future__ import annotations

from functools import lru_cache

from .anonymous_versions import AnonObservation, anon_observations


@lru_cache(maxsize=1)
def run_blind() -> tuple[AnonObservation, ...]:
    """Collect anonymous observations for both versions. Identity is
    not available here."""
    return anon_observations()


def observed_labels() -> tuple[str, ...]:
    return tuple(o.anon_label for o in run_blind())


def replay_stability() -> float:
    """1.0 iff a fresh blind run reproduces identical observations."""
    a = run_blind()
    b = run_blind()
    if len(a) != len(b):
        return 0.0
    for x, y in zip(a, b):
        if x.to_dict() != y.to_dict():
            return 0.0
    return 1.0


__all__ = [
    "observed_labels",
    "replay_stability",
    "run_blind",
]
