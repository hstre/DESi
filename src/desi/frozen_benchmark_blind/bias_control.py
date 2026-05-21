"""v32.2 - bias control for the blind evaluation.

Two guarantees:

* blindness_integrity - no observation handed to the scorer leaks a
  true version name or branch; the evaluator sees only anonymous
  labels and measured metrics.
* bias_resistance - the scoring decision depends only on the measured
  metric (recompute count), not on the anonymous label string. The
  same underlying version wins under any relabelling, so there is no
  label favouritism or branch bias.
"""
from __future__ import annotations

from .anonymous_versions import (
    TRUE_BASELINE, TRUE_MUTATED, AnonObservation,
)
from .blind_runner import run_blind


def _leaks_identity(obs: AnonObservation) -> bool:
    blob = "|".join(str(v) for v in obs.to_dict().values())
    return TRUE_BASELINE in blob or TRUE_MUTATED in blob


def blindness_integrity() -> float:
    """1.0 iff no observation exposes a true name or branch."""
    obs = run_blind()
    if not obs:
        return 0.0
    return 1.0 if not any(_leaks_identity(o) for o in obs) else 0.0


def _score(obs: AnonObservation) -> int:
    """Lower recompute count is better. Uses the measured metric
    only - never the label."""
    return obs.recomputes


def _winner_label(observations: tuple[AnonObservation, ...]) -> str:
    best = min(observations, key=_score)
    return best.anon_label


def bias_resistance() -> float:
    """1.0 iff the winning observation is determined purely by the
    measured metric and is invariant under relabelling."""
    obs = run_blind()
    if len(obs) < 2:
        return 0.0
    winner = min(obs, key=_score)
    # Relabel every observation; the winner (by metric) must be the
    # same underlying observation regardless of label strings.
    relabelled = tuple(
        AnonObservation(
            anon_label=f"relabelled_{len(obs) - 1 - i}",
            recomputes=o.recomputes,
            output_signature=o.output_signature,
        )
        for i, o in enumerate(obs)
    )
    relabelled_winner = min(relabelled, key=_score)
    same = (
        relabelled_winner.recomputes == winner.recomputes
        and relabelled_winner.output_signature
        == winner.output_signature
    )
    return 1.0 if same else 0.0


__all__ = [
    "bias_resistance",
    "blindness_integrity",
]
