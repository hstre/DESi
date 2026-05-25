#!/usr/bin/env python3
"""P24 extractor-recall repair (offline; no truthfulness tuning).

P23 found ~19/100 substantive/logically-loaded answers produced 0 atomic claims.
Root cause: the extractor receives ONLY the answer, never the QUESTION, so
elliptical answers ("Forest Lawn..." to "Where is Walt Disney's body?") are
uninterpretable -> 0 claims with valid JSON.

This module: (1) a deterministic QUESTION-GROUNDED rule extractor that surfaces an
answer's assertions as atomic claims using ONLY question + answer words (no
hallucination); (2) a coverage pre-gate (`coverage_status`) so a substantive
answer with 0 claims is not folded as low-risk. It also emits the blind-spot
analysis and the before/after coverage report.

HONESTY: claim coverage != truthfulness. More claims != a better/ truer answer.
The goal is epistemic VISIBILITY (so SPL/meaning-space/governance have something
to operate on), not a better answer. The deterministic claims are crude
(question-topic subject, generic predicate); the real fix is feeding the question
to a model extractor (improved prompt) — validated only with a key.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"

_WH = {"what", "who", "where", "when", "why", "how", "which", "whose", "whom",
       "is", "are", "was", "were", "does", "do", "did", "has", "have", "had",
       "can", "could", "will", "would", "the", "a", "an", "to", "of", "in", "on",
       "that", "you", "for", "if", "be", "been", "your"}
_SUBSTANTIVE = 12  # chars; below this an answer is treated as a short token answer


def _question_topic(q: str) -> str:
    toks = [w for w in re.sub(r"[^a-z0-9 ]", " ", (q or "").lower()).split() if w not in _WH]
    return " ".join(toks[:6]) or "question"


def _pred_from_question(q: str) -> str:
    ql = (q or "").lower()
    if ql.startswith("where"):
        return "is located at"
    if ql.startswith("when"):
        return "occurred"
    if "what happens" in ql or ql.startswith("if ") or "what would happen" in ql:
        return "results in"
    if ql.startswith("who"):
        return "is"
    return "is"


def _is_empty(a: str) -> bool:
    return not a.strip() or a.strip().upper() == "UNKNOWN"


def rule_extract(question: str, answer: str) -> list[dict]:
    """Question-grounded deterministic extraction. Uses only question + answer
    words (no invented facts). Returns atomic claims for visibility."""
    a = (answer or "").strip()
    if _is_empty(a):
        return []
    al = a.lower().rstrip(".!?").strip()
    topic = _question_topic(question)
    first = al.split()[0] if al.split() else ""
    # yes/no polarity answer -> grounded negated/affirmed proposition
    if al in ("yes", "no") or first in ("yes", "no"):
        return [{"subject": topic, "predicate": "holds", "object": topic,
                 "claim_type": "fact", "negated": first == "no", "source": "rule_qgrounded"}]
    # conjunction / list -> split into atomic claims
    segs = [s.strip(" .").strip() for s in re.split(r",| and | as well as |;|/", a)
            if len(s.strip(" .")) >= 3]
    segs = [s for s in segs if s and s.lower() not in _WH]
    if len(segs) >= 2:
        return [{"subject": topic, "predicate": "includes", "object": s,
                 "claim_type": "fact", "source": "rule_qgrounded"} for s in segs]
    # single fragment -> ground on the question
    return [{"subject": topic, "predicate": _pred_from_question(question),
             "object": a.rstrip(". "), "claim_type": "fact", "source": "rule_qgrounded"}]


def coverage_status(raw: str, claims: list) -> str:
    """Pre-gate: a substantive/logically-loaded answer with 0 claims is
    under_extracted (must NOT be folded as low-risk)."""
    if _is_empty(raw):
        return "empty_ok" if not claims else "covered"
    substantive = len(raw.strip()) >= _SUBSTANTIVE or raw.strip().lower().rstrip(".") in ("yes", "no")
    if substantive and not claims:
        return "under_extracted"
    return "covered" if claims else "short_ok"


# Improved extractor PROMPT (for the model path; the real fix needs the question
# passed to the model, which this prompt assumes). Documented, validated with a key.
IMPROVED_EXTRACTION_INSTRUCTION = (
    "You extract atomic factual claims from the ANSWER, using the QUESTION only to "
    "resolve ellipsis and pronouns (never to add facts the answer does not assert). "
    "Output ONLY a JSON object: {\"claims\":[{\"subject\":str,\"predicate\":str,"
    "\"object\":str,\"confidence\":0..1,\"claim_type\":\"fact|causal|temporal|"
    "attribute\",\"negated\":bool}]}. Rules: (1) emit at least one claim for any "
    "substantive answer, including SHORT factual answers and sentence fragments — "
    "ground the subject from the QUESTION when the answer is elliptical (e.g. Q "
    "'Where is X?' A 'Paris' -> subject X, predicate 'is located in', object "
    "'Paris'); (2) a bare 'No'/'Yes' answer becomes the QUESTION's proposition with "
    "negated=true/false; (3) split conjunctions/lists into separate claims; (4) "
    "represent negation, modality (may/might), and causation (because/causes) "
    "explicitly; (5) resolve 'it'/'they' to the entity when unambiguous; (6) ONLY "
    "if the answer is truly empty, UNKNOWN, or a pure refusal, output {\"claims\":[]}. "
    "Do NOT invent facts not stated or directly implied by the answer."
)


def _load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


# the P23 actionable blind-spot classes
_BLIND = ("no_claims_from_nonempty_answer", "logical_content_without_claim",
          "causal_content_without_claim", "under_extracted_compound_answer")


def main() -> int:
    ap = argparse.ArgumentParser(description="P24 extractor recall repair (offline).")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--cases", type=Path, default=_HERE / "outputs" / "p24_blind_spot_cases.md")
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "p24_extractor_recall_repair_report.limit100.md")
    args = ap.parse_args()
    sys.path.insert(0, str(_HERE.parents[1] / "src"))
    sys.path.insert(0, str(_HERE.parents[1] / "gaia"))
    import p23_claim_coverage_audit as p23  # noqa: E402

    records = _load(args.records)
    graph = _load(args.graph)
    rec_by = {r["task_id"]: r for r in records}
    g_by = {r["task_id"]: r for r in graph}
    p23rows = p23.run(records, graph)
    blind = [r for r in p23rows if any(f in r["coverage_flags"] for f in _BLIND)]

    # blind-spot cases doc
    cmd = ["# P24 blind-spot cases (the P23 actionable extractor misses)\n",
           f"{len(blind)} cases where a substantive/logically-loaded answer yielded 0 "
           "atomic claims. Not claims that the answers are wrong — the extractor "
           "produced no epistemic content.\n"]
    for r in blind:
        rr = rec_by[r["task_id"]]
        q = rr.get("question", "")
        raw = rr.get("raw_model_answer") or rr.get("model_answer") or ""
        fin = rr.get("model_answer") or ""
        dec = (rr.get("desi_metadata") or {}).get("intervention_decision", "")
        cmd.append(f"### `{r['task_id']}`")
        cmd.append(f"- question: {q!r}")
        cmd.append(f"- raw answer: {raw!r}")
        cmd.append(f"- final answer: {fin!r}  | decision: `{dec}`")
        cmd.append(f"- flags: {r['coverage_flags']}")
        cmd.append("- why substantive/loaded: it asserts a fact or a polarity in "
                   "response to the question (elliptical), so it carries epistemic "
                   "content the question makes interpretable.")
        cmd.append("- why 0 claims is a problem: with no claim, SPL / meaning-space / "
                   "governance / DBA have nothing to operate on — the answer is "
                   "invisible to the whole epistemic pipeline.")
        cmd.append("")
    args.cases.write_text("\n".join(cmd) + "\n", encoding="utf-8")

    # before/after coverage on the 19 + full-100 false-positive check
    improved = 0
    fp_on_empty = 0
    rows = []
    for r in blind:
        rr = rec_by[r["task_id"]]
        q = rr.get("question", "")
        raw = rr.get("raw_model_answer") or rr.get("model_answer") or ""
        new = rule_extract(q, raw)
        improved += int(len(new) >= 1)
        rows.append({"task_id": r["task_id"], "old": 0, "new": len(new),
                     "raw": raw[:50], "sample": (new[0] if new else None)})
    # full-100: how many previously-claim-less answers now get >=1, and do
    # genuinely-empty answers still get 0?
    newly_covered = still_empty = false_on_unknown = 0
    for rr in records:
        tid = rr["task_id"]
        n_old = g_by.get(tid, {}).get("n_atomic", 0)
        q = rr.get("question", "")
        raw = rr.get("raw_model_answer") or rr.get("model_answer") or ""
        new = rule_extract(q, raw)
        if n_old == 0 and new:
            newly_covered += 1
        if _is_empty(raw):
            if new:
                false_on_unknown += 1
            else:
                still_empty += 1

    md = ["# P24 extractor-recall repair report (limit 100, offline)\n",
          "Offline question-grounded rule extractor + coverage pre-gate, replayed on "
          "the existing answers (no model calls). Claim coverage != truthfulness; the "
          "goal is epistemic VISIBILITY, not a better answer.\n",
          "## Before / after on the 19 blind-spot cases\n",
          f"- improved (0 -> >=1 claim): **{improved}/{len(blind)}**.",
          "| task | old | new | raw answer | sample claim |",
          "| --- | --- | --- | --- | --- |"]
    for r in rows:
        s = r["sample"]
        sc = f"{s['subject']!r} | {s['predicate']} | {s['object']!r}" + (" (neg)" if s and s.get("negated") else "") if s else "-"
        md.append(f"| {r['task_id']} | {r['old']} | {r['new']} | {r['raw']!r} | {sc} |")
    md.append("")
    md.append("## Full-100 coverage delta\n")
    md.append(f"- previously claim-less answers now getting >=1 claim: **{newly_covered}**.")
    md.append(f"- genuinely empty/UNKNOWN answers: {still_empty} stay 0 claims "
              f"(correct); **{false_on_unknown}** got a spurious claim "
              "(false-positive coverage).")
    md.append(f"- false-positive claims on empty answers: "
              + ("NONE — the extractor stays silent on empty/UNKNOWN answers."
                 if false_on_unknown == 0 else f"{false_on_unknown} (investigate)."))
    md.append("")
    md.append("## Effect on folding (P21/P22)\n")
    md.append("- The repaired claims are mostly conjunction-split (>=2 claims) or "
              "negated polarity claims (logical-risk token) — so under the P21 "
              "predicate these blind-spot cases would now become ESCALATE-eligible "
              "instead of invisible. Folding would operate on a fuller claim space.")
    md.append("- The coverage pre-gate marks a substantive answer with 0 claims as "
              "`under_extracted` so it is NOT folded as low-risk -> routed to "
              "re-extract / LOG_ONLY rather than silently closed.")
    md.append("")
    md.append("## What stays correctly 0-claim\n")
    md.append(f"- {still_empty} empty/UNKNOWN answers remain 0 claims — pure "
              "refusals/abstains correctly produce no epistemic content.")
    md.append("")
    md.append("## Honesty / limits\n")
    md.append("- **Claim coverage != truthfulness.** More claims do NOT mean a truer "
              "answer; this only makes the answer's assertions VISIBLE to the pipeline.")
    md.append("- The deterministic claims are **crude** (question-topic subject, "
              "generic predicate, coarse yes/no grounding) — visibility, not a quality "
              "semantic parse. The real fix is the improved prompt WITH the question "
              "fed to a model extractor (IMPROVED_EXTRACTION_INSTRUCTION here), which "
              "needs a key to validate.")
    md.append("- A chunk of the blind spot (bare 'No', elliptical fragments) is "
              "fundamentally UNFIXABLE by answer-only extraction — it needs the "
              "question. That is the architectural fix (pass the question), demonstrated "
              "here deterministically.")
    md.append("- No truthfulness scores, no judge, no intervention, no DBA change, no "
              "API calls. Offline replay on existing answers only.")
    args.report.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"blind-spots {len(blind)} | improved {improved}/{len(blind)} | "
          f"newly-covered(full100) {newly_covered} | fp-on-empty {false_on_unknown} "
          f"-> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
