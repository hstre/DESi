"""Plausible-Wrong-Slice (PWS) fixtures — the adversarial set the 80-case A–H benchmark lacks.

Motivation (and the honest gap it targets): the A–H expected labels are partly self-referential, and
none of its cases is *plausible-wrong* — a slice that looks clean (high confidence, full recall, no
flags) yet is one-sided, under-supported, or out of scope. This set is exactly those traps, each
tagged with the deterministic check that SHOULD catch it, so ``false_clean_rate`` is reported per
subset and shows what each new signal does — and does not — close.

Each case has a ``slice`` (the clean-looking base, always present) and ``signals`` (the facts a
slice-INDEPENDENT scan would add). ``report(aware=False)`` omits the signals — the prior router that
never ran the scans — so the metric movement is attributable to the signals, not to caution. The
``detects_with`` tag names the responsible check:

  * ``missing_opposition`` — graph holds a contradiction / superseding sibling / open question the
    slice omits.
  * ``provenance_entropy`` — many claims on one root source / all-derived / stale.
  * ``scope_match`` — a correct claim applied out of scope.

TRUE-CLEAN controls (``klass='CLEAN'``) measure the other half of the honest pair: a real clean slice
must NOT be escalated. Optimising detection alone is trivial; (false_clean ↓, over_caution ↓) is the target.
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
    slice: dict                         # the clean-looking slice (always fed)
    signals: dict = field(default_factory=dict)   # scan-derived inputs (fed only when aware)
    conflicts: tuple = ()
    detects_with: str | None = None
    _r: Any = field(default=None, compare=False, repr=False)

    def report(self, *, aware: bool = True) -> DesiReport:
        kw = dict(self.slice)
        if aware:
            kw.update(self.signals)
        return report_from_snapshot(self.id, _Snap(self.conflicts), **kw)


def _clean(i, text, **extra):
    return dict(selected_claim_ids=(f"c{i}",), selected_claim_texts=(text,),
                extraction_confidence=0.95, state_recall_estimate=1.0, **extra)


def _build() -> list[PWSCase]:
    C: list[PWSCase] = []

    # === missing_opposition subset: the graph holds opposition the slice omits ===================
    C.append(PWSCase("PWS-01", "PWS", "old claim, not flagged, newer sibling exists",
                     slice=_clean(1, "deploy via the legacy blue-green script"),
                     signals=dict(graph_opposition_ids=("g_new1",),
                                  graph_opposition_texts=("newer sibling: deploy via canary",)),
                     detects_with="missing_opposition"))
    C.append(PWSCase("PWS-02", "PWS", "only the supporting side; known objection omitted",
                     slice=_clean(2, "the cache is safe to enable globally"),
                     signals=dict(graph_opposition_ids=("g_obj2",),
                                  graph_opposition_texts=("objection: cache corrupts on concurrent write",)),
                     detects_with="missing_opposition"))
    C.append(PWSCase("PWS-05", "PWS", "clean local slice, unresolved global conflict elsewhere",
                     slice=_clean(5, "region eu-west is the primary"),
                     signals=dict(graph_opposition_ids=("g_q5",),
                                  graph_opposition_texts=("open question: primary region disputed",)),
                     detects_with="missing_opposition"))
    C.append(PWSCase("PWS-08", "PWS", "earlier preference contradicted by a later, omitted claim",
                     slice=_clean(8, "user prefers email notifications"),
                     signals=dict(graph_opposition_ids=("g_c8",),
                                  graph_opposition_texts=("later: user disabled email, prefers push",)),
                     detects_with="missing_opposition"))

    # === provenance_entropy subset: thin / stale / all-derived support ==========================
    C.append(PWSCase("PWS-04", "PWS", "correct claim, stale provenance",
                     slice=_clean(4, "the on-call rotation is team-X"),
                     signals=dict(provenance_sources=("src-old",), provenance_stale=True),
                     detects_with="provenance_entropy"))
    C.append(PWSCase("PWS-07", "PWS", "many derived claims, one weak root source",
                     slice=dict(selected_claim_ids=("c7a", "c7b", "c7c"),
                                selected_claim_texts=("derived A", "derived B", "derived C"),
                                extraction_confidence=0.95, state_recall_estimate=1.0),
                     signals=dict(provenance_sources=("root1", "root1", "root1"),
                                  derived_flags=(True, True, True)),
                     detects_with="provenance_entropy"))

    # === scope_match subset: correct claim, wrong scope =========================================
    C.append(PWSCase("PWS-03", "PWS", "correct claim applied to the wrong scope",
                     slice=_clean(3, "rate limit is 1000/s"),
                     signals=dict(task_scope="proj-A", claim_scopes=("proj-B",)),
                     detects_with="scope_match"))

    # === TRUE-CLEAN controls: a real clean slice, scans find nothing -> must STAY clean ==========
    for i in range(4):
        C.append(PWSCase(f"CLEAN-{i:02d}", "CLEAN", "genuinely clean slice",
                         slice=_clean(100 + i, f"settled fact {i}"),
                         signals=dict(provenance_sources=(f"src-{i}",), task_scope="proj-A",
                                      claim_scopes=("proj-A",)),   # well-sourced, in scope
                         detects_with=None))
    # opposition exists but the slice already surfaced it -> not omitted -> still clean
    C.append(PWSCase("CLEAN-04", "CLEAN", "opposition exists but already surfaced in the slice",
                     slice=dict(selected_claim_ids=("c200", "g_seen"),
                                selected_claim_texts=("fact", "the counter-claim, included"),
                                extraction_confidence=0.95, state_recall_estimate=1.0),
                     signals=dict(graph_opposition_ids=("g_seen",)),
                     detects_with=None))
    return C


PWS_CASES: list[PWSCase] = _build()
