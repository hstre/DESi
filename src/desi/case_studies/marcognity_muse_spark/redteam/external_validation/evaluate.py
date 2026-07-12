"""Scoring for the external validation: inter-annotator agreement + frozen-v2 metrics.

Given two independent annotators' filled workbooks (+ optional adjudication of disagreements)
and the claims, this computes:
  - inter-annotator reliability: Cohen's kappa (2 raters) and Krippendorff's alpha (nominal)
    for the SIG/clean decision (sentence and document), the effect-size locus, and error type;
  - the frozen v2 rule's metrics against BOTH sentence-gold and document-gold: precision,
    recall, F1, coverage;
  - the primary quantities: precision vs document-gold, recall on TRUE epistemic errors, and
    the share of sentence-judgments revised by document context;
  - a per-locus breakdown (same_sentence / adjacent_sentence / table_or_figure / ci_only /
    absent) — the lexical-sentence-rule vs document-wide-check split.

Applies v2; never modifies it. Gold comes from annotators, never from the rule.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


def load_workbook(path: Path) -> dict[str, dict]:
    with Path(path).open(encoding="utf-8") as f:
        return {r["claim_id"]: r for r in csv.DictReader(f)}


# ---- inter-annotator reliability -------------------------------------------------

def cohen_kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    cats = set(a) | set(b)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    return 1.0 if pe == 1 else round((po - pe) / (1 - pe), 3)


def krippendorff_alpha_nominal(coder_labels: list[list[str | None]]) -> float:
    """Nominal alpha for aligned coder label lists (None = missing)."""
    n_units = len(coder_labels[0])
    o: dict[tuple, float] = defaultdict(float)
    for i in range(n_units):
        vals = [cl[i] for cl in coder_labels if cl[i] is not None]
        m = len(vals)
        if m < 2:
            continue
        for p in range(m):
            for q in range(m):
                if p != q:
                    o[(vals[p], vals[q])] += 1.0 / (m - 1)
    cats = {x for pair in o for x in pair}
    if not cats:
        return float("nan")
    nc = {c: sum(o[(c, k)] for k in cats) for c in cats}
    n = sum(nc.values())
    num = sum(o[(c, k)] for c in cats for k in cats if c != k)
    den = sum(nc[c] * nc[k] for c in cats for k in cats if c != k)
    if den == 0:
        return 1.0
    return round(1 - (n - 1) * num / den, 3)


def agreement(a: dict, b: dict, field: str) -> dict:
    ids = [i for i in a if i in b]
    la = [a[i][field] for i in ids]
    lb = [b[i][field] for i in ids]
    return {"field": field, "n": len(ids), "cohen_kappa": cohen_kappa(la, lb),
            "krippendorff_alpha": krippendorff_alpha_nominal([la, lb]),
            "raw_agreement": round(sum(x == y for x, y in zip(la, lb)) / len(ids), 3)
            if ids else float("nan")}


# ---- gold construction (adjudicated) ---------------------------------------------

def build_gold(a: dict, b: dict, adjudication: dict | None, fields: tuple) -> dict:
    """Where A==B use that; else take the adjudicator's value. Missing adjudication on a
    disagreement drops the claim from gold (reported)."""
    adj = adjudication or {}
    gold, dropped = {}, []
    for cid in a:
        if cid not in b:
            continue
        rec = {}
        ok = True
        for fld in fields:
            if a[cid][fld] == b[cid][fld] and a[cid][fld] != "":
                rec[fld] = a[cid][fld]
            elif cid in adj and adj[cid].get(fld):
                rec[fld] = adj[cid][fld]
            else:
                ok = False
                break
        if ok:
            gold[cid] = rec
        else:
            dropped.append(cid)
    return {"gold": gold, "dropped": dropped}


# ---- rule metrics ----------------------------------------------------------------

def _prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return round(p, 3), round(r, 3), round(f, 3)


def evaluate_rule(claims: list[dict], gold: dict, detector, sig_value: str = "SIG") -> dict:
    """Apply `detector` sentence-wise; score vs sentence-gold and document-gold."""
    text = {c["claim_id"]: c["sentence"] for c in claims}
    ids = [cid for cid in gold if cid in text]
    pred = {cid: bool(detector(text[cid])) for cid in ids}

    def score(gold_field):
        tp = fp = fn = 0
        for cid in ids:
            g = gold[cid].get(gold_field) == sig_value
            if pred[cid] and g:
                tp += 1
            elif pred[cid] and not g:
                fp += 1
            elif (not pred[cid]) and g:
                fn += 1
        p, r, f = _prf(tp, fp, fn)
        return {"precision": p, "recall": r, "f1": f, "tp": tp, "fp": fp, "fn": fn}

    # recall on TRUE epistemic errors (real significance-vs-relevance mistakes)
    true_err = [cid for cid in ids if gold[cid].get("error_type") == "true_epistemic_error"]
    rec_true = round(sum(pred[cid] for cid in true_err) / len(true_err), 3) if true_err else None
    # share of sentence-judgments the document context revises
    revised = [cid for cid in ids
               if gold[cid].get("gold_sentence_class") != gold[cid].get("gold_document_class")]
    # per-locus precision/recall vs document gold
    by_locus = {}
    for cid in ids:
        by_locus.setdefault(gold[cid].get("effect_size_locus", "?"), []).append(cid)
    locus_scores = {}
    for loc, cids in sorted(by_locus.items()):
        tp = sum(pred[c] and gold[c].get("gold_document_class") == sig_value for c in cids)
        fp = sum(pred[c] and gold[c].get("gold_document_class") != sig_value for c in cids)
        fn = sum((not pred[c]) and gold[c].get("gold_document_class") == sig_value for c in cids)
        p, r, f = _prf(tp, fp, fn)
        locus_scores[loc] = {"n": len(cids), "precision": p, "recall": r,
                             "tp": tp, "fp": fp, "fn": fn}

    return {
        "n_scored": len(ids),
        "coverage": round(sum(pred.values()) / len(ids), 3) if ids else 0.0,
        "vs_sentence_gold": score("gold_sentence_class"),
        "vs_document_gold": score("gold_document_class"),
        "recall_true_epistemic_errors": rec_true,
        "context_revised_share": round(len(revised) / len(ids), 3) if ids else 0.0,
        "per_locus_vs_document_gold": locus_scores,
    }


__all__ = ["load_workbook", "cohen_kappa", "krippendorff_alpha_nominal", "agreement",
           "build_gold", "evaluate_rule"]
