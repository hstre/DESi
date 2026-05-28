"""v2 dual-layer: composite anchors + section-aware proportional state (deterministic, no embeddings).

Reuses v1 segmentation (`dual_layer.segment`) and the epistemic_compression helpers READ-ONLY.
The active state is built per section (proportional claim budget); each unit gets a composite
anchor (section + offsets + span hash + neighbour fingerprints). Resolution has an EXACT mode
(offset + span-hash check, for the archived snapshot) and a FUZZY mode (locator + neighbour
fingerprints, drift-robust) — the fuzzy mode is the honest navigation test vs. v1's bare locator.
"""
from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "wikipedia_dual_layer"))
sys.path.insert(0, str(_HERE.parent / "wikipedia_epistemic_compression"))

import dual_layer as v1dl          # noqa: E402  (segment(), read-only)
import epistemic_state as es       # noqa: E402  (cues, anchors, is_claim, token_count, ...)
from preregistration import (      # noqa: E402
    FP_WEIGHT, LOCATOR_LEN, NEIGHBOR_FP_LEN, SECTION_BUDGET_CAP, SECTION_BUDGET_FRAC,
    SECTION_BUDGET_MIN, SPAN_HASH_HEX,
)


def _span_hash(text: str) -> str:
    toks = sorted(es.content_tokens(text))
    return hashlib.sha256(",".join(toks).encode("utf-8")).hexdigest()[:SPAN_HASH_HEX]


def _fp(text: str) -> list:
    return es.content_tokens(text)[:NEIGHBOR_FP_LEN]


def classify(text: str) -> list:
    return v1dl.classify(text)


def composite_anchor(units: list, i: int) -> dict:
    u = units[i]
    prev_t = units[i - 1]["text"] if i > 0 else ""
    next_t = units[i + 1]["text"] if i + 1 < len(units) else ""
    return {
        "kinds": classify(u["text"]),
        "section_idx": u["section_idx"], "section_path": [u["section_title"]],
        "sent_idx": u["sent_idx"], "start": u["start"], "end": u["end"],
        "span_hash": _span_hash(u["text"]),
        "locator": es.content_tokens(u["text"])[:LOCATOR_LEN],
        "prev_fp": _fp(prev_t), "next_fp": _fp(next_t),
        "n_anchors": len(es.anchors(u["text"])),
    }


def _section_budget(n_claims: int) -> int:
    if n_claims <= 0:
        return 0
    return max(SECTION_BUDGET_MIN, min(SECTION_BUDGET_CAP, math.ceil(SECTION_BUDGET_FRAC * n_claims)))


def build_active_state_v2(units: list) -> dict:
    """Section-aware: per section keep ALL markers + top proportional pure-claims."""
    idx_by_kind = [(i, classify(u["text"])) for i, u in enumerate(units)]
    epistemic = [(i, k) for i, k in idx_by_kind if k]
    by_section = {}
    for i, k in epistemic:
        by_section.setdefault(units[i]["section_idx"], []).append((i, k))
    kept_idx = []
    for sec, items in by_section.items():
        markers = [(i, k) for i, k in items if set(k) & {"branch", "conflict", "uncertainty"}]
        pure = [(i, k) for i, k in items if k == ["claim"]]
        pure.sort(key=lambda ik: (len(es.anchors(units[ik[0]]["text"])), -ik[0]), reverse=True)
        budget = _section_budget(len(pure))
        kept_idx += [i for i, _ in markers] + [i for i, _ in pure[:budget]]
    kept_idx = sorted(set(kept_idx))
    return {"anchors": [composite_anchor(units, i) for i in kept_idx],
            "n_total_units": len(epistemic), "n_active_units": len(kept_idx)}


def resolve_exact(anchor: dict, cold_text: str) -> bool:
    span = cold_text[anchor["start"]:anchor["end"]]
    return _span_hash(span) == anchor["span_hash"]


def _jac(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b) if (a | b) else 0.0


def resolve_fuzzy(anchor: dict, units: list):
    """Locator + neighbour-fingerprint scoring (no offsets/hash). Returns (unit, is_correct)."""
    key = set(anchor["locator"])
    pkey, nkey = set(anchor["prev_fp"]), set(anchor["next_fp"])
    if not key:
        return None, False
    best, best_score = None, -1.0
    for i, u in enumerate(units):
        toks = set(es.content_tokens(u["text"]))
        if not toks:
            continue
        prev_t = set(es.content_tokens(units[i - 1]["text"])) if i > 0 else set()
        next_t = set(es.content_tokens(units[i + 1]["text"])) if i + 1 < len(units) else set()
        score = _jac(key, toks) + FP_WEIGHT * _jac(pkey, prev_t) + FP_WEIGHT * _jac(nkey, next_t)
        if score > best_score:
            best, best_score = u, score
    return best, bool(best is not None and best["start"] == anchor["start"])


def build_dual_layer_v2(article: dict) -> dict:
    cold_text = article.get("plaintext", "") or ""
    wikitext = article.get("wikitext", "") or ""
    units = v1dl.segment(cold_text)
    active = build_active_state_v2(units)
    anchors = active["anchors"]

    state_text = repr([(a["kinds"], a["section_idx"], a["start"], a["end"],
                        a["span_hash"], a["locator"], a["prev_fp"], a["next_fp"]) for a in anchors])
    raw_tokens = es.token_count(cold_text)
    state_tokens = es.token_count(state_text)

    exact_ok = sum(1 for a in anchors if resolve_exact(a, cold_text))
    offset_integrity = round(exact_ok / len(anchors), 3) if anchors else 1.0
    fuzzy_correct = sum(1 for a in anchors if resolve_fuzzy(a, units)[1])
    anchor_precision = round(fuzzy_correct / len(anchors), 3) if anchors else 0.0

    def survival(kind, cues):
        of_kind = [a for a in anchors if kind in a["kinds"]]
        if not of_kind:
            return 1.0
        ok = 0
        for a in of_kind:
            best, corr = resolve_fuzzy(a, units)
            if corr and best is not None and es._has_cue(best["text"].lower(), cues):
                ok += 1
        return round(ok / len(of_kind), 3)

    total = active["n_total_units"]
    act = active["n_active_units"]
    navigable_rate = round(act / total, 3) if total else 0.0
    cold_scan_rate = round(1 - act / total, 3) if total else 0.0
    anchor_recoverability = round(fuzzy_correct / total, 3) if total else 0.0
    n_sections = len({u["section_idx"] for u in units})

    return {"cold_text": cold_text, "units": units, "anchors": anchors, "metrics": {
        "title": article.get("title"), "pageid": article.get("pageid"),
        "article_type": es.classify_type(cold_text),
        "raw_tokens": raw_tokens, "state_tokens": state_tokens,
        "compression_ratio": round(1.0 - state_tokens / raw_tokens, 4) if raw_tokens else 0.0,
        "anchor_count": len(anchors),
        "anchor_precision": anchor_precision, "offset_integrity": offset_integrity,
        "anchor_recoverability": anchor_recoverability,
        "navigable_rate": navigable_rate, "cold_scan_rate": cold_scan_rate,
        "branch_survival": survival("branch", es.BRANCH_CUES),
        "conflict_survival": survival("conflict", es.CONFLICT_CUES),
        "uncertainty_survival": survival("uncertainty", es.UNCERTAINTY_CUES),
        "n_total_units": total, "n_active_units": act, "n_sections": n_sections,
        "n_branches": sum(1 for a in anchors if "branch" in a["kinds"]),
        "n_conflicts": sum(1 for a in anchors if "conflict" in a["kinds"]),
        "n_uncertainty": sum(1 for a in anchors if "uncertainty" in a["kinds"]),
        "citation_anchors": es.count_citations(wikitext),
    }}
