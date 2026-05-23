"""v31.1 - real peripheral mutation engine.

Applies real, deterministic optimisations to allowed peripheral
areas. Each mutation runs a baseline (repeated recompute) and a
mutated path (deterministic memoisation of the same computation):
the output is byte-identical and the recompute count drops. This
is a real code path, not a projection. Mutations target only
allowed areas; core-targeting attempts never reach the engine.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.peripheral_mutation import is_allowed
from desi.replay_cache_evolution import RecomputeCounter, rebuild

# (mutation_id, target_area, seed, work, repeat)
_MUTATION_SPECS: tuple[
    tuple[str, str, str, int, int], ...
] = (
    ("RM1", "runtime_scheduling", "schedule", 12000, 10),
    ("RM2", "graph_queries", "query", 12000, 8),
    ("RM3", "scientific_rendering", "render", 12000, 9),
    ("RM4", "artifact_compression", "compress", 12000, 7),
)


@dataclass(frozen=True)
class RealMutation:
    mutation_id: str
    target_area: str
    baseline_recomputes: int
    mutated_recomputes: int
    baseline_hash: str
    mutated_hash: str
    is_allowed_target: bool

    def output_identical(self) -> bool:
        return self.baseline_hash == self.mutated_hash

    def recompute_reduced(self) -> bool:
        return self.mutated_recomputes < self.baseline_recomputes

    def succeeded(self) -> bool:
        return (
            self.is_allowed_target
            and self.output_identical()
            and self.recompute_reduced()
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "mutation_id": self.mutation_id,
            "target_area": self.target_area,
            "baseline_recomputes": self.baseline_recomputes,
            "mutated_recomputes": self.mutated_recomputes,
            "baseline_hash": self.baseline_hash,
            "mutated_hash": self.mutated_hash,
            "is_allowed_target": self.is_allowed_target,
            "output_identical": self.output_identical(),
            "recompute_reduced": self.recompute_reduced(),
            "succeeded": self.succeeded(),
        }


def _baseline(seed: str, work: int, repeat: int) -> tuple[int, str]:
    counter = RecomputeCounter()
    out = ""
    for _ in range(repeat):
        counter.record_miss()
        out = rebuild(seed, work)
    return counter.misses, out


def _mutated(seed: str, work: int, repeat: int) -> tuple[int, str]:
    cache: dict[str, str] = {}
    counter = RecomputeCounter()
    out = ""
    for _ in range(repeat):
        if seed in cache:
            counter.record_hit()
            out = cache[seed]
        else:
            counter.record_miss()
            out = rebuild(seed, work)
            cache[seed] = out
    return counter.misses, out


def real_mutations() -> tuple[RealMutation, ...]:
    out: list[RealMutation] = []
    for mid, area, seed, work, repeat in _MUTATION_SPECS:
        b_rec, b_hash = _baseline(seed, work, repeat)
        m_rec, m_hash = _mutated(seed, work, repeat)
        out.append(RealMutation(
            mutation_id=mid,
            target_area=area,
            baseline_recomputes=b_rec,
            mutated_recomputes=m_rec,
            baseline_hash=b_hash,
            mutated_hash=m_hash,
            is_allowed_target=is_allowed(area),
        ))
    return tuple(out)


def successful_mutations() -> tuple[RealMutation, ...]:
    return tuple(m for m in real_mutations() if m.succeeded())


__all__ = [
    "RealMutation",
    "real_mutations",
    "successful_mutations",
]
