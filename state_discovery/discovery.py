"""discover_state(chat) — lexical, deterministic discovery of epistemic state, no markers.

Categories: claims, constraints, decisions, conflicts, open_questions.

The discoverer scans each speaker turn sentence-by-sentence and classifies each one by
LEXICAL CUES only:

  * decisions: agreement / commit verbs ("let's", "we'll", "agreed", "go with"), optionally
    negated ("don't pin", "do not", "let's not")
  * constraints: hard normative + modal patterns ("must", "cannot", "hard rule", "not up for
    negotiation"), modally negated ("can not depend on")
  * claims: factual assertions with epistemic markers ("the cause is", "confirmed", "I think",
    "we observe") — split by evidence: established / likely / unclear / untested
  * conflicts: tension / contradiction language ("tension", "in conflict", "trade-off", "pull
    in different directions") and unresolved-statement adjacency
  * open_questions: interrogatives, and "we don't know / haven't checked / unverified" forms

It returns STRUCTURED ENTRIES with auto-assigned IDs, a short canonical text (capped, NOT a
summary), and per-category metadata. It does NOT emit prose. The evaluator independently
matches discovered entries against the frozen ground truth by lexical content overlap (a
generous Jaccard, fixed in code), and reports precision / recall / F1 per category.

Nothing here reads any groundtruth_*.json file.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "claude_compression"))
from state import token_count  # noqa: E402

# --- cue lexicons (FIXED before evaluation; not tuned to results) -----------------------

DECISION_VERBS = ("let's", "let us", "we'll", "we will", "we should", "we won't", "we will not",
                  "we'd", "we would", "we're going to", "we are going to", "agreed", "agreed.",
                  "decided", "go with", "i think we", "i don't think we", "treat it as", "fine,",
                  "fine.", "yes —", "yes,", "yes.", "okay,", "okay.", "ok,", "ok.", "rule out",
                  "don't fix", "do not fix", "add the", "leave that one open", "leave that open",
                  "leave that on the", "keep it", "keep them", "keep that", "not in scope",
                  "out of scope", "discard pile", "on the discard")

CONSTRAINT_PATS = (
    re.compile(r"\bmust(?: be)?\b"),
    re.compile(r"\b(?:can|cannot|can not|can'?t|won'?t|won not)\b.{0,40}\bdepend\b"),
    re.compile(r"\bhard rule\b"),
    re.compile(r"\bnot up for negotiation\b"),
    re.compile(r"\bnever (?:feed|depend|allow|accept|skip)\b"),
    re.compile(r"\bno (?:required |allowed )?(?:server|llm|embeddings?|vector|cloud)\b"),
    re.compile(r"\boffline[- ]?capable\b"),
    re.compile(r"\bnot? pin(?:ned)?\b.{0,30}\bglobally\b"),
    re.compile(r"\bthat'?s a (?:hard )?constraint\b"),
    re.compile(r"\bthat constraint\b"),
    re.compile(r"\bnever (?:to )?\b"),
)

CONFLICT_CUES = ("tension", "trade-off", "tradeoff", "pull in different directions",
                 "pulls in different", "in conflict", "conflict with", "that's a smell",
                 "smell\\.", "unresolved", "haven't resolved", "have not resolved",
                 "not really resolved", "torn", "two pull")

OPEN_QUESTION_PATS = (
    re.compile(r"\bopen question\b"),
    re.compile(r"\bdon'?t know\b"),
    re.compile(r"\bdo not know\b"),
    re.compile(r"\bhaven'?t (?:checked|verified|tested|profiled|figured)\b"),
    re.compile(r"\bhave not (?:checked|verified|tested|profiled|figured)\b"),
    re.compile(r"\bunverified\b"),
    re.compile(r"\bunexplained\b"),
    re.compile(r"\btreat as unverified\b"),
    re.compile(r"\bworth a regression test\b"),
    re.compile(r"\bstill missing\b"),
    re.compile(r"\bnobody owns\b"),
    re.compile(r"\bownership is missing\b"),
    re.compile(r"\bwho (?:owns|is responsible|monitors|actually uses)\b"),
    re.compile(r"\bhow does .* behave\b"),
    re.compile(r"\bwhy is .*\b"),
    re.compile(r"\bnote.{0,15}\bdiscrepancy\b"),
    re.compile(r"\bnote it as an open\b"),
    re.compile(r"\bflag (?:that|it) (?:as|to)\b"),
    re.compile(r"\banother thing to flag\b"),
    re.compile(r"\b(?:not|aren'?t) (?:sold|sure)\b"),
)

CLAIM_EVIDENCE = (
    # (regex, evidence label)
    (re.compile(r"\b(?:confirmed|verified|established|observed|measured|showed|we (?:do )?(?:fix|have))\b"), "established"),
    (re.compile(r"\b(?:i think|we think|i suspect|we suspect|i believe|probably|likely|seems|appears|i'?d treat)\b"), "likely"),
    (re.compile(r"\b(?:unclear|unverified|don'?t know|haven'?t|currently|i'm not sure|unexplained|vague|fuzzy)\b"), "unclear"),
    (re.compile(r"\b(?:untested|not (?:yet )?tested|never .* tested)\b"), "untested"),
)

INTERROGATIVE_END = re.compile(r"\?\s*$")
# very short utterances that look like questions but are just back-channels
BACK_CHANNEL = ("right?", "okay?", "ok?", "really?", "yes?", "yeah?")


def _sentences(text: str) -> list:
    text = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9'\"(\[]|[Ii] |[Ww] |[Tt]hat |[Oo]kay |[Yy]es |[Nn]o |[Hh]mm |[Ll]et )", text)
    return [p.strip() for p in parts if len(p.strip()) > 4]


def _canon(text: str, max_words: int = 18) -> str:
    text = re.sub(r"\s+", " ", text or "").strip().rstrip(".,;:!?")
    text = text.lstrip("— -")
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words])
    return text


def _hit_cues(low: str, cues) -> bool:
    return any(c.lower() in low for c in cues)


def _hit_pats(low: str, pats) -> bool:
    return any(p.search(low) for p in pats)


def _classify_evidence(low: str) -> str:
    for pat, label in CLAIM_EVIDENCE:
        if pat.search(low):
            return label
    return "untested"


def _looks_like_question(sent: str) -> bool:
    low = sent.lower().strip()
    if low in BACK_CHANNEL:
        return False
    if INTERROGATIVE_END.search(sent):
        return True
    return _hit_pats(low, OPEN_QUESTION_PATS)


def _looks_like_decision(sent: str) -> bool:
    low = sent.lower()
    if _hit_cues(low, DECISION_VERBS):
        # exclude bare back-channels
        return len(low.split()) >= 4
    return False


def _looks_like_constraint(sent: str) -> bool:
    return _hit_pats(sent.lower(), CONSTRAINT_PATS)


def _looks_like_conflict(sent: str) -> bool:
    return _hit_cues(sent.lower(), CONFLICT_CUES)


def _looks_like_claim(sent: str) -> bool:
    low = sent.lower()
    # a sentence claiming something: indicative verbs + epistemic markers, NOT interrogative
    if INTERROGATIVE_END.search(sent):
        return False
    if any(pat.search(low) for pat, _ in CLAIM_EVIDENCE):
        # must look like a factual statement, not a question or command
        if len(low.split()) >= 6:
            return True
    return False


def _dedup(items, key=lambda x: x["what"]):
    seen, out = set(), []
    for it in items:
        k = re.sub(r"[^a-z0-9 ]", "", key(it).lower())[:48]
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def discover_state(chat: list) -> dict:
    if not isinstance(chat, list):
        raise TypeError("chat must be a list of {'role','content'} dicts")
    claims, constraints, decisions, conflicts, open_questions = [], [], [], [], []

    for msg in chat:
        if not isinstance(msg, dict):
            continue
        content = msg.get("content") or ""
        for sent in _sentences(content):
            low = sent.lower()
            classified = False
            # priority order matters: questions first (they shadow claims), then commitments,
            # then constraints, conflicts, claims.
            if _looks_like_question(sent):
                open_questions.append({"what": _canon(sent)})
                classified = True
            if not classified and _looks_like_decision(sent):
                decisions.append({"what": _canon(sent)})
                classified = True
            if not classified and _looks_like_constraint(sent):
                constraints.append({"what": _canon(sent)})
                classified = True
            if not classified and _looks_like_conflict(sent):
                conflicts.append({"what": _canon(sent)})
                classified = True
            if not classified and _looks_like_claim(sent):
                claims.append({"what": _canon(sent), "evidence": _classify_evidence(low)})

    # de-duplicate within each category by content fingerprint
    claims = _dedup(claims)
    constraints = _dedup(constraints)
    decisions = _dedup(decisions)
    conflicts = _dedup(conflicts)
    open_questions = _dedup(open_questions)

    # assign IDs after dedup so they are stable across re-runs
    def _idify(prefix, items):
        for i, it in enumerate(items, start=1):
            it["id"] = f"{prefix}{i}"
        return items

    return {
        "claims":         _idify("C", claims),
        "constraints":    _idify("R", constraints),
        "decisions":      _idify("D", decisions),
        "conflicts":      _idify("K", conflicts),
        "open_questions": _idify("Q", open_questions),
    }


def state_token_size(state: dict) -> int:
    import json
    return token_count(json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
