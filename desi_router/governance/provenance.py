"""Deterministic provenance-entropy check — the thin-support plausible-wrong-slice signal.

A slice can be plausible-wrong without containing any false claim and without any omitted opposition:
it consists of many claims that all trace back to **one** root source, an old import, or are entirely
*derived* (no primary evidence). It looks well-supported (many nodes) while resting on a single,
possibly weak or stale foundation — no independent confirmation.

This turns that into a deterministic structural flag from provenance facts only (root-source family
per claim, derived-vs-primary, staleness). No LLM. Against a live Layer-9 the source family comes
from the same key Joni already uses to collapse same-origin claims (``_source_family``); derived/
primary from the claim's origin type; staleness from provenance age vs the snapshot.

Honest scope: this flags *under-support* (thin/old/all-derived provenance). It does NOT judge whether
a well-sourced claim is true — that is not a provenance question. It degrades to caution, never blocks.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence


def assess_provenance(*, n_claims: int, source_families: Sequence[str] = (),
                      derived_flags: Iterable[bool] = (), stale: bool = False) -> dict:
    """Return a deterministic provenance assessment for a slice.

    ``under_support`` is True when the slice is plausibly thin: ≥2 claims resting on ≤1 independent
    root source, OR every claim is derived (no primary), OR the provenance is stale. Each reason is
    reported so the router (and an audit) can see *why*.
    """
    families = [f for f in source_families if f]
    independent = len(set(families))
    derived = [bool(d) for d in derived_flags]
    all_derived = bool(n_claims and derived and len(derived) == n_claims and all(derived))
    derived_ratio = (sum(derived) / n_claims) if n_claims else 0.0

    # only flag thinness when source info is actually PRESENT and collapses to one root; absence of
    # provenance info (independent == 0) is "unknown", which must NOT masquerade as a thin-source flag.
    thin_sources = bool(n_claims >= 2 and 0 < independent <= 1)
    reasons = []
    if thin_sources:
        reasons.append("many_claims_one_root_source")
    if all_derived:
        reasons.append("all_derived_no_primary")
    if stale:
        reasons.append("stale_provenance")
    under = bool(reasons)
    return {
        "independent_sources": independent,
        "derived_ratio": round(derived_ratio, 3),
        "all_derived": all_derived,
        "stale": bool(stale),
        "under_support": under,
        "reasons": tuple(reasons),
    }
