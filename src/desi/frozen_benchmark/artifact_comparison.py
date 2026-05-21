"""v32.1 - artifact identity between baseline and mutated.

The whole point of a replay-safe optimisation is that it changes the
recompute count WITHOUT changing any output. Artifact identity is
1.0 iff every per-workload output is byte-identical between the
frozen baseline and the mutated version.
"""
from __future__ import annotations

from .benchmark import mutated_run, outputs_identical
from desi.frozen_baseline import baseline_run


def per_workload_identity() -> dict[str, bool]:
    base = baseline_run().output_map()
    mut = mutated_run().output_map()
    names = sorted(set(base) | set(mut))
    return {n: base.get(n) == mut.get(n) for n in names}


def all_outputs_identical() -> bool:
    return outputs_identical()


def artifact_identity() -> float:
    """1.0 iff all outputs are byte-identical between versions."""
    ident = per_workload_identity()
    if not ident:
        return 0.0
    return 1.0 if all(ident.values()) else 0.0


__all__ = [
    "all_outputs_identical",
    "artifact_identity",
    "per_workload_identity",
]
