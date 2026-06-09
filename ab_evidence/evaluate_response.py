"""Evaluate a Claude response against the FROZEN ground truth — five primary metrics.

For each expected item (claim / constraint / decision / conflict / open_question) we test
whether the response text mentions it via content-token Jaccard >= MATCH_THRESHOLD against the
GT body. The threshold is fixed BEFORE running — not tuned to results.

We additionally detect new claims in the response that have NO ground-truth match —
hallucinations. (Hallucination detection here is conservative: a response sentence with claim-
shaped vocabulary that doesn't match any GT body counts as a hallucination only if its content-
token Jaccard with every GT entry is below MATCH_THRESHOLD.)
"""
from __future__ import annotations

import re

MATCH_THRESHOLD = 0.25  # fixed BEFORE running, not tuned to results

_STOP = frozenset((
    "the a an of to in on and or is are was were be been being that this these those it its as at "
    "by for with from has have had do does did but if then than so such into out up down over under "
    "about their they them we you i which who not no only any all per also more most some can").split())


def _toks(s: str) -> set:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", (s or "").lower())
            if t not in _STOP and len(t) > 2}


def _jac(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return (len(a & b) / len(a | b)) if (a | b) else 0.0


def _split_units(text: str) -> list:
    """Split response into 'units' = bullet lines OR sentences. Real Claude answers use bullets;
    sentence-splitting alone misses every bullet-style item. We split on newlines first, then
    on sentence terminators inside each non-bullet line."""
    if not text:
        return []
    units = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # treat bullets / numbered lines / headers as one unit each
        if re.match(r"^([\*\-•●]\s+|\d+[.)]\s+|#{1,4}\s+|\*\*[^*]+\*\*\s*$)", line):
            cleaned = re.sub(r"^([\*\-•●]\s+|\d+[.)]\s+|#{1,4}\s+)", "", line).strip()
            cleaned = cleaned.strip("*")
            if cleaned:
                units.append(cleaned)
            continue
        # otherwise split into sentences
        for s in re.split(r"(?<=[.!?])\s+", line):
            s = s.strip()
            if s:
                units.append(s)
    return units


def _recall_against_response(expected_items: list, response_text: str) -> dict:
    """A GT item is preserved iff some response UNIT (bullet OR sentence) Jaccard-matches its body."""
    units = _split_units(response_text)
    matched, missing = [], []
    for e in expected_items:
        eb = _toks(e["what"])
        best = max((_jac(eb, _toks(u)) for u in units), default=0.0) if units else 0.0
        if best >= MATCH_THRESHOLD:
            matched.append({"id": e["id"], "jaccard": round(best, 3)})
        else:
            missing.append({"id": e["id"], "what": e["what"], "best_jaccard": round(best, 3)})
    total = len(expected_items)
    recall = round(len(matched) / total, 3) if total else 1.0
    return {"total": total, "matched": matched, "missing": missing, "recall": recall}


def _hallucinations(response_text: str, gt_all_bodies: list) -> dict:
    """Units in the response that look claim-like but match no GT entry."""
    gt_tok_sets = [_toks(b) for b in gt_all_bodies]
    units = [u for u in _split_units(response_text) if len(u) > 10]
    hallucinated = []
    for u in units:
        ut = _toks(u)
        if len(ut) < 4:        # too short to claim anything
            continue
        # ignore obvious headers / labels (section names the prompt uses)
        if u.lower().startswith(("active constraints", "decisions taken", "open conflicts",
                                  "open questions", "established claims",
                                  "working hypothesis", "ruled out", "quasi-controls used",
                                  "confirmed root cause", "decided fixes", "not yet verified",
                                  "rejected options", "external-comms guardrails")):
            continue
        best = max((_jac(ut, gtok) for gtok in gt_tok_sets), default=0.0)
        if best < MATCH_THRESHOLD:
            hallucinated.append({"sentence": u[:200], "best_gt_jaccard": round(best, 3)})
    return {"count": len(hallucinated), "items": hallucinated[:8]}


def evaluate(response_text: str, ground_truth: dict) -> dict:
    claims     = _recall_against_response(ground_truth["active_claims"],     response_text)
    constraints = _recall_against_response(ground_truth["active_constraints"], response_text)
    decisions  = _recall_against_response(ground_truth["decisions"],         response_text)
    conflicts  = _recall_against_response(ground_truth["open_conflicts"],    response_text)
    questions  = _recall_against_response(ground_truth["open_questions"],    response_text)
    all_bodies = ([c["what"] for c in ground_truth["active_claims"]]
                  + [c["what"] for c in ground_truth["active_constraints"]]
                  + [d["what"] for d in ground_truth["decisions"]]
                  + [k["what"] for k in ground_truth["open_conflicts"]]
                  + [q["what"] for q in ground_truth["open_questions"]])
    halluc = _hallucinations(response_text, all_bodies)
    return {
        "match_threshold": MATCH_THRESHOLD,
        "claim_preservation":      claims,
        "constraint_preservation": constraints,
        "decision_preservation":   decisions,
        "conflict_visibility":     conflicts,
        "open_question_preservation": questions,
        "hallucinations": halluc,
        "primary_success_criteria": {
            "decisions_>=_0.90":   decisions["recall"]   >= 0.90,
            "constraints_>=_0.90": constraints["recall"] >= 0.90,
        },
    }
