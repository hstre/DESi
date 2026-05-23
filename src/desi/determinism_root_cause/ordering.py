"""v3.96b - ordering-dependency probe.

For each high-risk trace hit we ask: what would
fix it? The answer is one of a closed taxonomy:

* ``SORTED_KEYS``      - wrap the iterable in
  ``sorted(...)``.
* ``STABLE_HASH``      - replace the built-in
  ``hash()`` with a sha256-derived stable hash.
* ``EXPLICIT_ORDER``   - pin iteration over a
  closed tuple/list literal.
* ``JSON_SORT_KEYS``   - add ``sort_keys=True``
  to a ``json.dumps`` call.

The classifier reads the trace excerpt and
selects the appropriate fix kind. It is read-only
- the v3.96b sprint does not yet apply patches.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .trace import (
    TraceHit, all_trace_hits,
)


class OrderingFix(str, Enum):
    SORTED_KEYS    = "sorted_keys"
    STABLE_HASH    = "stable_hash"
    EXPLICIT_ORDER = "explicit_order"
    JSON_SORT_KEYS = "json_sort_keys"


@dataclass(frozen=True)
class OrderingClassification:
    path: str
    line_number: int
    kind: str
    excerpt: str
    suggested_fix: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "line_number": self.line_number,
            "kind": self.kind,
            "excerpt": self.excerpt,
            "suggested_fix": self.suggested_fix,
        }


def _suggested_fix(hit: TraceHit) -> str:
    if hit.kind == "builtin_hash":
        return OrderingFix.STABLE_HASH.value
    if hit.kind == "json_dumps_no_sort":
        return OrderingFix.JSON_SORT_KEYS.value
    if hit.kind == "dict_fromkeys":
        return OrderingFix.SORTED_KEYS.value
    if hit.kind == "raw_set_literal":
        return OrderingFix.SORTED_KEYS.value
    return OrderingFix.EXPLICIT_ORDER.value


def all_classifications() -> tuple[
    OrderingClassification, ...,
]:
    out: list[OrderingClassification] = []
    for h in all_trace_hits():
        out.append(OrderingClassification(
            path=h.path,
            line_number=h.line_number,
            kind=h.kind,
            excerpt=h.excerpt,
            suggested_fix=_suggested_fix(h),
        ))
    return tuple(out)


def unstable_functions() -> tuple[str, ...]:
    """Source locations whose ordering is
    classified as unstable (high-risk plus any
    ``json_dumps_no_sort`` hit)."""
    return tuple(sorted({
        f"{c.path}:{c.line_number}"
        for c in all_classifications()
        if c.suggested_fix in (
            OrderingFix.STABLE_HASH.value,
            OrderingFix.JSON_SORT_KEYS.value,
        )
    }))


__all__ = [
    "OrderingClassification",
    "OrderingFix",
    "all_classifications",
    "unstable_functions",
]
