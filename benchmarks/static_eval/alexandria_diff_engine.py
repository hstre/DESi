#!/usr/bin/env python3
"""Alexandria diff engine — typed deviation detection between two BuilderGraphs.

Aligns two independent reconstructions by CONTENT similarity (it does not know
which builder produced which, and never decides who is right) and emits a typed
DiffReport. "Explained difference", not "winner selection".

Detects: missing_claim, extra_claim, granularity_mismatch, modality_mismatch,
quantifier_mismatch, temporal_mismatch, relation_mismatch, uncertainty_divergence,
assumption_mismatch, entity_alias_mismatch.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "src"))

from desi_intervention import _content_tokens, _norm  # noqa: E402
from alexandria_dba_schema import DiffItem, DiffReport, DiffType  # noqa: E402

_ALIGN = 0.45          # overall (s/p/o) similarity to consider two claims aligned
_PARTIAL = 0.55        # subject+predicate similarity to treat a leftover as a split
_CONF_DIVERGE = 0.20   # confidence gap that counts as uncertainty divergence
_ARTICLES = ("the ", "a ", "an ")
_QUANTIFIERS = {"all", "every", "each", "none", "no", "some", "most", "many",
                "few", "any", "always", "never"}
_TEMPORAL_WORDS = {"always", "never", "now", "today", "currently", "historically",
                   "ago", "since", "until", "before", "after"}
_CAUSAL_MARKERS = ("because", "causes", "cause", "caused", "due to", "leads to",
                   "results in", "result in", "so that", "therefore")


def _is_causal(c: dict) -> bool:
    if c.get("claim_type") == "causal":
        return True
    text = f"{c.get('predicate','')} {c.get('object','')}".lower()
    return any(m in text for m in _CAUSAL_MARKERS)


def _dice(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return 2.0 * len(a & b) / (len(a) + len(b))


def _subj_norm(c: dict) -> str:
    s = _norm(c.get("subject", ""))
    for art in _ARTICLES:
        if s.startswith(art):
            s = s[len(art):]
    return s


def _overall(a: dict, b: dict) -> float:
    sd = _dice(_content_tokens(a.get("subject", "")), _content_tokens(b.get("subject", "")))
    pd = _dice(_content_tokens(a.get("predicate", "")), _content_tokens(b.get("predicate", "")))
    od = _dice(_content_tokens(a.get("object", "")), _content_tokens(b.get("object", "")))
    return 0.4 * sd + 0.25 * pd + 0.35 * od


def _subj_pred(a: dict, b: dict) -> float:
    sd = _dice(_content_tokens(a.get("subject", "")), _content_tokens(b.get("subject", "")))
    pd = _dice(_content_tokens(a.get("predicate", "")), _content_tokens(b.get("predicate", "")))
    return 0.6 * sd + 0.4 * pd


def _quant(c: dict) -> set:
    toks = _content_tokens(c.get("subject", "")) | _content_tokens(c.get("object", ""))
    return toks & _QUANTIFIERS


def _temporal(c: dict) -> set:
    text = f"{c.get('subject','')} {c.get('object','')}"
    toks = set(_norm(text).split())
    years = {t for t in toks if t.isdigit() and len(t) == 4}
    return (toks & _TEMPORAL_WORDS) | years


def _object_granularity_differs(a: dict, b: dict) -> bool:
    oa, ob = _content_tokens(a.get("object", "")), _content_tokens(b.get("object", ""))
    if not oa or not ob or oa == ob:
        return False
    # one object strictly contains the other's tokens -> different granularity
    return (oa < ob) or (ob < oa)


def _pair_diffs(a: dict, b: dict) -> list[DiffItem]:
    out: list[DiffItem] = []
    if a.get("modality", "asserted") != b.get("modality", "asserted"):
        out.append(DiffItem(DiffType.MODALITY_MISMATCH, "alpha", "beta", a, b,
                            f"modality {a.get('modality')} vs {b.get('modality')}"))
    if abs(float(a.get("confidence", 1.0)) - float(b.get("confidence", 1.0))) >= _CONF_DIVERGE:
        out.append(DiffItem(DiffType.UNCERTAINTY_DIVERGENCE, "alpha", "beta", a, b,
                            f"confidence {a.get('confidence')} vs {b.get('confidence')}"))
    if _subj_norm(a) != _subj_norm(b) and _dice(_content_tokens(a.get("subject", "")),
                                                 _content_tokens(b.get("subject", ""))) > 0:
        out.append(DiffItem(DiffType.ENTITY_ALIAS_MISMATCH, "alpha", "beta", a, b,
                            f"subject surface {a.get('subject')!r} vs {b.get('subject')!r}"))
    if _quant(a) != _quant(b):
        out.append(DiffItem(DiffType.QUANTIFIER_MISMATCH, "alpha", "beta", a, b,
                            f"quantifiers {sorted(_quant(a))} vs {sorted(_quant(b))}"))
    if _temporal(a) != _temporal(b):
        out.append(DiffItem(DiffType.TEMPORAL_MISMATCH, "alpha", "beta", a, b,
                            f"temporal {sorted(_temporal(a))} vs {sorted(_temporal(b))}"))
    if _object_granularity_differs(a, b):
        out.append(DiffItem(DiffType.GRANULARITY_MISMATCH, "alpha", "beta", a, b,
                            "aligned claims differ in object granularity"))
    if _is_causal(a) != _is_causal(b):
        out.append(DiffItem(DiffType.CAUSALITY_MISMATCH, "alpha", "beta", a, b,
                            f"causal structure differs (alpha causal={_is_causal(a)}, "
                            f"beta causal={_is_causal(b)})"))
    return out


def _edges_differ(alpha_edges: list, beta_edges: list) -> bool:
    return sorted(map(str, alpha_edges or [])) != sorted(map(str, beta_edges or []))


def diff_graphs(alpha: list[dict], beta: list[dict], *, source_ref: str = "",
                alpha_edges: list | None = None, beta_edges: list | None = None) -> DiffReport:
    diffs: list[DiffItem] = []
    used_beta: set[int] = set()
    aligned: list[tuple[dict, dict]] = []

    for a in alpha:
        best, bj = -1.0, None
        for j, b in enumerate(beta):
            if j in used_beta:
                continue
            s = _overall(a, b)
            if s > best:
                best, bj = s, j
        if bj is not None and best >= _ALIGN:
            used_beta.add(bj)
            aligned.append((a, beta[bj]))
        else:
            diffs.append(DiffItem(DiffType.MISSING_CLAIM, "alpha", "beta", a, None,
                                  "present in alpha, no aligned beta claim"))

    for a, b in aligned:
        diffs.extend(_pair_diffs(a, b))

    for j, b in enumerate(beta):
        if j in used_beta:
            continue
        if b.get("claim_type") == "assumption":
            diffs.append(DiffItem(DiffType.ASSUMPTION_MISMATCH, "alpha", "beta", None, b,
                                  "beta added an implicit-assumption claim"))
        elif max((_subj_pred(a, b) for a in alpha), default=0.0) >= _PARTIAL:
            diffs.append(DiffItem(DiffType.GRANULARITY_MISMATCH, "alpha", "beta", None, b,
                                  "beta has a finer sub-claim of an alpha claim"))
        else:
            diffs.append(DiffItem(DiffType.EXTRA_CLAIM, "alpha", "beta", None, b,
                                  "present in beta, no aligned alpha claim"))

    if _edges_differ(alpha_edges or [], beta_edges or []):
        diffs.append(DiffItem(DiffType.RELATION_MISMATCH, "alpha", "beta", None, None,
                              "relation/grouping structure differs between builders"))
    return DiffReport(source_ref=source_ref, builder_a="alpha", builder_b="beta", diffs=diffs)


_NEGATION = {"not", "no", "never", "cannot", "n't", "without", "neither", "nor", "none"}
_HEDGE = {"may", "might", "could", "possibly", "likely", "perhaps", "probably", "maybe", "seems"}
_Q_UNIVERSAL = {"all", "every", "each", "always", "everyone", "everything", "any"}
_Q_PARTIAL = {"some", "most", "many", "few", "several", "none", "never", "no"}
_TEMPORAL_OPP = [("before", "after"), ("always", "never"), ("past", "future"),
                 ("ancient", "modern"), ("now", "then")]
_POLARITY = {"increase": "decrease", "more": "less", "higher": "lower", "hot": "cold",
             "fast": "slow", "true": "false", "safe": "dangerous", "harmful": "harmless",
             "possible": "impossible", "alive": "dead", "rise": "fall", "gain": "lose",
             "accept": "reject", "cause": "prevent", "open": "closed", "positive": "negative"}
_CAUSAL = ("cause", "because", "causes", "caused", "due to", "leads to", "results in")


def _bag(claims, fields=("predicate", "object")) -> set:
    toks = set()
    for c in claims:
        text = " ".join(str(c.get(f, "")) for f in fields).lower().replace("'", " ")
        toks |= set(text.split())
    return toks


def typed_logical_divergences(alpha: list[dict], beta: list[dict]) -> list[str]:
    """Lexical (embedding-free) detection of LOGICAL divergences that semantic
    similarity must not reconcile. NOT truth labels — epistemic conflict types.
    Heuristic / lexicon-based; the reliable one is negation_flip."""
    out = []
    a, b = _bag(alpha), _bag(beta)
    a_so, b_so = _bag(alpha, ("subject", "predicate", "object")), _bag(beta, ("subject", "predicate", "object"))

    if (a & _NEGATION) ^ (b & _NEGATION):
        out.append("negation_flip")
    if (a & _HEDGE) ^ (b & _HEDGE):
        out.append("modality_flip")
    # quantifier_flip: opposing quantifier classes across the two sides
    if ((a_so & _Q_UNIVERSAL) and (b_so & _Q_PARTIAL)) or \
       ((b_so & _Q_UNIVERSAL) and (a_so & _Q_PARTIAL)):
        out.append("quantifier_flip")
    # temporal_flip: an opposing temporal pair split across sides
    for w1, w2 in _TEMPORAL_OPP:
        if (w1 in a_so and w2 in b_so) or (w2 in a_so and w1 in b_so):
            out.append("temporal_flip")
            break
    # polarity_flip: an antonym pair split across sides
    pol = {**_POLARITY, **{v: k for k, v in _POLARITY.items()}}
    if any(w in b_so for t in (a_so & set(pol)) for w in [pol[t]]):
        out.append("polarity_flip")
    # causal_direction_flip: both causal, with subject/object roles swapped
    def causal_pairs(claims):
        ps = []
        for c in claims:
            txt = f"{c.get('predicate','')} {c.get('object','')}".lower()
            if c.get("claim_type") == "causal" or any(m in txt for m in _CAUSAL):
                ps.append((_content_tokens(c.get("subject", "")), _content_tokens(c.get("object", ""))))
        return ps
    pa, pb = causal_pairs(alpha), causal_pairs(beta)
    for sa, oa in pa:
        for sb, ob in pb:
            if sa and ob and oa and sb and _dice(sa, ob) >= 0.5 and _dice(oa, sb) >= 0.5:
                out.append("causal_direction_flip")
                break
        else:
            continue
        break
    return sorted(set(out))


def region_aware_outcome(base_outcome: str, region_similarity: float | None,
                         n_alpha: int, n_beta: int, *, region_high: float = 0.55) -> str:
    """P18 rule: a branch_required driven by missing/extra claims over the SAME
    semantic region (high region_similarity) is re-characterised as a
    reconstruction (not a real branch). Pure function — the embedding-based
    region_similarity is supplied by the meaning-space layer; this engine stays
    embedding-free. Never asserts truth, never overrides a genuine divergence
    (low region_similarity keeps branch_required)."""
    if base_outcome != "branch_required" or region_similarity is None:
        return base_outcome
    if region_similarity >= region_high:
        return "reconstruction_isomorph" if n_alpha == n_beta else "coarse_grain_equivalent"
    return "branch_required"


__all__ = ["diff_graphs", "region_aware_outcome", "typed_logical_divergences"]
