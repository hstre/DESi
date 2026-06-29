"""CLSP fixtures + metrics — a deterministic benchmark for the cross-lingual probe's decision core.

Each case is an aligned cluster (what the LLM extraction+alignment would hand CLSP) plus the GOLD
category and whether it SHOULD be promotable. The discriminating metrics are:

  * ``false_candidate_rate`` — probe-only / artefact clusters wrongly promoted (the dangerous error:
    a translation hallucination entering the claim graph). MUST be 0.
  * ``anchor_rate``          — share of promoted candidates that are lead-anchored (invariant core).
  * ``overamp_detection``    — share of over-amplification traps caught.
  * ``category_accuracy``    — chosen category == gold.

The lead-language rule is the load-bearing invariant: nothing un-anchored may be promoted.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi_router.governance import clsp
from desi_router.governance.clsp import Cluster


@dataclass(frozen=True)
class CLSPCase:
    cluster: Cluster
    gold_category: str
    gold_promotable: bool


CASES: list[CLSPCase] = [
    # invariant core: stable across de+en+fr AND strongly anchored in the lead (de) source
    CLSPCase(Cluster("the method has unresolved risk", ("de", "en", "fr"), clsp.STRONG,
                     original_span="die Methode hat ungelöstes Risiko"),
             clsp.INVARIANT_CORE, True),
    # emergent: surfaced in en+fr, only weakly anchorable in the lead source -> verify, don't trust
    CLSPCase(Cluster("the issue may be methodological rather than factual", ("en", "fr"), clsp.WEAK),
             clsp.EMERGENT_CANDIDATE, True),
    # probe-only: a moral reading that appears only in fr and cannot be re-anchored in the lead text
    CLSPCase(Cluster("the author expresses moral criticism", ("fr",), clsp.NONE),
             clsp.PROBE_ONLY_CANDIDATE, False),
    # over-amplification: a hedged German original projected into a causal English claim
    CLSPCase(Cluster("this suggests a causal relationship", ("en",), clsp.WEAK,
                     original_span="könnte damit zusammenhängen",
                     projected_claim="this suggests a causal relationship"),
             clsp.OVERAMPLIFICATION_RISK, False),
    # over-amplification: hedged original -> normative/certain projection ("the method is invalid")
    CLSPCase(Cluster("the method is invalid", ("en",), clsp.WEAK,
                     original_span="nicht ganz unproblematisch",
                     projected_claim="the method is definitely invalid"),
             clsp.OVERAMPLIFICATION_RISK, False),
    # semantic loss: present (anchored) in the lead source but weakened/absent in the projections
    CLSPCase(Cluster("a weak warning is intended", ("en",), clsp.STRONG,
                     original_span="nicht ganz unproblematisch", lost_in_projection=True),
             clsp.SEMANTIC_LOSS, False),
    # invariant core control #2
    CLSPCase(Cluster("region eu-west is primary", ("de", "en"), clsp.STRONG,
                     original_span="Region eu-west ist primär"),
             clsp.INVARIANT_CORE, True),
]


def evaluate(cases: list[CLSPCase] | None = None) -> dict:
    cases = cases or CASES
    n = len(cases)
    cat_hits = 0
    promotable_disagree = 0
    false_candidates = 0          # NOT-promotable gold wrongly promoted
    promoted_anchored = promoted_total = 0
    overamp_caught = overamp_total = 0
    for c in cases:
        res = clsp.classify(c.cluster)
        cat_hits += (res.category == c.gold_category)
        promotable_disagree += (res.promotable != c.gold_promotable)
        if not c.gold_promotable and res.promotable:
            false_candidates += 1
        if res.promotable:
            promoted_total += 1
            promoted_anchored += (c.cluster.lead_anchor != clsp.NONE)   # the lead-language rule
        if c.gold_category == clsp.OVERAMPLIFICATION_RISK:
            overamp_total += 1
            overamp_caught += (res.category == clsp.OVERAMPLIFICATION_RISK)

    def rate(a, b):
        return round(a / b, 3) if b else None

    return {
        "n": n,
        "category_accuracy": rate(cat_hits, n),
        "false_candidate_rate": rate(false_candidates, n),
        "anchor_rate": rate(promoted_anchored, promoted_total),
        "overamp_detection": rate(overamp_caught, overamp_total),
        "promotable_disagreements": promotable_disagree,
    }
