"""v3.96b - container-type classifier.

Groups trace hits by the kind of container they
touch:

* ``hash_call``    - Python's built-in randomized
  hash applied to a string.
* ``set_literal``  - set() constructor.
* ``dict_fromkeys`` - dict-as-ordered-set.
* ``json_dumps``    - JSON serialization, possibly
  without sort_keys.

The classifier is read-only.
"""
from __future__ import annotations

from collections import Counter

from .trace import all_trace_hits


def container_kind_counts() -> dict[str, int]:
    counts: Counter[str] = Counter()
    for h in all_trace_hits():
        counts[h.kind] += 1
    return dict(counts)


def unstable_container_kinds() -> tuple[str, ...]:
    """Kinds present in the trace AND classified
    as high-risk (i.e., would actually cause
    seed-dependent output)."""
    from .trace import is_high_risk
    return tuple(sorted({
        h.kind for h in all_trace_hits()
        if is_high_risk(h.kind)
    }))


def total_hit_count() -> int:
    return len(all_trace_hits())


def high_risk_hit_count() -> int:
    from .trace import is_high_risk
    return sum(
        1 for h in all_trace_hits()
        if is_high_risk(h.kind)
    )


__all__ = [
    "container_kind_counts",
    "high_risk_hit_count",
    "total_hit_count",
    "unstable_container_kinds",
]
