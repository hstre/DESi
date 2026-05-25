#!/usr/bin/env python3
"""P2 (rule-based) vs P3 (model-assisted) claim extraction — comparison demo.

Runs both extractors on the same answers (a canonical example + a few real
TruthfulQA answers) and writes a Markdown report. P3 makes real LLM calls
(Granite preferred → DeepSeek fallback); P2 is offline. Honest prototype: P3 is
model-dependent and can hallucinate; a source-overlap heuristic flags low-overlap
P3 claims (paraphrase or possible hallucination). Tokens from env only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from freetext_claim_extractor import extract_subclaims        # noqa: E402
from model_claim_extractor import extract_claims_model        # noqa: E402

DEFAULT_INPUT = (Path(__file__).resolve().parent / "outputs"
                 / "truthfulqa.deepseek-v4.desi_intervened.refined.limit50.jsonl")
CANONICAL = "Virginia Woolf was born in London in 1882 and became a famous writer."
_STOP = {"the", "a", "an", "of", "is", "was", "were", "in", "to", "and", "on",
         "it", "be", "as", "by", "for", "that", "this", "are"}


def _answer_text(record: dict) -> str:
    return ((record.get("raw_model_answer") or "").strip()
            or (record.get("model_answer") or "").strip())


def _grounded(claim: dict, source: str) -> bool:
    src = set(re.findall(r"[a-z0-9]+", source.lower()))
    blob = f"{claim['subject']} {claim['predicate']} {claim['object']}".lower()
    toks = set(re.findall(r"[a-z0-9]+", blob)) - _STOP
    if not toks:
        return True
    return len(toks & src) / len(toks) >= 0.5


def _pick_real(path: Path, n: int) -> list[str]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ans = _answer_text(json.loads(line))
        if ans and len(extract_subclaims(ans)) >= 2:
            out.append(ans)
        if len(out) >= n:
            break
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="P2 vs P3 claim extraction demo.")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--n-real", type=int, default=4)
    p.add_argument("--report", type=Path, default=Path(__file__).resolve().parent
                   / "outputs" / "model_claim_extraction_report.md")
    args = p.parse_args()

    answers = [CANONICAL] + _pick_real(args.input, args.n_real)
    rows = []
    methods = Counter()
    json_status = Counter()
    ungrounded_total = p3_total = 0

    for ans in answers:
        p2 = [sc.text for sc in extract_subclaims(ans)]
        p3 = extract_claims_model(ans)
        methods[p3["extraction_method"]] += 1
        json_status["raw_ok" if p3["raw_json_ok"] else
                    "recovery" if p3["json_recovery_used"] else "fallback"] += 1
        grounded_flags = [_grounded(c, ans) for c in p3["claims"]]
        ungrounded_total += sum(1 for g in grounded_flags if not g)
        p3_total += len(p3["claims"])
        rows.append({"answer": ans, "p2": p2, "p3": p3, "grounded": grounded_flags})

    md = ["# Claim extraction: P2 (rule-based) vs P3 (model-assisted)\n",
          f"- Answers compared: **{len(answers)}**",
          f"- P3 extraction methods used: `{dict(methods)}`",
          f"- P3 JSON status: `{dict(json_status)}`",
          f"- P3 claims with low source-overlap (paraphrase or possible "
          f"hallucination): **{ungrounded_total}/{p3_total}**\n",
          "## Side-by-side\n"]
    for r in rows:
        md.append(f"**Answer:** {r['answer'][:140]!r}")
        md.append(f"- _P2 rule-based_ ({len(r['p2'])}):")
        for t in r["p2"]:
            md.append(f"    - {t!r}")
        p3 = r["p3"]
        md.append(f"- _P3 {p3['extraction_method']}_ "
                  f"(raw_ok={p3['raw_json_ok']}, recovery={p3['json_recovery_used']}, "
                  f"fallback={p3['fallback_used']}; {len(p3['claims'])} claims):")
        for c, g in zip(p3["claims"], r["grounded"]):
            flag = "" if g else "  ⚠ low-overlap"
            md.append(f"    - ({c['claim_type']}, {c['confidence']}) "
                      f"{c['subject']!r} — {c['predicate']!r} — {c['object']!r}{flag}")
        md.append("")

    md.append("## Where P3 is better than P2\n")
    md.append("- **Coreference / subject resolution:** P3 resolves pronouns and "
              "implied subjects into (subject, predicate, object) triples where P2 "
              "leaves `it` / verb-initial fragments.")
    md.append("- **Date / temporal logic:** P3 labels temporal claims and parses "
              "dates more sensibly than P2's brittle year regex (which mis-split "
              '"August 2, 1776").')
    md.append("- **Sentence structure:** P3 handles nested/relative clauses and "
              "`because of <noun>` that P2 fragments.\n")
    md.append("## Where P3 is weak / risky\n")
    md.append("- **Hallucination:** P3 can emit triples not present in the text "
              "(flagged ⚠ by the source-overlap heuristic — note this also flags "
              "legitimate paraphrases, so it is a *risk* signal, not proof).")
    md.append("- **Confidence is self-reported** by the model and not calibrated.")
    md.append("- **JSON stability:** strict-JSON adherence varies; the parser has "
              "a recovery step and falls back to P2 when parsing fails "
              "(see the JSON-status counts above).")
    md.append("- **Granite unavailable here:** Granite is preferred as the "
              "structured extractor, but the test token's HF Inference providers do "
              "not serve it, so every Granite attempt falls back to DeepSeek "
              "(see `attempts` in the JSONL).\n")
    md.append("## Honesty\n")
    md.append("P3 is a **model-assisted prototype**, not a semantic-graph parser. "
              "It is model-dependent, potentially hallucination-prone, and produces "
              "candidate claims — but it is structurally much closer to real claim "
              "extraction (typed subject/predicate/object triples) than P2's "
              "string-splitting.")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Compared {len(answers)} answers (P3 methods={dict(methods)}, "
          f"json={dict(json_status)}). Report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
