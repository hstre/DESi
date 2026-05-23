"""v12.1 — exploration-redundancy compression.

Cluster the wild brother's hypotheses by their
detected EpistemicStatus and shape; redundant
within-cluster hypotheses are compressed into a
single canonical representative. The metric
``redundancy_reduction`` measures how much the
wild brother's output shrinks once compressed.
"""
from __future__ import annotations

from functools import lru_cache

from ..open_math.explorer import (
    fixture as wild_fixture,
)
from ..open_math.governance import (
    governed_hypotheses,
)


@lru_cache(maxsize=1)
def compressed_groups() -> tuple[
    tuple[str, tuple[str, ...]], ...,
]:
    """Group governed hypotheses by
    (detected_status, shape). Returns
    (group_key, member_ids) tuples sorted by
    group key."""
    by_key: dict[
        tuple[str, str], list[str],
    ] = {}
    for g in governed_hypotheses():
        key = (g.detected_status, g.shape)
        by_key.setdefault(key, []).append(
            g.hypothesis_id,
        )
    out: list[
        tuple[str, tuple[str, ...]],
    ] = []
    for (status, shape), members in sorted(
        by_key.items(),
    ):
        out.append((
            f"{status}|{shape}",
            tuple(sorted(members)),
        ))
    return tuple(out)


def compression_count() -> int:
    """Number of distinct (status, shape)
    groups after compression."""
    return len(compressed_groups())


def redundancy_reduction() -> float:
    """1 - groups / hypotheses. Higher means
    more compression. Clipped at 0."""
    raw = len(wild_fixture())
    grouped = compression_count()
    if raw <= 0:
        return 0.0
    return round(
        max(0.0, (raw - grouped) / raw),
        6,
    )


__all__ = [
    "compressed_groups",
    "compression_count",
    "redundancy_reduction",
]
