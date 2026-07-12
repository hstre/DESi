"""Deterministic 'missing-opposition' check — the plausible-wrong-slice signal.

A state slice is dangerous not when it contains a *false* claim, but when it carries only the
**supporting** side: the graph KNOWS an objection / superseding sibling / contradicting evidence /
unresolved question for a selected claim, and the slice omits it. The slice then looks coherent and
high-confidence while a relevant branch is absent — exactly the Phase-2 ``signaled vs unsignaled``
blind spot.

This module turns that into a deterministic structural flag. It is **slice-independent on purpose**:
the inputs are (a) what the slice surfaced and (b) what a full-graph adjacency scan found — NOT the
slice's own self-assessment. In the governance benchmark the scan result is a fixture input; against
a live Layer-9 it comes from graph traversal (in-links of type ``contradicts`` / ``supersedes`` /
``invalidates`` plus open questions touching the selected claims — e.g. ``layer9_v2.graph.traversal``
``contradicting`` / ``walk``). Either way the decision stays deterministic; no LLM judge.

Honest scope: this catches the *opposition-omission* family (a known objection / newer sibling /
global conflict the slice left out). It does NOT catch a wrong-scope or stale-provenance slice whose
opposition the graph does not hold — those need the scope-match and provenance-entropy checks, which
are separate signals. The benchmark reports that split rather than hiding it.
"""
from __future__ import annotations

from collections.abc import Iterable

# Opposition relation classes the scan distinguishes — also the deterministic attack-vector labels
# an anti-delphi pass would search for (the LLM may PROPOSE which to look for; this code decides).
OPPOSITION_CLASSES = (
    "contested_by", "superseded_by", "contradicted_by", "open_question", "same_scope_newer",
)


def omitted_opposition(surfaced_ids: Iterable[str],
                       graph_opposition_ids: Iterable[str]) -> tuple[str, ...]:
    """Opposition node-ids the graph holds that the slice did NOT surface. Order-stable, de-duped.

    ``surfaced_ids`` = everything the slice already put in front of the router (selected claims +
    whatever it flagged as invalidated/superseded/open-conflict). ``graph_opposition_ids`` = the
    opposition the full-graph scan found for the selected claims. The difference is the danger.
    """
    surfaced = {s for s in surfaced_ids if s}
    out: dict[str, None] = {}
    for o in graph_opposition_ids:
        if o and o not in surfaced:
            out[o] = None
    return tuple(out)


def partition_omitted(surfaced_ids: Iterable[str],
                      graph_opposition: Iterable[tuple[str, str]]) -> dict[str, tuple[str, ...]]:
    """Same as :func:`omitted_opposition` but keeps the per-class breakdown for reporting / the
    anti-delphi attack vectors. ``graph_opposition`` is ``(id, klass)`` pairs."""
    surfaced = {s for s in surfaced_ids if s}
    by_class: dict[str, dict[str, None]] = {}
    for oid, klass in graph_opposition:
        if oid and oid not in surfaced:
            by_class.setdefault(klass, {})[oid] = None
    return {k: tuple(v) for k, v in by_class.items()}
