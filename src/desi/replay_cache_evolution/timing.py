"""v29.0 - recompute instrumentation.

The cost of a rebuild is measured deterministically as the number
of times the rebuild body actually executes (a cache miss). This
count is the reproducible, replay-stable cost proxy. Wall-clock
time is observable via `wall_clock` for live confirmation, but it
is never stored in an artifact (it is non-deterministic).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RecomputeCounter:
    misses: int = 0
    hits: int = 0

    def record_miss(self) -> None:
        self.misses += 1

    def record_hit(self) -> None:
        self.hits += 1

    def total(self) -> int:
        return self.misses + self.hits

    def to_dict(self) -> dict[str, int]:
        return {
            "misses": self.misses,
            "hits": self.hits,
            "total": self.total(),
        }


def wall_clock(fn, *args, **kwargs) -> tuple[object, float]:
    """Run fn and return (result, elapsed_seconds). For live
    confirmation only - the elapsed time is never persisted."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - start


__all__ = [
    "RecomputeCounter",
    "wall_clock",
]
