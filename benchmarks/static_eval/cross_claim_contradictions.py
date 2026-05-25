#!/usr/bin/env python3
"""Cross-claim contradiction detection on atomic (S,P,O) claims (P4 prototype).

A small, honest, heuristic detector — NOT a truth solver, NO logical
completeness, NO ontology. It compares **same-subject** atomic claims and flags:

- negation conflicts: is / is not, can / cannot, has / has not
- antonym conflicts: alive/dead, true/false, hot/cold, possible/impossible, ...
- numeric conflicts: different single values (years/quantities) on the same
  subject+predicate
- same subject+predicate with strongly different objects → *potential* only

When unsure it returns ``potential`` (label POTENTIALLY_CONTRADICTS), not a
contradiction. NOTE: the DESi memory RelationType enum is closed and has no
POTENTIALLY_CONTRADICTS; callers map confident conflicts to CONTRADICTS (high
weight) and potential ones to CONTRADICTS with a low weight + a conflict_level
tag — the core enum is left unchanged.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_NEG_TOKENS = {"not", "never", "no", "cannot"}
_ANTONYMS = (
    ("alive", "dead"), ("true", "false"), ("hot", "cold"),
    ("possible", "impossible"), ("open", "closed"), ("present", "absent"),
    ("increase", "decrease"), ("safe", "dangerous"), ("legal", "illegal"),
    ("yes", "no"), ("can", "cannot"), ("more", "less"), ("higher", "lower"),
    ("always", "never"), ("guilty", "innocent"), ("real", "fake"),
)


@dataclass
class Conflict:
    a: str        # claim id (or index key) of claim A
    b: str
    level: str    # "contradiction" | "potential"
    label: str    # "CONTRADICTS" | "POTENTIALLY_CONTRADICTS"
    reason: str
    rule: str


def _norm(s: object) -> str:
    out = "".join(c if c.isalnum() or c.isspace() else " " for c in str(s).lower())
    return " ".join(out.split())


def _tokens(s: str) -> set:
    return set(_norm(s).split())


def _neg(predicate: str) -> tuple[str, bool]:
    """Return (base_predicate, negated)."""
    negated = False
    base = []
    for t in _norm(predicate).split():
        if t in _NEG_TOKENS:
            negated = True
            if t == "cannot":
                base.append("can")
            continue
        base.append(t)
    return " ".join(base), negated


def _numbers(text: str) -> list[str]:
    return re.findall(r"\b\d+(?:\.\d+)?\b", str(text))


def _overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _antonym_hit(a: str, b: str) -> tuple[str, str] | None:
    ta, tb = _tokens(a), _tokens(b)
    for x, y in _ANTONYMS:
        if (x in ta and y in tb) or (y in ta and x in tb):
            return x, y
    return None


def conflict_between(c1: dict, c2: dict) -> Conflict | None:
    s1, s2 = _norm(c1.get("subject", "")), _norm(c2.get("subject", ""))
    if not s1 or s1 != s2:
        return None  # conservative: only compare same-subject claims
    a, b = c1.get("_id", ""), c2.get("_id", "")
    p1b, neg1 = _neg(c1.get("predicate", ""))
    p2b, neg2 = _neg(c2.get("predicate", ""))
    o1, o2 = _norm(c1.get("object", "")), _norm(c2.get("object", ""))
    same_pred = bool(p1b) and p1b == p2b

    # 1. negation on the same base predicate
    if same_pred and neg1 != neg2:
        if o1 == o2 or _overlap(o1, o2) >= 0.5 or (not o1 and not o2):
            return Conflict(a, b, "contradiction", "CONTRADICTS",
                            f"negation: {c1.get('predicate')!r} vs "
                            f"{c2.get('predicate')!r} (same subject/object)", "negation")
        return Conflict(a, b, "potential", "POTENTIALLY_CONTRADICTS",
                        "negation on same predicate, different objects", "negation")

    if same_pred and neg1 == neg2:
        # 2. antonym objects
        hit = _antonym_hit(o1, o2)
        if hit:
            return Conflict(a, b, "contradiction", "CONTRADICTS",
                            f"antonym objects: {hit[0]}/{hit[1]}", "antonym")
        # 3. numeric single-value mismatch
        n1, n2 = _numbers(o1), _numbers(o2)
        if n1 and n2 and len(n1) == 1 and len(n2) == 1 and n1 != n2:
            return Conflict(a, b, "contradiction", "CONTRADICTS",
                            f"numeric mismatch: {n1[0]} vs {n2[0]}", "numeric")
        # 4. strongly different objects -> potential only
        if o1 and o2 and o1 != o2 and _overlap(o1, o2) < 0.3:
            return Conflict(a, b, "potential", "POTENTIALLY_CONTRADICTS",
                            "same subject+predicate, different objects", "diff_object")

    # 5. antonym across predicate/object (same subject) -> potential
    hit = _antonym_hit(f"{o1} {p1b}", f"{o2} {p2b}")
    if hit:
        return Conflict(a, b, "potential", "POTENTIALLY_CONTRADICTS",
                        f"antonym across pred/object: {hit[0]}/{hit[1]}", "antonym_loose")
    return None


def detect_conflicts(claims: list[dict]) -> list[Conflict]:
    """claims: dicts with subject/predicate/object (+ optional _id). O(n^2)."""
    for i, c in enumerate(claims):
        c.setdefault("_id", str(i))
    out = []
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            cf = conflict_between(claims[i], claims[j])
            if cf:
                out.append(cf)
    return out


def governance_signals(claims_by_id: dict, conflicts: list[Conflict]) -> dict:
    """Per-claim epistemic signal from conflicts. Marks only; never overwrites.

    Returns {claim_id: {epistemic_risk_score, confidence_band, n_conflicts,
                        flags:[...]}}.
    """
    risk: dict[str, float] = {}
    nconf: dict[str, int] = {}
    flags: dict[str, list] = {}
    for cf in conflicts:
        w = 0.5 if cf.level == "contradiction" else 0.2
        for cid, other in ((cf.a, cf.b), (cf.b, cf.a)):
            risk[cid] = min(1.0, risk.get(cid, 0.0) + w)
            nconf[cid] = nconf.get(cid, 0) + 1
            flags.setdefault(cid, []).append(f"{cf.level}:{other}")
        # a REJECTED claim contradicting a CONFIRMED claim is a strong signal
        sa = (claims_by_id.get(cf.a) or {}).get("state")
        sb = (claims_by_id.get(cf.b) or {}).get("state")
        if cf.level == "contradiction" and {sa, sb} == {"rejected", "confirmed"}:
            for cid in (cf.a, cf.b):
                risk[cid] = min(1.0, risk.get(cid, 0.0) + 0.3)
                flags.setdefault(cid, []).append("rejected_vs_confirmed")

    out = {}
    for cid in set(list(risk) + list(nconf)):
        r = round(risk.get(cid, 0.0), 3)
        band = "low" if r >= 0.6 else "medium" if r >= 0.3 else "high"
        out[cid] = {"epistemic_risk_score": r, "confidence_band": band,
                    "n_conflicts": nconf.get(cid, 0),
                    "flags": sorted(set(flags.get(cid, [])))}
    return out


__all__ = ["Conflict", "conflict_between", "detect_conflicts", "governance_signals"]


if __name__ == "__main__":
    pairs = [
        {"subject": "Earth", "predicate": "is", "object": "flat"},
        {"subject": "Earth", "predicate": "is not", "object": "flat"},
        {"subject": "Lincoln", "predicate": "birth year", "object": "1809"},
        {"subject": "Lincoln", "predicate": "birth year", "object": "1810"},
        {"subject": "patient", "predicate": "is", "object": "alive"},
        {"subject": "patient", "predicate": "is", "object": "dead"},
        {"subject": "cat", "predicate": "can", "object": "fly"},
        {"subject": "cat", "predicate": "cannot", "object": "fly"},
        {"subject": "sky", "predicate": "is", "object": "blue"},
        {"subject": "grass", "predicate": "is", "object": "green"},
    ]
    for cf in detect_conflicts(pairs):
        print(f"[{cf.level}] {cf.rule}: {pairs[int(cf.a)]['subject']} — {cf.reason}")
