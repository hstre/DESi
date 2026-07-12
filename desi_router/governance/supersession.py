"""Deterministic supersession-distance check (#5) — the silent-staleness plausible-wrong signal.

A slice can be wrong because a claim was never *formally* invalidated but is *de facto* displaced: a
newer claim with the SAME scope (same topic / tenant / subject) exists, and the slice still uses the
old one. There is no contradiction edge and no supersede flag — only a newer sibling the slice omits.
That is invisible to the missing-opposition check (no opposition node) and to the status check (the
old claim is still 'active').

This turns it into a deterministic flag: given the same-scope claims the scan found to be NEWER than
a slice claim, what the slice omits is the silent-staleness signal. Against a live Layer-9 the newer
siblings come from a same-topic/same-scope lookup ordered by tick; in the benchmark they are a fixture
input. Degrades to caution, never blocks; an empty set means the scan found no newer sibling.
"""
from __future__ import annotations

from collections.abc import Iterable


def omitted_newer_siblings(surfaced_ids: Iterable[str],
                           newer_sibling_ids: Iterable[str]) -> tuple[str, ...]:
    """Same-scope NEWER claims the slice did not surface — the de-facto-displaced-but-unflagged set.
    Order-stable, de-duped. Empty when the scan found no newer sibling (then the slice is current)."""
    surfaced = {s for s in surfaced_ids if s}
    out: dict[str, None] = {}
    for sib in newer_sibling_ids:
        if sib and sib not in surfaced:
            out[sib] = None
    return tuple(out)
