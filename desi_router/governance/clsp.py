"""CLSP — Cross-Lingual Semantic Probe (the deterministic decision core).

Multilingual projection is a *probe*, never an authority: re-expressing a text in other languages
forces different semantic cuts and can surface weak signal the lead-language read missed. But it can
just as easily hallucinate — a hedge becomes a causal claim, an understatement becomes a verdict. So
the rule is fixed:

    The author's primary (lead) language is the semantic authority. Every cross-lingual projection is
    a probe channel. A claim found only in a probe language stays a CANDIDATE — it may not enter the
    EIR/claim graph until it can be re-anchored in the lead-language source.

The LLM does the language work (translate, extract claims per language, align "the same claim" across
languages into a cluster) and proposes candidates. THIS module is deterministic: given the aligned
clusters + the lead-language anchor, it classifies each, detects over-amplification, and gates which
candidates may be promoted. No LLM in the decision path — replay-stable and unit-testable, exactly
like ``modes.select_mode``. ``Layer 9 decides; lead language anchors.``
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# The six categories a cross-lingual candidate can fall into (spec §CLSP-Kategorien).
INVARIANT_CORE = "invariant_core"               # stable across langs AND anchored in the lead source
EMERGENT_CANDIDATE = "emergent_candidate"       # appears via projection, weak lead anchor -> verify
PROBE_ONLY_CANDIDATE = "probe_only_candidate"   # only in probe langs, NOT anchorable in the lead text
TRANSLATION_ARTIFACT = "translation_artifact"   # likely an artefact of translation / over-reading
SEMANTIC_LOSS = "semantic_loss"                 # present in the lead text, lost/weakened in projection
OVERAMPLIFICATION_RISK = "overamplification_risk"  # a vague original became precise/causal/normative
CATEGORIES = (INVARIANT_CORE, EMERGENT_CANDIDATE, PROBE_ONLY_CANDIDATE, TRANSLATION_ARTIFACT,
              SEMANTIC_LOSS, OVERAMPLIFICATION_RISK)

# Anchor strength of a candidate against the lead-language source (supplied by the aligner).
STRONG, WEAK, NONE = "strong", "weak", "none"

# Strength markers that a projection must NOT add over a hedged original (bilingual; a lexical proxy —
# extensible, deliberately deterministic, never a learned classifier in the hard path).
_CAUSAL = re.compile(r"\b(causes?|because|leads? to|results? in|due to|causal|verursacht|"
                     r"führt zu|deshalb|daher)\b", re.I)
_NORMATIVE = re.compile(r"\b(must|should|ought|have to|required|muss|sollte|müssen)\b", re.I)
_CERTAINTY = re.compile(r"\b(proves?|definitely|certainly|clearly|invalid|impossible|beweist|"
                        r"eindeutig|sicher|unmöglich)\b", re.I)
_HEDGE = re.compile(r"\b(might|may|could|possibly|perhaps|suggests?|seems?|appears?|tends? to|"
                    r"kann|könnte|vielleicht|möglicherweise|scheint|deutet)\b", re.I)
# Litotes / understatement — a hedge by double-negation, NOT by a hedge word, so the lexicon above
# misses it. This is exactly the "German understatement / weak warning" signal the proposal flags
# ("nicht ganz unproblematisch"). Caught structurally: nicht/not + (optional) ganz + un-word, or
# nicht/not + ohne/without.
_LITOTES = re.compile(r"\bnicht\s+(ganz\s+)?un\w+|\bnot\s+un\w+|\bnicht\s+ohne\b|\bnot\s+without\b",
                      re.I)


def _hedged(text: str) -> bool:
    return bool(_HEDGE.search(text) or _LITOTES.search(text))


def _has_strength(text: str) -> bool:
    return bool(_CAUSAL.search(text) or _NORMATIVE.search(text) or _CERTAINTY.search(text))


def overamplification(original_span: str, projected_claim: str) -> bool:
    """True when a HEDGED original was projected into a STRONGER claim — a causal/normative/certainty
    marker appears in the projection that the (hedged) original did not carry. Deterministic."""
    orig_hedged = _hedged(original_span or "") and not _has_strength(original_span or "")
    proj_strong = _has_strength(projected_claim or "")
    return orig_hedged and proj_strong


@dataclass(frozen=True)
class Cluster:
    """One aligned cross-lingual claim, as produced by the (LLM) extraction+alignment step."""
    claim: str
    languages: tuple[str, ...]                   # probe languages the claim surfaced in
    lead_anchor: str = NONE                      # STRONG | WEAK | NONE — anchorability in the lead text
    original_span: str = ""                      # the lead-language span (for over-amplification)
    projected_claim: str = ""                    # the probe-language projection (for over-amplification)
    lost_in_projection: bool = False             # present in lead, weakened/absent in probes


@dataclass
class CLSPResult:
    category: str
    promotable: bool                             # may it enter EIR at all?
    status: str                                  # candidate_for_eir | requires_verifier | probe_only | rejected
    reason: str


def classify(c: Cluster) -> CLSPResult:
    """Deterministically classify one cluster and decide its promotion status. The lead-language rule
    is enforced here: no probe-only claim is promotable, and an over-amplified projection is an
    artefact, never a claim."""
    if overamplification(c.original_span, c.projected_claim):
        return CLSPResult(OVERAMPLIFICATION_RISK, False, "rejected",
                          "hedged original projected into a stronger (causal/normative/certain) claim")
    if c.lost_in_projection and c.lead_anchor != NONE:
        return CLSPResult(SEMANTIC_LOSS, False, "rejected",
                          "present in the lead source but weakened/lost in projection")
    if c.lead_anchor == STRONG and len(c.languages) >= 2:
        return CLSPResult(INVARIANT_CORE, True, "candidate_for_eir",
                          "stable across languages and anchored in the lead source")
    if c.lead_anchor in (STRONG, WEAK):
        return CLSPResult(EMERGENT_CANDIDATE, True, "requires_verifier",
                          "plausibly present in the lead source; verify before trusting")
    return CLSPResult(PROBE_ONLY_CANDIDATE, False, "probe_only",
                      "found only in a probe language; cannot be re-anchored in the lead source")


def to_eir_candidates(clusters: list[Cluster]) -> dict:
    """Run every cluster through :func:`classify` and split into what may enter the EIR vs what stays a
    probe-only candidate or is rejected. NO silent promotion: every cluster carries its category +
    reason. Returns the promotable candidates (with their status) and an audit of the rest."""
    rows = [(c, classify(c)) for c in clusters]
    promote = [{"claim": c.claim, "status": r.status, "category": r.category,
                "languages": list(c.languages)} for c, r in rows if r.promotable]
    held = [{"claim": c.claim, "category": r.category, "reason": r.reason} for c, r in rows
            if not r.promotable]
    return {"promote": promote, "held": held,
            "by_category": _counts(r.category for _, r in rows)}


def _counts(cats) -> dict:
    out: dict = {}
    for c in cats:
        out[c] = out.get(c, 0) + 1
    return out


def to_report_inputs(clusters: list[Cluster]) -> dict:
    """Bridge CLSP → EIR: turn the promotable candidates into ``report_from_snapshot`` kwargs, so the
    cross-lingual findings flow through the SAME deterministic gate as any other claim. The lead-
    language rule is preserved end-to-end: probe-only / artefact / loss clusters never become selected
    claims. If any promoted candidate is only WEAKLY anchored (emergent), the slice's extraction
    confidence is lowered so ``select_mode`` requires a verifier before the answer may propose
    anything; an all-``invariant_core`` slice (strong, multilingual, anchored) is trusted.

    Usage::

        rep = report_from_snapshot(task_id, snapshot, **clsp.to_report_inputs(clusters))
        decision = select_mode(rep)        # CLSP candidates now gated like everything else
    """
    usable = [(c, r) for c in clusters for r in (classify(c),) if r.promotable]
    ids = tuple(f"clsp-{i}" for i, _ in enumerate(usable))
    texts = tuple(c.claim for c, _ in usable)
    has_emergent = any(r.category == EMERGENT_CANDIDATE for _, r in usable)
    return {
        "selected_claim_ids": ids,
        "selected_claim_texts": texts,
        # weak (emergent) anchoring -> low extraction confidence -> the router gates to verify/guard.
        "extraction_confidence": 0.4 if has_emergent else 0.9,
        "state_recall_estimate": 1.0,
    }
