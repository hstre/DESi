#!/usr/bin/env python3
"""SPL semantic alignment layer (P17) — cross-model claim alignment for DBA.

Problem from P16: granularity/grouping differences between two independent
builders produced missing_claim / extra_claim / branch_required even when both
reconstructed the SAME semantic region. P17 adds an alignment layer that asks
"do these two reconstructions cover the same meaning-region?" instead of "are the
claims string-identical?", and re-characterises the DBA outcome accordingly.

It REUSES spl_core (no new parallel SPL): every claim is projected through
spl_core.project_atomic_claim into a CanonicalClaimCandidate (canonical s/p/o +
projection entropy + emission rule), and alignment is computed over those
canonical forms plus the spl_core projection signals.

Alignment types (NOT truth labels): semantic_isomorph, granularity_overlap,
semantic_overlap, partial_overlap, projection_neighbor, structurally_divergent.

HONEST SCOPE: spl_core's "semantic projection" is a confidence-shaped entropy over
a synthetic relation distribution, NOT a learned meaning embedding. So the
alignment here is canonical-lexical (token Dice over canonical s/p/o) augmented by
spl_core's projection/entropy neighbourhood — it recognises lexical/structural
isomorphism, it does NOT prove meaning-equivalence. No claim that isomorphy is
"solved".
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "src"))

from desi.spl_core import normalized_shannon_entropy, project_atomic_claim  # noqa: E402
from desi_intervention import _content_tokens  # noqa: E402
from alexandria_dba_schema import AlignmentType  # noqa: E402

_ALIGN_PAIR = 0.55        # per-pair overall canonical overlap for a 1-1 alignment
_REGION_HIGH = 0.60       # union content Jaccard for "same region"
_REGION_MID = 0.35
_ENTROPY_BAND = 0.15      # spl_core entropy proximity for projection_neighbor


def _dice(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return 2.0 * len(a & b) / (len(a) + len(b))


def _canonize(claim: dict) -> dict:
    """Project a claim through spl_core into its canonical, entropy-tagged form."""
    cand, _ = project_atomic_claim({
        "subject": claim.get("subject", ""), "predicate": claim.get("predicate", ""),
        "object": claim.get("object", ""), "confidence": claim.get("confidence", 0.7),
        "claim_type": claim.get("claim_type", "fact")})
    return {"subject": cand.subject, "predicate": cand.predicate, "object": cand.object,
            "entropy": cand.projection_entropy, "rule": cand.emission_rule,
            "content_tokens": _content_tokens(f"{cand.subject} {cand.object}"),
            "spo_tokens": _content_tokens(f"{cand.subject} {cand.predicate} {cand.object}")}


def _pair_overall(a: dict, b: dict) -> float:
    sd = _dice(_content_tokens(a["subject"]), _content_tokens(b["subject"]))
    pd = _dice(_content_tokens(a["predicate"]), _content_tokens(b["predicate"]))
    od = _dice(_content_tokens(a["object"]), _content_tokens(b["object"]))
    return 0.4 * sd + 0.25 * pd + 0.35 * od


def _is_projection_neighbor(a: dict, b: dict) -> bool:
    """spl_core signal: close in projection/entropy space + some subject overlap."""
    if a["entropy"] is None or b["entropy"] is None:
        return False
    return (a["rule"] == b["rule"]
            and abs(a["entropy"] - b["entropy"]) <= _ENTROPY_BAND
            and _dice(_content_tokens(a["subject"]), _content_tokens(b["subject"])) > 0)


def align_graphs(alpha: list[dict], beta: list[dict]) -> dict:
    """Classify how Gα and Gβ relate. Returns alignment type + coverage + edges."""
    ca = [_canonize(c) for c in alpha]
    cb = [_canonize(c) for c in beta]
    na, nb = len(ca), len(cb)

    if na == 0 and nb == 0:
        return {"alignment": AlignmentType.SEMANTIC_ISOMORPH.value, "coverage": 1.0,
                "region_jaccard": 1.0, "bijective": True, "n_alpha": 0, "n_beta": 0,
                "edges": [], "projection_neighbors": 0, "reconcilable": True}
    if na == 0 or nb == 0:
        return {"alignment": AlignmentType.STRUCTURALLY_DIVERGENT.value, "coverage": 0.0,
                "region_jaccard": 0.0, "bijective": False, "n_alpha": na, "n_beta": nb,
                "edges": [], "projection_neighbors": 0, "reconcilable": False}

    # region overlap (set-level, granularity-insensitive)
    ua = set().union(*[c["content_tokens"] for c in ca]) if ca else set()
    ub = set().union(*[c["content_tokens"] for c in cb]) if cb else set()
    region = (len(ua & ub) / len(ua | ub)) if (ua | ub) else 0.0

    # greedy 1-1 alignment by canonical overlap
    used_b, edges, pairs = set(), [], []
    for i, a in enumerate(ca):
        best, bj = -1.0, None
        for j, b in enumerate(cb):
            if j in used_b:
                continue
            s = _pair_overall(a, b)
            if s > best:
                best, bj = s, j
        if bj is not None and best >= _ALIGN_PAIR:
            used_b.add(bj)
            pairs.append((i, bj, round(best, 3)))
            edges.append({"alpha": i, "beta": bj, "overlap": round(best, 3)})
    aligned_a = {i for i, _, _ in pairs}
    aligned_b = {j for _, j, _ in pairs}
    proj_neighbors = sum(1 for i, a in enumerate(ca) if i not in aligned_a
                         for b in cb if _is_projection_neighbor(a, b))
    coverage = (len(aligned_a) + len(aligned_b)) / (na + nb)
    bijective = (na == nb) and len(pairs) == na and all(o >= 0.6 for *_, o in pairs)

    # classify
    if region >= _REGION_HIGH:
        if bijective:
            align = AlignmentType.SEMANTIC_ISOMORPH
        elif na != nb or len(pairs) < max(na, nb):
            align = AlignmentType.GRANULARITY_OVERLAP   # same region, split/merge
        else:
            align = AlignmentType.SEMANTIC_OVERLAP
    elif region >= _REGION_MID:
        align = AlignmentType.PARTIAL_OVERLAP
    elif proj_neighbors and coverage == 0.0:
        align = AlignmentType.PROJECTION_NEIGHBOR
    else:
        align = AlignmentType.STRUCTURALLY_DIVERGENT

    reconcilable = align in (AlignmentType.SEMANTIC_ISOMORPH,
                             AlignmentType.GRANULARITY_OVERLAP)
    return {"alignment": align.value, "coverage": round(coverage, 3),
            "region_jaccard": round(region, 3), "bijective": bijective,
            "n_alpha": na, "n_beta": nb, "edges": edges,
            "projection_neighbors": proj_neighbors, "reconcilable": reconcilable}


def semantic_reoutcome(p16_outcome: str, alignment: dict) -> str:
    """Re-characterise a P16 DBA outcome using the semantic alignment.

    Only ever REPLACES a spurious branch_required with a same-region alignment
    label; it never asserts truth and never overrides a genuine divergence."""
    if p16_outcome != "branch_required":
        return p16_outcome
    al = alignment["alignment"]
    if al in (AlignmentType.SEMANTIC_ISOMORPH.value, AlignmentType.GRANULARITY_OVERLAP.value):
        return al                       # same region -> reconcilable, not a branch
    if al == AlignmentType.SEMANTIC_OVERLAP.value:
        return AlignmentType.SEMANTIC_OVERLAP.value
    return "branch_required"            # partial / divergent -> stays a real branch


__all__ = ["align_graphs", "semantic_reoutcome"]
