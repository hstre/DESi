"""v29.1 - deterministic render reuse.

A render cache that reuses a previously rendered output for an
identical render key. Reuse is exact (byte-identical); a render
is never approximated or rewritten. Demonstrates the render-reuse
half of the optimisation.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from desi.replay_cache_evolution import RecomputeCounter, rebuild


def render(key: str, work: int = 8000) -> str:
    """A deterministic render (real CPU work)."""
    return rebuild(f"render::{key}", work)


@dataclass
class RenderCache:
    _store: dict[str, str] = field(default_factory=dict)
    counter: RecomputeCounter = field(
        default_factory=RecomputeCounter,
    )

    def get_or_render(self, key: str, work: int = 8000) -> str:
        if key in self._store:
            self.counter.record_hit()
            return self._store[key]
        self.counter.record_miss()
        value = render(key, work)
        self._store[key] = value
        return value


def render_reuse_demo(
    keys: tuple[str, ...] = ("paper", "appendix", "paper"),
) -> tuple[RecomputeCounter, dict[str, str]]:
    """Render a sequence of keys; repeats reuse the cached render
    with identical output."""
    cache = RenderCache()
    out: dict[str, str] = {}
    for k in keys:
        out[k] = cache.get_or_render(k)
    return cache.counter, out


def render_reuse_is_exact() -> bool:
    """A reused render equals a fresh render of the same key."""
    cache = RenderCache()
    first = cache.get_or_render("paper")
    second = cache.get_or_render("paper")
    return first == second == render("paper")


__all__ = [
    "RenderCache",
    "render",
    "render_reuse_demo",
    "render_reuse_is_exact",
]
