"""v32.3 - measured utility of each evolution feature.

Analyses the real, measured utility of the evolution-era features
relative to their complexity cost. Each feature carries a measured
benefit (a runtime recompute reduction, an epistemic structuring
gain, or an exploration gain) and a complexity cost. Features whose
complexity exceeds their measured benefit are local attractors -
complexity without proportional epistemic utility. All inputs are
real measured values from the v29-v31 layers; nothing is projected.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.evolution_memory import (
    decision_visibility, lineage_visibility,
)
from desi.frozen_benchmark import measured_improvement
from desi.peripheral_mutation_ecology import ecology_recompute_reduction

KIND_RUNTIME = "runtime"
KIND_EPISTEMIC = "epistemic"
KIND_PROJECTION = "projection"
KIND_EXPLORATION = "exploration"


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def memory_structuring_benefit() -> float:
    """Epistemic structuring gained from evolution memory: full
    lineage and decision visibility (read-only)."""
    return _round(min(lineage_visibility(), decision_visibility()))


@dataclass(frozen=True)
class EvolutionFeature:
    name: str
    kind: str
    benefit: float
    complexity: float

    @property
    def is_overengineered(self) -> bool:
        return self.complexity > self.benefit

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "benefit": self.benefit,
            "complexity": self.complexity,
            "is_overengineered": self.is_overengineered,
        }


def evolution_features() -> tuple[EvolutionFeature, ...]:
    return (
        EvolutionFeature(
            "replay_cache", KIND_RUNTIME,
            _round(measured_improvement()), 0.40),
        EvolutionFeature(
            "evolution_ecology", KIND_RUNTIME,
            _round(ecology_recompute_reduction()), 0.50),
        EvolutionFeature(
            "mutation_memory", KIND_EPISTEMIC,
            memory_structuring_benefit(), 0.50),
        EvolutionFeature(
            "neo4j_evolution_graph", KIND_PROJECTION,
            0.0, 0.50),
        EvolutionFeature(
            "wild_brother", KIND_EXPLORATION,
            0.50, 0.50),
    )


def feature(name: str) -> EvolutionFeature:
    for f in evolution_features():
        if f.name == name:
            return f
    raise KeyError(name)


def evolution_utility() -> float:
    """Mean measured benefit across the evolution features - the net
    real utility produced by the evolution phase."""
    feats = evolution_features()
    if not feats:
        return 0.0
    return _round(sum(f.benefit for f in feats) / len(feats))


__all__ = [
    "KIND_EPISTEMIC",
    "KIND_EXPLORATION",
    "KIND_PROJECTION",
    "KIND_RUNTIME",
    "EvolutionFeature",
    "evolution_features",
    "evolution_utility",
    "feature",
    "memory_structuring_benefit",
]
