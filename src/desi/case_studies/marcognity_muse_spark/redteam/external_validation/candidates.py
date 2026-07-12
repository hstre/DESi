"""Stratified candidate-claim generation.

Candidates are sentences matching any of four formulation strata (p-value / confidence
interval / effect-size / relevance). These are SAMPLING patterns — deliberately broad
and independent of the frozen rule — so the corpus is drawn across formulation types
(not only 'p <'), yielding positive, negative and boundary cases without bias toward
the rule's lexicon. Selection caps each document at 2-3 candidates spread across strata.
"""
from __future__ import annotations

import re

from .jats import Document

STRATA = {
    "p_value": re.compile(
        r"\bp\s*[<>=]\s*0?\.\d+|\bp[- ]?values?\b|\bstatistic(?:al|ally)\s+signif"
        r"|\bsignifican(?:t|ce)\b", re.I),
    "conf_int": re.compile(
        r"\b\d{2,3}\s*%\s*(?:ci|c\.i\.|confidence interval)|\bconfidence intervals?\b"
        r"|\bci\s*[:=]?\s*[\[(]|\bci\b\s*\d", re.I),
    "effect_size": re.compile(
        r"\bcohen'?s\s*d\b|\beffect sizes?\b|\bodds ratios?\b|\bor\s*=\s*\d"
        r"|\bhazard ratios?\b|\bhr\s*=\s*\d|\brisk ratios?\b|\brr\s*=\s*\d"
        r"|\bstandardi[sz]ed mean difference\b|\bsmd\b|\bpartial\s+(?:η|eta)"
        r"|\bη2\b|\beta[- ]squared|\br\s*=\s*[-.\d]|\br2\b|\bregression coefficient", re.I),
    "relevance": re.compile(
        r"\bclinical(?:ly)?\s+(?:signif|relevan|meaningful|important)"
        r"|\bpractical(?:ly)?\s+(?:signif|relevan|important)|\bclinical importance\b"
        r"|\bmeaningful(?:ly)?\b|\bimportant\b|\bsubstantial(?:ly)?\b|\bnegligible\b"
        r"|\bmodest\b|\btrivial\b|\bno (?:clinical|meaningful|practical)", re.I),
}
# positive allowlist: only sample where study importance claims live (results /
# discussion / conclusion / abstract / interpretation). Everything else (intro,
# background, methods, statistical-analysis, data-acquisition, refs) is skipped.
_SECTION_OK = re.compile(r"result|discuss|conclusion|abstract|interpret|comment", re.I)


def _strata_of(sentence: str) -> list[str]:
    return [name for name, rx in STRATA.items() if rx.search(sentence)]


def _section_allowed(para) -> bool:
    return bool(_SECTION_OK.search((para.section_type or "") + " " + (para.section_title or "")))


def find_candidates(doc: Document) -> list[dict]:
    """Sentences in results/discussion/conclusion/abstract that hit >=1 stratum."""
    out = []
    for para in doc.paragraphs:
        if not _section_allowed(para):
            continue
        sents = para.sentences
        for i, s in enumerate(sents):
            strata = _strata_of(s)
            if not strata:
                continue
            out.append({
                "pmcid": doc.pmcid, "section_type": para.section_type,
                "section_title": para.section_title, "paragraph_id": para.id,
                "sentence_index": i, "strata": strata, "sentence": s,
                "prev_sentence": sents[i - 1] if i > 0 else "",
                "next_sentence": sents[i + 1] if i + 1 < len(sents) else "",
                "paragraph_text": para.text,
                "referenced_tables": [
                    {"label": doc.tables[t]["label"], "caption": doc.tables[t]["caption"]}
                    for t in para.table_refs if t in doc.tables],
                "referenced_figures": [
                    {"label": doc.figures[f]["label"], "caption": doc.figures[f]["caption"]}
                    for f in para.fig_refs if f in doc.figures],
            })
    return out


def _priority(cand: dict) -> tuple:
    # prefer candidates combining a statistical marker with a relevance claim (the
    # significance-vs-importance construct), then more strata, then earlier position
    stat = any(s in cand["strata"] for s in ("p_value", "conf_int", "effect_size"))
    combo = stat and ("relevance" in cand["strata"])
    return (not combo, -len(cand["strata"]), cand["paragraph_id"], cand["sentence_index"])


def select_stratified(cands: list[dict], max_per_doc: int, rng) -> list[dict]:
    """Pick <= max_per_doc per document, spreading across strata (not only p-value)."""
    ordered = sorted(cands, key=_priority)
    chosen: list[dict] = []
    covered: set[str] = set()
    # first pass: greedily cover new strata
    for c in ordered:
        if len(chosen) >= max_per_doc:
            break
        if set(c["strata"]) - covered:
            chosen.append(c)
            covered |= set(c["strata"])
    # fill remaining slots by priority (deterministic; rng only breaks exact ties)
    for c in ordered:
        if len(chosen) >= max_per_doc:
            break
        if c not in chosen:
            chosen.append(c)
    rng.shuffle(chosen)  # de-correlate presentation order; selection itself is deterministic
    return chosen[:max_per_doc]


__all__ = ["STRATA", "find_candidates", "select_stratified"]
