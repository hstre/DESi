"""Plausible-Wrong-Slice (PWS) fixtures — the adversarial set the 80-case A–H benchmark lacks.

Motivation (and the honest gap it targets): the A–H benchmark's expected labels are partly
self-referential, and none of its cases is *plausible-wrong* — a slice that looks clean
(high confidence, full recall, no flags) yet omits a relevant branch the graph holds. This set is
exactly those traps, each tagged with the signal that SHOULD catch it, so the metric can report
``false_clean_rate`` honestly AND show what a single new signal (missing-opposition) does and does
NOT close.

Each case carries a slice that, taken alone, routes to a clean ``state_slice``/``normal`` with an
allowed update. The danger lives in ``graph_opposition`` (what a slice-independent full-graph scan
holds) and/or scope/provenance facts. ``detects_with`` names the deterministic check that resolves
it:

  * ``missing_opposition`` — graph holds a contradiction / superseding sibling / open question the
    slice omits. **Implemented now.**
  * ``provenance_entropy`` — many claims, one root source / all-derived. (next check, not yet built)
  * ``scope_match`` — correct claim, wrong scope / different entity. (next check, not yet built)

A handful of TRUE-CLEAN controls (``klass='CLEAN'``) measure the other half of the honest metric:
a real clean slice must NOT be escalated. Optimising detection alone is trivial (flag everything);
the pair (false_clean ↓, over_caution ↓) is the real target.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from desi_router.governance.report import DesiReport, report_from_snapshot


class _Snap:
    def __init__(self, conflicts=()):
        self.conflicts = tuple(type("C", (), {"id": c[0], "kind": c[1], "scope": c[2]})()
                               for c in conflicts)
        self.provenance = type("P", (), {"snapshot_hash": "pws"})()


@dataclass(frozen=True)
class PWSCase:
    id: str
    klass: str                          # 'PWS' (trap) | 'CLEAN' (control)
    desc: str
    inputs: dict                        # kwargs for report_from_snapshot (the clean-looking slice)
    graph_opposition: tuple = ()        # (id, text) the full-graph scan holds; '' text allowed
    conflicts: tuple = ()
    detects_with: str | None = None     # which check should resolve it (None for CLEAN controls)
    _r: Any = field(default=None, compare=False, repr=False)

    def report(self, *, aware: bool = True) -> DesiReport:
        """``aware=True`` feeds the graph scan in (the new path); ``aware=False`` reproduces the OLD
        router that never ran the scan — the contrast the metric uses to prove the signal moved it."""
        kw = dict(self.inputs)
        if aware and self.graph_opposition:
            kw["graph_opposition_ids"] = tuple(o[0] for o in self.graph_opposition)
            kw["graph_opposition_texts"] = tuple(o[1] for o in self.graph_opposition)
        return report_from_snapshot(self.id, _Snap(self.conflicts), **kw)


def _clean_slice(i, text):
    return dict(selected_claim_ids=(f"c{i}",), selected_claim_texts=(text,),
                extraction_confidence=0.95, state_recall_estimate=1.0)


def _build() -> list[PWSCase]:
    C: list[PWSCase] = []

    # PWS-01 · old claim, no invalid flag, but a newer sibling exists in the graph (superseded_by)
    C.append(PWSCase("PWS-01", "PWS", "old claim, not flagged, newer sibling exists",
                     inputs=_clean_slice(1, "deploy via the legacy blue-green script"),
                     graph_opposition=(("g_new1", "newer sibling: deploy via canary, replaces it"),),
                     detects_with="missing_opposition"))
    # PWS-02 · all-support slice, a known objection in the graph is omitted (contested_by)
    C.append(PWSCase("PWS-02", "PWS", "only the supporting side; known objection omitted",
                     inputs=_clean_slice(2, "the cache is safe to enable globally"),
                     graph_opposition=(("g_obj2", "objection: cache corrupts under concurrent write"),),
                     detects_with="missing_opposition"))
    # PWS-05 · correct local slice, a global conflict elsewhere touches the same subject (open_question)
    C.append(PWSCase("PWS-05", "PWS", "clean local slice, unresolved global conflict elsewhere",
                     inputs=_clean_slice(5, "region eu-west is the primary"),
                     graph_opposition=(("g_q5", "open question: primary region disputed after outage"),),
                     detects_with="missing_opposition"))
    # PWS-08 · previous user preference contradicted by a later claim the slice omits (contradicted_by)
    C.append(PWSCase("PWS-08", "PWS", "earlier preference contradicted by a later, omitted claim",
                     inputs=_clean_slice(8, "user prefers email notifications"),
                     graph_opposition=(("g_c8", "later: user disabled email, prefers push"),),
                     detects_with="missing_opposition"))

    # --- the subset missing-opposition CANNOT close (the graph holds no opposition node) ----------
    # PWS-03 · correct claim, wrong scope — needs scope_match, not opposition
    C.append(PWSCase("PWS-03", "PWS", "correct claim applied to the wrong scope",
                     inputs=_clean_slice(3, "rate limit is 1000/s") | dict(project_id="proj-A"),
                     detects_with="scope_match"))
    # PWS-04 · correct claim, stale provenance — needs provenance/age, not opposition
    C.append(PWSCase("PWS-04", "PWS", "correct claim, stale provenance (old import, new snapshot)",
                     inputs=_clean_slice(4, "the on-call rotation is team-X"),
                     detects_with="provenance_entropy"))
    # PWS-07 · derived chain hides a weak single root source — needs provenance entropy
    C.append(PWSCase("PWS-07", "PWS", "many derived claims, one weak root source",
                     inputs=dict(selected_claim_ids=("c7a", "c7b", "c7c"),
                                 selected_claim_texts=("derived A", "derived B", "derived C"),
                                 extraction_confidence=0.95, state_recall_estimate=1.0),
                     detects_with="provenance_entropy"))

    # --- TRUE-CLEAN controls: a real clean slice, the scan finds nothing -> must STAY clean --------
    for i in range(4):
        C.append(PWSCase(f"CLEAN-{i:02d}", "CLEAN", "genuinely clean slice, no omitted opposition",
                         inputs=_clean_slice(100 + i, f"settled fact {i}"),
                         detects_with=None))
    # a clean slice where the graph opposition IS already surfaced in the slice -> not omitted
    C.append(PWSCase("CLEAN-04", "CLEAN", "opposition exists but the slice already surfaced it",
                     inputs=dict(selected_claim_ids=("c200", "g_seen"),
                                 selected_claim_texts=("fact", "the counter-claim, included"),
                                 extraction_confidence=0.95, state_recall_estimate=1.0),
                     graph_opposition=(("g_seen", "counter-claim — but it is in the slice"),),
                     detects_with=None))
    return C


PWS_CASES: list[PWSCase] = _build()
