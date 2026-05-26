"""Algorithmic micro-semantic pre-solver router (PERIPHERAL, benchmark adapter).

Principle: everything that can be decided algorithmically is decided here; the
LLM solver only handles the residue. Given one NLI/verification item (claim /
hypothesis + evidence / premise) this computes deterministic lexical-semantic
features and routes to a solver PROMPT MODE before the solver runs.

This is a self-contained benchmark micro-layer. It does NOT import or touch the
DESi semantic core / ontology; it is pure string/token arithmetic. No LLM, no
gold label, no dataset name. Deterministic and replay-stable: identical
(claim, evidence) -> identical mode.

Routing modes -> solver policy (the three FIXED prompt families):
    direct_entailment_likely -> entailment_direct
    contradiction_likely     -> baseline
    missing_linkage_risk     -> evidence_strict
    partial_support_risk     -> evidence_strict
    high_nei_risk            -> evidence_strict
    ambiguous                -> baseline
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MODES = (
    "direct_entailment_likely", "contradiction_likely", "missing_linkage_risk",
    "partial_support_risk", "high_nei_risk", "ambiguous",
)
POLICY = {
    "direct_entailment_likely": "entailment_direct",
    "contradiction_likely": "baseline",
    "missing_linkage_risk": "evidence_strict",
    "partial_support_risk": "evidence_strict",
    "high_nei_risk": "evidence_strict",
    "ambiguous": "baseline",
}

# Decision thresholds (fixed; not tuned per benchmark).
_HIGH_COV = 0.8
_MID_COV_LO = 0.4
_LOW_COV = 0.25
_ENT_LO = 0.5
_OVERLAP_FOR_POLARITY = 0.6

_STOP = frozenset((
    "the", "a", "an", "of", "to", "in", "on", "and", "or", "is", "are", "was",
    "were", "be", "been", "being", "that", "this", "these", "those", "it", "its",
    "as", "at", "by", "for", "with", "from", "has", "have", "had", "do", "does",
    "did", "but", "if", "then", "than", "so", "such", "into", "out", "up", "down",
    "over", "under", "about", "their", "they", "them", "he", "she", "his", "her",
    "him", "we", "you", "i", "which", "who", "whom", "whose", "what", "when",
    "where", "while", "there", "here", "also", "been", "being", "s", "t",
))
_NEGATIONS = frozenset((
    "not", "no", "never", "none", "without", "nobody", "nothing", "neither",
    "nor", "cannot", "fails", "fail", "failed", "absent", "lacks", "lack",
    "lacking", "denied", "denies", "deny", "refused", "refuses", "refuse",
    "unable",
))
_QUANTIFIERS = frozenset((
    "all", "every", "each", "any", "some", "most", "many", "few", "several",
    "both", "only", "least", "exactly", "entire", "whole", "half", "majority",
    "minority", "multiple", "single", "numerous",
))
_MODALITY = frozenset((
    "may", "might", "could", "would", "should", "can", "possibly", "probably",
    "likely", "perhaps", "allegedly", "reportedly", "claimed", "claims",
    "suggests", "suggest", "appears", "appear", "seems", "seem", "believed",
    "thought", "potential", "potentially", "presumably", "supposedly",
))
_TEMPORAL = frozenset((
    "before", "after", "during", "since", "until", "year", "years", "century",
    "decade", "month", "day", "today", "yesterday", "tomorrow", "ago", "later",
    "earlier", "previously", "subsequently", "annually", "monthly",
))

# Antonym groups: any token in one side + a counterpart on the other = contradiction.
_ANTONYM_PAIRS = (
    ("increase", "decrease"), ("increased", "decreased"), ("rise", "fall"),
    ("rose", "fell"), ("gain", "loss"), ("gained", "lost"), ("win", "lose"),
    ("won", "lost"), ("victory", "defeat"), ("alive", "dead"), ("living", "dead"),
    ("born", "died"), ("birth", "death"), ("before", "after"), ("more", "less"),
    ("more", "fewer"), ("open", "closed"), ("open", "shut"), ("true", "false"),
    ("accept", "reject"), ("accepted", "rejected"), ("include", "exclude"),
    ("included", "excluded"), ("begin", "end"), ("began", "ended"),
    ("start", "finish"), ("started", "finished"), ("succeed", "fail"),
    ("success", "failure"), ("present", "absent"), ("same", "different"),
    ("above", "below"), ("first", "last"), ("married", "divorced"),
    ("single", "married"), ("yes", "no"), ("support", "oppose"),
    ("supported", "opposed"), ("agree", "disagree"), ("legal", "illegal"),
    ("possible", "impossible"), ("hot", "cold"), ("high", "low"),
    ("large", "small"), ("big", "small"), ("positive", "negative"),
)
# Synonym groups: tokens in a group are treated as covering one another.
_SYN_GROUPS = (
    ("win", "won", "received", "receive", "awarded", "award", "earned", "earn",
     "got", "gained", "gain", "achieved", "achieve"),
    ("made", "make", "created", "create", "produced", "produce", "built", "build"),
    ("said", "say", "stated", "state", "announced", "announce", "declared",
     "declare", "reported", "report", "noted", "mentioned"),
    ("began", "begin", "started", "start", "founded", "found", "established",
     "establish", "launched", "launch"),
    ("ended", "end", "finished", "finish", "concluded", "conclude", "stopped",
     "stop", "ceased", "cease"),
    ("big", "large", "huge", "great", "major"),
    ("small", "little", "tiny", "minor"),
    ("died", "die", "passed", "deceased"),
    ("famous", "renowned", "celebrated", "noted", "prominent"),
    ("located", "locate", "situated", "based", "found"),
    ("author", "writer", "wrote", "write", "authored"),
    ("directed", "direct", "director"),
)


def _norm(text: str) -> str:
    return (text or "").strip()


def _raw_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9.\-&']*", text or "")


def _stem(tok: str) -> str:
    t = tok.lower().strip(".'-")
    if t.endswith("'s"):
        t = t[:-2]
    if t.endswith(("ies", "ied")) and len(t) > 4:
        return t[:-3] + "y"
    if t.endswith("ing") and len(t) > 5:
        return t[:-3]
    if t.endswith("ed") and len(t) > 4:
        return t[:-2]
    if t.endswith("s") and not t.endswith("ss") and len(t) > 3:
        return t[:-1]
    return t


def _build_syn_map():
    m = {}
    for gid, group in enumerate(_SYN_GROUPS):
        for w in group:
            m[_stem(w)] = f"g{gid}"
    return m


_SYN_MAP = _build_syn_map()


def _group(stem: str) -> str:
    return _SYN_MAP.get(stem, stem)


def _content_groups(text: str) -> set[str]:
    out = set()
    for tok in _raw_tokens(text):
        low = tok.lower()
        if low in _STOP:
            continue
        st = _stem(tok)
        if len(st) <= 1 and not st.isdigit():
            continue
        out.add(_group(st))
    return out


def _entities(text: str) -> set[str]:
    # capitalised proper-noun-like tokens; common function words are excluded via
    # the stopword set (so sentence-initial "The"/"A"/"In" do not count).
    ents = set()
    for t in _raw_tokens(text):
        if t[0].isupper() and any(ch.isalpha() for ch in t) and t.lower() not in _STOP:
            ents.add(t.lower().strip("."))
    return ents


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text or ""))


def _count_markers(text: str, markers: frozenset) -> int:
    return sum(1 for t in _raw_tokens(text) if t.lower() in markers)


def _stem_set(text: str) -> set[str]:
    return {_stem(t) for t in _raw_tokens(text) if t.lower() not in _STOP}


@dataclass(frozen=True)
class RouteResult:
    mode: str       # one of MODES
    policy: str     # one of baseline / evidence_strict / entailment_direct
    features: dict
    reason: str


class MicroSemanticRouter:
    """Deterministic algorithmic router. No LLM, no gold label, no dataset name."""

    def features(self, claim: str, evidence: str) -> dict:
        c, e = _norm(claim), _norm(evidence)
        cg, eg = _content_groups(c), _content_groups(e)
        ce, ee = _entities(c), _entities(e)
        cn, en = _numbers(c), _numbers(e)
        cov_claim = round(len(cg & eg) / len(cg), 3) if cg else 0.0
        cov_evid = round(len(cg & eg) / len(eg), 3) if eg else 0.0
        ent_overlap = round(len(ce & ee) / len(ce), 3) if ce else 1.0
        neg_c = sum(1 for t in _raw_tokens(c) if t.lower() in _NEGATIONS) + c.lower().count("n't")
        neg_e = sum(1 for t in _raw_tokens(e) if t.lower() in _NEGATIONS) + e.lower().count("n't")
        cstems, estems = _stem_set(c), _stem_set(e)
        antonym = any((a in cstems and b in estems) or (b in cstems and a in estems)
                      for a, b in ((_stem(x), _stem(y)) for x, y in _ANTONYM_PAIRS))
        numeric_mismatch = bool(cn and en and cn.isdisjoint(en) and cov_claim >= 0.5)
        polarity_mismatch = (neg_c > 0) != (neg_e > 0)
        return {
            "claim_content_n": len(cg), "evidence_content_n": len(eg),
            "content_coverage_claim": cov_claim, "content_coverage_evidence": cov_evid,
            "entity_overlap": ent_overlap, "claim_entities": len(ce),
            "shared_entities": len(ce & ee),
            "negation_claim": neg_c, "negation_evidence": neg_e,
            "quantifier_claim": _count_markers(c, _QUANTIFIERS),
            "quantifier_evidence": _count_markers(e, _QUANTIFIERS),
            "modality_claim": _count_markers(c, _MODALITY),
            "modality_evidence": _count_markers(e, _MODALITY),
            "numeric_claim": len(cn), "numeric_evidence": len(en),
            "numeric_mismatch": numeric_mismatch,
            "temporal_claim": _count_markers(c, _TEMPORAL),
            "temporal_evidence": _count_markers(e, _TEMPORAL),
            "antonym_hit": antonym, "polarity_mismatch": polarity_mismatch,
            # derived indicators
            "contradiction_indicator": bool(
                antonym or numeric_mismatch
                or (cov_claim >= _OVERLAP_FOR_POLARITY and polarity_mismatch)),
            "missing_linkage_indicator": bool(len(ce) > 0 and ent_overlap < _ENT_LO),
            "direct_entailment_indicator": bool(cov_claim >= _HIGH_COV and ent_overlap >= _ENT_LO),
            "evidence_coverage_score": cov_claim,   # how much of the claim the evidence covers
            "claim_coverage_score": cov_evid,
        }

    def route(self, claim: str, evidence: str, question: str | None = None) -> RouteResult:
        del question  # verify task uses claim + evidence
        f = self.features(claim, evidence)
        cov, ent = f["content_coverage_claim"], f["entity_overlap"]

        # 1. contradiction (antonym / numeric / polarity flip on shared content)
        if f["contradiction_indicator"]:
            why = ("antonym" if f["antonym_hit"] else
                   "numeric mismatch" if f["numeric_mismatch"] else "polarity flip")
            mode = "contradiction_likely"
            reason = f"{why} on overlapping content (cov={cov}) -> contradiction"
        # 2. claim content fully covered by evidence + entities present -> entailment
        elif f["direct_entailment_indicator"]:
            mode = "direct_entailment_likely"
            reason = f"claim covered by evidence (cov={cov}, entity_overlap={ent}) -> entailment"
        # 3. claim names entities the evidence does not -> missing linkage
        elif f["missing_linkage_indicator"]:
            mode = "missing_linkage_risk"
            reason = f"claim entities not in evidence (entity_overlap={ent}) -> missing linkage"
        # 4. almost no lexical overlap -> not enough info
        elif cov < _LOW_COV:
            mode = "high_nei_risk"
            reason = f"very low content coverage (cov={cov}) -> high NEI risk"
        # 5. partial overlap -> partial support
        elif _MID_COV_LO <= cov < _HIGH_COV:
            mode = "partial_support_risk"
            reason = f"partial content coverage (cov={cov}) -> partial support"
        # 6. otherwise ambiguous
        else:
            mode = "ambiguous"
            reason = f"no decisive lexical-semantic signal (cov={cov}, entity_overlap={ent}) -> ambiguous"

        return RouteResult(mode=mode, policy=POLICY[mode], features=f, reason=reason)


__all__ = ["MODES", "POLICY", "MicroSemanticRouter", "RouteResult"]
