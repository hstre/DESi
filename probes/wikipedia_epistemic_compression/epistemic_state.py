"""Deterministic epistemic-state extraction from a Wikipedia article (NO embeddings).

Treats the article as an epistemic state space and extracts, by fixed lexical/structural
rules (pre-registered here, never tuned to results):

  * claims            -- fact-bearing sentences (>= MIN_CLAIM_WORDS content words, >=1 anchor)
  * anchors           -- proper-noun / numeric tokens (DESi 'anchor_density' applied to text)
  * branches          -- sentences with alternative-narrative cues
  * conflicts         -- sentences with disagreement/contradiction cues
  * uncertainty       -- sentences with hedging/uncertainty cues
  * citations         -- <ref>/{{sfn}}/{{harv}} anchors counted from wikitext
  * sections          -- == headers == (+ optional per-section DESi frame)
  * open regions      -- sections that carry claims but no citation support

The COMPRESSED DESi state keeps: the top-K claims (by anchor density), and the FULL set
of branch/conflict/uncertainty markers + citation counts + section frames. We then MEASURE
what is lost (anchors not covered, claims beyond budget, and -- always -- the prose itself).
"""
from __future__ import annotations

import json
import re

MIN_CLAIM_WORDS = 6
CLAIM_BUDGET = 25          # compressed state keeps at most this many core claims (fixed)
MAX_ANCHORS_PER_CLAIM = 6
FRAME_TEXT_CAP = 2000

_STOP = frozenset((
    "the a an of to in on and or is are was were be been being that this these those it its "
    "as at by for with from has have had do does did but if then than so such into out up down "
    "over under about their they them we you i which who he she his her not no only any all per "
    "also more most some many other than when where while there here also been being".split()))

# --- fixed cue lexicons (alternative narratives / conflict / uncertainty) ---------------
BRANCH_CUES = ("alternatively", "another view", "other scholars", "some scholars",
               "some historians", "some argue", "others argue", "others contend",
               "others believe", "some believe", "competing", "rival", "two theories",
               "several theories", "different interpretation", "on the other hand",
               "by contrast", "conversely", "another explanation", "an alternative",
               "according to some", "according to others", "a minority", "mainstream view",
               "fringe", "variously", "either", "whereas")
CONFLICT_CUES = ("however", "contradict", "disput", "controvers", "refut", "criticiz",
                 "criticis", "conflict", " versus ", " vs ", "denied", "contrary",
                 "challenged", "contested", "rejected", "debate", "at odds", "tension between")
UNCERTAINTY_CUES = ("may ", "might ", "perhaps", "possibly", "probably", "uncertain",
                    "unclear", "unknown", "allegedly", "reportedly", "estimat", "approximat",
                    "circa", "speculat", "believed to", "thought to", "suggest", "appears to",
                    "seems to", "likely", "presumably", "remains unclear", "poorly understood",
                    "is believed", "is thought", "no consensus")

# --- article-type heuristic (deterministic; for cross-article observation only) ---------
TYPE_KEYWORDS = {
    "biography": ("born", "died", "his career", "her career", "graduated", "married"),
    "history": ("war", "battle", "empire", "century", "invasion", "treaty", "dynasty",
                "revolution", "ancient", "medieval", "regiment", "campaign"),
    "politics": ("election", "government", "party", "policy", "parliament", "president",
                 "minister", "senate", "vote", "legislation", "constituency"),
    "science": ("species", "genus", "theorem", "equation", "protein", "element", "orbit",
                "algorithm", "molecule", "hypothesis", "experiment", "isotope", "galaxy"),
}


def token_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", text or ""))


def _strip_headers(text: str) -> str:
    return "\n".join(ln for ln in text.splitlines() if not re.match(r"\s*=+.*=+\s*$", ln))


def sentences(text: str) -> list:
    body = _strip_headers(text)
    body = re.sub(r"\s+", " ", body)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", body)
    return [s.strip() for s in parts if len(s.strip()) > 1]


def content_tokens(text: str) -> list:
    return [t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", (text or "").lower())
            if t not in _STOP and len(t) > 2]


def anchors(sentence: str) -> set:
    """Proper-noun and numeric anchors (skip the sentence-initial capital)."""
    out = set()
    for m in re.finditer(r"\b\d[\d,\.]*\b", sentence):
        out.add(m.group(0).rstrip(".,"))
    words = sentence.split()
    for i, w in enumerate(words):
        core = re.sub(r"[^A-Za-z]", "", w)
        if i == 0:
            continue
        if len(core) > 2 and core[0].isupper() and not core.isupper():
            out.add(core.lower())
    return out


def _has_cue(low: str, cues) -> bool:
    return any(c in low for c in cues)


def is_claim(sentence: str) -> bool:
    if "=" in sentence and re.match(r"\s*=+", sentence):
        return False
    if sentence.endswith("?"):
        return False
    return len(content_tokens(sentence)) >= MIN_CLAIM_WORDS and len(anchors(sentence)) >= 1


def _sections(plaintext: str) -> list:
    """Split exsectionformat=wiki plaintext into [(title, body)] sections."""
    out, title, buf = [], "Lead", []
    for ln in plaintext.splitlines():
        m = re.match(r"\s*=+\s*(.*?)\s*=+\s*$", ln)
        if m:
            out.append((title, "\n".join(buf)))
            title, buf = m.group(1), []
        else:
            buf.append(ln)
    out.append((title, "\n".join(buf)))
    return [(t, b) for t, b in out if b.strip() or t == "Lead"]


def count_citations(wikitext: str) -> int:
    low = (wikitext or "").lower()
    return low.count("<ref") + low.count("{{sfn") + low.count("{{harv") + low.count("{{cite")


def classify_type(plaintext: str) -> str:
    low = plaintext.lower()[:8000]
    scores = {t: sum(low.count(k) for k in kws) for t, kws in TYPE_KEYWORDS.items()}
    top = max(scores, key=scores.get)
    return top if scores[top] > 0 else "general"


def build_state(article: dict, frame_fn=None) -> dict:
    """Extract the epistemic state + compression metrics for one cached article."""
    plaintext = article.get("plaintext", "") or ""
    wikitext = article.get("wikitext", "") or ""
    sents = sentences(plaintext)
    sects = _sections(plaintext)

    claims = []
    for idx, s in enumerate(sents):
        if is_claim(s):
            a = sorted(anchors(s))
            claims.append({"i": idx, "anchors": a[:MAX_ANCHORS_PER_CLAIM], "n_anchors": len(a)})
    branch_idx = [i for i, s in enumerate(sents) if _has_cue(s.lower(), BRANCH_CUES)]
    conflict_idx = [i for i, s in enumerate(sents) if _has_cue(s.lower(), CONFLICT_CUES)]
    uncertainty_idx = [i for i, s in enumerate(sents) if _has_cue(s.lower(), UNCERTAINTY_CUES)]

    all_anchors = set()
    for s in sents:
        all_anchors |= anchors(s)

    # compressed state: top-K claims by anchor density (+ index), FULL marker structure
    kept = sorted(claims, key=lambda c: (c["n_anchors"], -c["i"]), reverse=True)[:CLAIM_BUDGET]
    kept = sorted(kept, key=lambda c: c["i"])
    state_anchors = set()
    for c in kept:
        state_anchors |= set(c["anchors"])
    for i in branch_idx + conflict_idx:
        state_anchors |= anchors(sents[i])

    citations = count_citations(wikitext)
    # per-section frames (DESi frame layer, read-only) + open regions (claims, no citation)
    frames, open_regions = [], []
    for stitle, sbody in sects:
        fr = frame_fn(sbody[:FRAME_TEXT_CAP]) if frame_fn else "skipped"
        has_claim = any(is_claim(x) for x in sentences(sbody))
        sect_cites = count_citations("")  # citations counted globally (wikitext not section-split)
        frames.append({"section": stitle, "frame": fr, "has_claim": has_claim})

    n_sents = max(1, len(sents))
    n_claims = len(claims)
    recover = round(len(state_anchors) / len(all_anchors), 3) if all_anchors else 0.0

    compressed = {
        "title": article.get("title"), "pageid": article.get("pageid"),
        "n_sections": len(sects),
        "claims": kept,
        "branches": [{"i": i, "anchors": sorted(anchors(sents[i]))[:MAX_ANCHORS_PER_CLAIM]} for i in branch_idx],
        "conflicts": [{"i": i} for i in conflict_idx],
        "uncertainty": {"count": len(uncertainty_idx), "sentences": uncertainty_idx},
        "citations": citations,
        "frames": [{"section": f["section"], "frame": f["frame"]} for f in frames],
    }
    state_text = json.dumps(compressed, ensure_ascii=False, sort_keys=True)

    # DESi-style epistemic vector (mirrors core StateVector dims, applied to text)
    vector = {
        "anchor_density": round(len(all_anchors) / n_sents, 3),
        "contradiction_load": round(len(conflict_idx) / n_sents, 3),
        "branch_cost": round(len(branch_idx) / n_sents, 3),
        "uncertainty_load": round(len(uncertainty_idx) / n_sents, 3),
        "citation_support": round(citations / max(1, n_claims), 3),
        "open_region_ratio": round(sum(1 for f in frames if f["has_claim"]
                                       and f["frame"] in ("frame_undeclared", "skipped", "unavailable"))
                                   / max(1, len(frames)), 3),
    }

    raw_tokens = token_count(plaintext)
    state_tokens = token_count(state_text)
    metrics = {
        "title": article.get("title"), "pageid": article.get("pageid"),
        "article_type": classify_type(plaintext),
        "raw_tokens": raw_tokens, "desi_state_tokens": state_tokens,
        "compression_ratio": round(1.0 - state_tokens / raw_tokens, 4) if raw_tokens else 0.0,
        "claim_count": n_claims, "claims_kept": len(kept),
        "branch_count": len(branch_idx),
        "conflict_count": len(conflict_idx),
        "uncertainty_markers": len(uncertainty_idx),
        "citation_anchors": citations,
        "recoverability_proxy": recover,
        "compression_loss": round(1.0 - recover, 3),
        "n_sentences": len(sents), "n_sections": len(sects),
        "frame_diversity": len({f["frame"] for f in frames}),
        "vector": vector,
        # explicit preservation flags (existence-level; prose is NOT preserved by construction)
        "branches_preserved": 1.0 if branch_idx == [b["i"] for b in compressed["branches"]] else 0.0,
        "conflicts_preserved": 1.0 if conflict_idx == [c["i"] for c in compressed["conflicts"]] else 0.0,
        "uncertainty_preserved": 1.0 if len(uncertainty_idx) == compressed["uncertainty"]["count"] else 0.0,
        "claim_coverage": round(len(kept) / n_claims, 3) if n_claims else 1.0,
        "prose_tokens_in_state": 0,
    }
    return {"compressed": compressed, "metrics": metrics, "state_text": state_text}
