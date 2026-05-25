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

# P6: predicate typing. Multi-valued predicates can take several compatible
# objects; single-valued ones should hold one value; the rest are unknown.
_MULTI_VALUED = ("described as", "associated with", "has quality", "has",
                 "includes", "include", "consists of", "contains", "contain",
                 "exports", "export", "produces", "features", "comprises",
                 "is described as")
_SINGLE_VALUED = ("birth year", "death year", "capital of", "is the capital of",
                  "located in", "legal status", "truth value", "boils at",
                  "born in", "died in", "founded in", "year")
_TEMPORAL_BEFORE = {"before", "earlier", "pre", "prior"}
_TEMPORAL_AFTER = {"after", "later", "post"}


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


# --------------------------------------------------------------------------- #
# P6 helpers: object normalisation, predicate typing, temporal order
# --------------------------------------------------------------------------- #
def normalize_object(o: object) -> str:
    """Lower/strip + light unit normalisation (degrees celsius ≈ c, percent)."""
    s = _norm(o)  # _norm already drops punctuation incl. % and °
    s = re.sub(r"\bdegrees?\b", "", s)
    s = re.sub(r"\bcelsius\b", "c", s)
    s = re.sub(r"\bpercent\b", "pct", s)
    return " ".join(s.split())


def _single_number(text: str) -> str | None:
    nums = _numbers(text)
    return nums[0] if len(nums) == 1 else None


def predicate_kind(predicate: str, o1: str, o2: str) -> str:
    """Classify a (same) predicate given its two objects."""
    p = _norm(predicate)
    if _single_number(o1) and _single_number(o2):
        return "numeric_value"
    if any(k in p for k in _MULTI_VALUED):
        return "multi_valued"
    if any(k in p for k in _SINGLE_VALUED):
        return "single_valued"
    return "unknown"


def _temporal_dir(text: str) -> str | None:
    t = _tokens(text)
    if t & _TEMPORAL_BEFORE:
        return "before"
    if t & _TEMPORAL_AFTER:
        return "after"
    return None


def temporal_inverse(p1: str, o1: str, p2: str, o2: str) -> bool:
    """True if one claim says before-<ref> and the other after-<same ref>."""
    d1, d2 = _temporal_dir(f"{p1} {o1}"), _temporal_dir(f"{p2} {o2}")
    if not (d1 and d2 and d1 != d2):
        return False
    r1 = _tokens(o1) - _TEMPORAL_BEFORE - _TEMPORAL_AFTER
    r2 = _tokens(o2) - _TEMPORAL_BEFORE - _TEMPORAL_AFTER
    if not r1 and not r2:
        return True
    return (len(r1 & r2) / max(1, len(r1 | r2))) >= 0.3


def conflict_between(c1: dict, c2: dict, *, predicate_types: bool = True) -> Conflict | None:
    s1, s2 = _norm(c1.get("subject", "")), _norm(c2.get("subject", ""))
    if not s1 or s1 != s2:
        return None  # conservative: only compare same-subject claims
    a, b = c1.get("_id", ""), c2.get("_id", "")
    p1b, neg1 = _neg(c1.get("predicate", ""))
    p2b, neg2 = _neg(c2.get("predicate", ""))
    if predicate_types:
        o1, o2 = normalize_object(c1.get("object", "")), normalize_object(c2.get("object", ""))
    else:
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

    # 2. temporal order inversion (P6): X before <ref> vs X after <ref>
    if predicate_types and temporal_inverse(p1b, o1, p2b, o2):
        return Conflict(a, b, "contradiction", "CONTRADICTS",
                        "temporal order inversion (before vs after, same reference)",
                        "temporal_order")

    if same_pred and neg1 == neg2:
        # 3. antonym objects (boolean attribute)
        hit = _antonym_hit(o1, o2)
        if hit:
            return Conflict(a, b, "contradiction", "CONTRADICTS",
                            f"antonym objects: {hit[0]}/{hit[1]}", "antonym")
        # 4. numeric single-value mismatch
        if _single_number(o1) and _single_number(o2) and _single_number(o1) != _single_number(o2):
            return Conflict(a, b, "contradiction", "CONTRADICTS",
                            f"numeric mismatch: {_single_number(o1)} vs {_single_number(o2)}",
                            "numeric")
        # 5. strongly different objects
        if o1 and o2 and o1 != o2 and _overlap(o1, o2) < 0.3:
            if predicate_types:
                kind = predicate_kind(p1b, o1, o2)
                if kind == "multi_valued":
                    return None  # different objects are complementary, not a conflict
                return Conflict(a, b, "potential", "POTENTIALLY_CONTRADICTS",
                                f"different objects on {kind} predicate", f"diff_object/{kind}")
            return Conflict(a, b, "potential", "POTENTIALLY_CONTRADICTS",
                            "same subject+predicate, different objects", "diff_object")

    # 6. antonym across predicate/object (same subject) -> potential
    hit = _antonym_hit(f"{o1} {p1b}", f"{o2} {p2b}")
    if hit:
        return Conflict(a, b, "potential", "POTENTIALLY_CONTRADICTS",
                        f"antonym across pred/object: {hit[0]}/{hit[1]}", "antonym_loose")
    return None


def detect_conflicts(claims: list[dict], *, predicate_types: bool = True) -> list[Conflict]:
    """claims: dicts with subject/predicate/object (+ optional _id). O(n^2)."""
    for i, c in enumerate(claims):
        c.setdefault("_id", str(i))
    out = []
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            cf = conflict_between(claims[i], claims[j], predicate_types=predicate_types)
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
