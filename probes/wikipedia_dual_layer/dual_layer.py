"""Dual-layer epistemic navigation: compact active state + cold full prose, joined by anchors.

Deterministic, embedding-free. The active DESi state stores, per epistemic unit, a
NarrativeAnchor = {kind(s), section, char offsets, short lexical locator} -- never the
sentence text. Retrieval has two modes:

  * OFFSET mode  -- cold_text[start:end]; exact by construction (validates replayable offsets).
  * LOCATOR mode -- find the cold sentence best matching the stored locator tokens (Jaccard),
    the NON-trivial test of "does a compact key reliably navigate back to the right place?".

Reuses the wikipedia_epistemic_compression probe READ-ONLY (cue lexicons, anchor/claim
helpers, the frozen set + cache).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "wikipedia_epistemic_compression"))

import epistemic_state as es  # noqa: E402  (read-only reuse)

LOCATOR_LEN = 6          # content tokens kept as the lexical locator (fixed, pre-registered)
CLAIM_BUDGET = es.CLAIM_BUDGET


def segment(plaintext: str) -> list:
    """Split into sentences with TRUE char offsets into `plaintext` (the cold store).

    Header lines (== Section ==) set the current section and are not emitted as units.
    """
    units, sec_idx, sec_title, sidx, pos = [], -1, "Lead", 0, 0
    for line in plaintext.split("\n"):
        h = re.match(r"\s*=+\s*(.*?)\s*=+\s*$", line)
        if h:
            sec_idx += 1
            sec_title = h.group(1)
        elif line.strip():
            for m in re.finditer(r"[^.!?]*[.!?]+|\S[^.!?]*$", line):
                raw = m.group(0)
                s = raw.strip()
                if len(s) <= 1:
                    continue
                lead = len(raw) - len(raw.lstrip())
                start = pos + m.start() + lead
                units.append({"sent_idx": sidx, "section_idx": max(sec_idx, 0),
                              "section_title": sec_title, "start": start,
                              "end": start + len(s), "text": s})
                sidx += 1
        pos += len(line) + 1
    return units


def classify(text: str) -> list:
    low = text.lower()
    kinds = []
    if es.is_claim(text):
        kinds.append("claim")
    if es._has_cue(low, es.BRANCH_CUES):
        kinds.append("branch")
    if es._has_cue(low, es.CONFLICT_CUES):
        kinds.append("conflict")
    if es._has_cue(low, es.UNCERTAINTY_CUES):
        kinds.append("uncertainty")
    return kinds


def _anchor(unit: dict, kinds: list) -> dict:
    return {"kinds": kinds, "section_idx": unit["section_idx"],
            "start": unit["start"], "end": unit["end"],
            "locator": es.content_tokens(unit["text"])[:LOCATOR_LEN],
            "n_anchors": len(es.anchors(unit["text"]))}


def build_active_state(units: list) -> dict:
    """Active memory: ALL marker-bearing units + top-K pure-claim units, as anchors only."""
    classified = [(u, classify(u["text"])) for u in units]
    epistemic = [(u, k) for u, k in classified if k]
    markers = [(u, k) for u, k in epistemic if set(k) & {"branch", "conflict", "uncertainty"}]
    pure_claims = [(u, k) for u, k in epistemic if k == ["claim"]]
    pure_claims.sort(key=lambda uk: (len(es.anchors(uk[0]["text"])), -uk[0]["sent_idx"]), reverse=True)
    kept = markers + pure_claims[:CLAIM_BUDGET]
    kept.sort(key=lambda uk: uk[0]["sent_idx"])
    return {"anchors": [_anchor(u, k) for u, k in kept],
            "n_total_units": len(epistemic), "n_active_units": len(kept),
            "kept_sent_idx": {u["sent_idx"] for u, _ in kept}}


def resolve_offset(anchor: dict, cold_text: str) -> str:
    return cold_text[anchor["start"]:anchor["end"]]


def resolve_locator(anchor: dict, units: list):
    """Find the cold sentence whose content tokens best match the locator (Jaccard).
    Returns (matched_unit, is_correct) where correct == lands on the anchored span."""
    key = set(anchor["locator"])
    if not key:
        return None, False
    best, best_score = None, -1.0
    for u in units:
        toks = set(es.content_tokens(u["text"]))
        if not toks:
            continue
        score = len(key & toks) / len(key | toks)
        if score > best_score:
            best, best_score = u, score
    correct = bool(best is not None and best["start"] == anchor["start"])
    return best, correct


def build_dual_layer(article: dict) -> dict:
    cold_text = article.get("plaintext", "") or ""
    wikitext = article.get("wikitext", "") or ""
    units = segment(cold_text)
    active = build_active_state(units)
    anchors = active["anchors"]

    # serialize ACTIVE state (anchors only, no prose) for token accounting
    state_text = repr([(a["kinds"], a["section_idx"], a["start"], a["end"], a["locator"])
                       for a in anchors])
    raw_tokens = es.token_count(cold_text)
    state_tokens = es.token_count(state_text)

    # offset integrity (validates replayable offsets; ~1.0 on the frozen text)
    offs_ok = sum(1 for a in anchors if resolve_offset(a, cold_text).strip()
                  == cold_text[a["start"]:a["end"]].strip())
    offset_integrity = round(offs_ok / len(anchors), 3) if anchors else 1.0

    # locator precision (the non-trivial navigation test)
    correct = sum(1 for a in anchors if resolve_locator(a, units)[1])
    anchor_precision = round(correct / len(anchors), 3) if anchors else 0.0

    # per-type survival = unit of that type whose locator resolves to a span re-containing a cue
    def survival(kind, cues):
        of_kind = [a for a in anchors if kind in a["kinds"]]
        if not of_kind:
            return 1.0
        ok = 0
        for a in of_kind:
            best, corr = resolve_locator(a, units)
            if corr and best is not None and es._has_cue(best["text"].lower(), cues):
                ok += 1
        return round(ok / len(of_kind), 3)

    branch_survival = survival("branch", es.BRANCH_CUES)
    conflict_survival = survival("conflict", es.CONFLICT_CUES)
    uncertainty_survival = survival("uncertainty", es.UNCERTAINTY_CUES)

    total_units = active["n_total_units"]
    active_units = active["n_active_units"]
    # cold fallback: epistemic units with NO active anchor -> require a brute cold scan
    cold_access_rate = round((total_units - active_units) / total_units, 3) if total_units else 0.0
    # anchor recoverability = fraction of ALL units that are active AND locator-resolvable correctly
    anchor_recoverability = round(correct / total_units, 3) if total_units else 0.0

    n_sections = len({u["section_idx"] for u in units})
    metrics = {
        "title": article.get("title"), "pageid": article.get("pageid"),
        "article_type": es.classify_type(cold_text),
        "raw_tokens": raw_tokens, "state_tokens": state_tokens,
        "compression_ratio": round(1.0 - state_tokens / raw_tokens, 4) if raw_tokens else 0.0,
        "anchor_count": len(anchors),
        "anchor_precision": anchor_precision,
        "offset_integrity": offset_integrity,
        "anchor_recoverability": anchor_recoverability,
        "cold_access_rate": cold_access_rate,
        "branch_survival": branch_survival,
        "conflict_survival": conflict_survival,
        "uncertainty_survival": uncertainty_survival,
        "narrative_loss": round(1.0 - state_tokens / raw_tokens, 4) if raw_tokens else 0.0,
        "n_total_units": total_units, "n_active_units": active_units,
        "n_branches": sum(1 for a in anchors if "branch" in a["kinds"]),
        "n_conflicts": sum(1 for a in anchors if "conflict" in a["kinds"]),
        "n_uncertainty": sum(1 for a in anchors if "uncertainty" in a["kinds"]),
        "citation_anchors": es.count_citations(wikitext),
        "n_sections": n_sections,
    }
    return {"cold_text": cold_text, "units": units, "anchors": anchors, "metrics": metrics}
