"""v32.0 - the five baseline Pflichtmetriken in one place.

Collects the frozen-baseline metrics: identity, artifact identity,
governance identity, reproducibility and replay stability. Artifact
identity here means the baseline's output artifacts are byte-identical
across independent reconstructions.
"""
from __future__ import annotations

from .baseline_identity import (
    baseline_identity, governance_identity, output_signature,
)
from .baseline_restore import baseline_run
from .frozen_replay import baseline_reproducibility, replay_stability


def artifact_identity() -> float:
    """1.0 iff the baseline's output artifacts (per-workload output
    hashes) are byte-identical across independent reconstructions."""
    a = output_signature()
    b = output_signature()
    if a != b:
        return 0.0
    return 1.0 if baseline_run().outputs == baseline_run().outputs else 0.0


def baseline_metrics() -> dict[str, float]:
    return {
        "baseline_identity": baseline_identity(),
        "artifact_identity": artifact_identity(),
        "governance_identity": governance_identity(),
        "baseline_reproducibility": baseline_reproducibility(),
        "replay_stability": replay_stability(),
    }


__all__ = [
    "artifact_identity",
    "baseline_metrics",
]
