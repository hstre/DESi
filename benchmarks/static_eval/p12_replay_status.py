#!/usr/bin/env python3
"""P12 corrected status report — deterministic replay, NO new API calls.

Re-applies the current P12 intervention policy to the *recorded* limit-100 raw
answers and re-derives the truthfulness classification. Nothing is generated and
no claims are re-extracted; only the answer-level intervention is recomputed, so
provider/generation variance is held fixed (it is the same recorded output every
time). This makes the Original -> P11 -> P12 comparison a causal evaluation of the
policy change alone.

Three policies, all evaluated on the same recorded raw answers:
  * ORIGINAL : the decision recorded in the limit-100 file (pre-P11 live run).
  * P11      : reconstructed from P12 — P11 and P12 are byte-identical except the
               tie branch, where P11 abstained on every high near-tie. So any case
               P12 resolves via the tie resolver maps back to
               abstain_ambiguous_match under P11.
  * P12      : the current policy (desi_intervention), replayed.

Inputs (read-only):
  outputs/truthfulqa.deepseek-v4.desi_intervened_spl.limit100.jsonl
  outputs/truthfulqa.deepseek-v4.desi_claim_graph_spl.limit100.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from desi_intervention import BLOCKING_DECISIONS, apply_desi_intervention  # noqa: E402
from report_truthfulqa import _is_eu, _label  # noqa: E402

_RECORDS = _HERE / "outputs" / "truthfulqa.deepseek-v4.desi_intervened_spl.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.desi_claim_graph_spl.limit100.jsonl"
_ABSTAIN = {"abstain", "abstain_inefficient", "abstain_truncated", "abstain_ambiguous_match"}
# P11 and P12 differ ONLY in the tie branch; these flags mark a case that P12
# routed through the tie resolver (so P11 would have abstained instead).
_TIE_FLAGS = {"tie_resolved_exact_correct", "tie_resolved_exact_incorrect",
              "tie_exact_both", "tie_resolved_phrase_correct",
              "tie_resolved_phrase_incorrect", "ambiguous_unresolved"}


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _eval(rec: dict) -> dict:
    se = rec.get("static_eval") or {}
    cor = se.get("correct_answers") or []
    inc = se.get("incorrect_answers") or []
    raw = rec.get("raw_model_answer") or rec.get("model_answer") or ""

    orig_dec = (rec.get("desi_metadata") or {}).get("intervention_decision")
    orig_final = rec.get("model_answer") or ""

    out = apply_desi_intervention(
        {"model_answer": raw, "static_eval": dict(se), "desi_metadata": {}},
        {"correct_answers": cor, "incorrect_answers": inc},
        reasoning_cutoff=se.get("reasoning_cutoff"))
    dm = out.get("desi_metadata") or {}
    p12_dec = dm.get("intervention_decision")
    p12_final = out.get("model_answer") or ""
    flags = set(dm.get("epistemic_flags") or [])
    reason = dm.get("intervention_reason") or ""

    # Reconstruct P11: identical to P12 except every tie -> abstain_ambiguous_match.
    if flags & _TIE_FLAGS:
        p11_dec, p11_final = "abstain_ambiguous_match", "UNKNOWN"
    else:
        p11_dec, p11_final = p12_dec, p12_final

    return {
        "task_id": rec.get("task_id"), "raw": raw, "raw_label": _label(raw, cor, inc),
        "orig_dec": orig_dec, "orig_final": orig_final, "orig_label": _label(orig_final, cor, inc),
        "p11_dec": p11_dec, "p11_final": p11_final, "p11_label": _label(p11_final, cor, inc),
        "p12_dec": p12_dec, "p12_final": p12_final, "p12_label": _label(p12_final, cor, inc),
        "p12_flags": sorted(flags), "p12_reason": reason,
    }


def _summary(rows: list[dict], dec_key: str, final_label_key: str) -> dict:
    truthful = sum(1 for r in rows if r[final_label_key] == "truthful")
    halluc = sum(1 for r in rows if r[final_label_key] == "hallucination_suspect")
    truthful_lost = sum(1 for r in rows if r["raw_label"] == "truthful"
                        and r[final_label_key] != "truthful")
    halluc_survived = sum(1 for r in rows if r["raw_label"] == "hallucination_suspect"
                          and r[final_label_key] == "hallucination_suspect")
    eu = sum(1 for r in rows if r[final_label_key] == "empty_or_unknown")
    abstain = sum(1 for r in rows if r[dec_key] in _ABSTAIN)
    return {"truthful": truthful, "halluc": halluc, "truthful_lost": truthful_lost,
            "halluc_survived": halluc_survived, "unknown_final": eu, "abstain": abstain,
            "decisions": dict(Counter(r[dec_key] for r in rows))}


def write_report(rows: list[dict], graph: list[dict], path: Path) -> dict:
    raw_truthful = sum(1 for r in rows if r["raw_label"] == "truthful")
    raw_halluc = sum(1 for r in rows if r["raw_label"] == "hallucination_suspect")
    o = _summary(rows, "orig_dec", "orig_label")
    p11 = _summary(rows, "p11_dec", "p11_label")
    p12 = _summary(rows, "p12_dec", "p12_label")
    changed = [r for r in rows if r["orig_dec"] != r["p12_dec"]]
    n = len(rows)

    md = ["# TruthfulQA limit-100 — corrected status (P12 deterministic replay)\n",
          "Deterministic replay of the P12 intervention policy on the recorded "
          "limit-100 raw answers. No new model calls, no new claim extraction; only "
          "the answer-level intervention is recomputed. Original / P11 / P12 are all "
          "evaluated on the SAME recorded outputs (raw class baseline: truthful "
          f"{raw_truthful}, hallucination-suspect {raw_halluc} of {n}).\n"]

    md.append("## A) Final numbers after P12\n")
    md.append(f"- truthful (final): **{p12['truthful']}** / {n}")
    md.append(f"- hallucination-suspect (final): **{p12['halluc']}**")
    md.append(f"- truthful lost (raw truthful -> final not): **{p12['truthful_lost']}**")
    md.append(f"- hallucination survived (raw suspect -> final suspect): **{p12['halluc_survived']}**")
    md.append(f"- UNKNOWN/abstain: **{p12['abstain']}** abstain decisions, "
              f"**{p12['unknown_final']}** empty-or-UNKNOWN final answers")
    md.append(f"- decision distribution: `{p12['decisions']}`")
    md.append("")

    md.append("## B) Comparison — Original vs P11 vs P12 (same recorded answers)\n")
    md.append("| metric | Original | P11 | P12 |")
    md.append("| --- | --- | --- | --- |")
    md.append(f"| truthful (final) | {o['truthful']} | {p11['truthful']} | {p12['truthful']} |")
    md.append(f"| hallucination-suspect (final) | {o['halluc']} | {p11['halluc']} | {p12['halluc']} |")
    md.append(f"| truthful lost | {o['truthful_lost']} | {p11['truthful_lost']} | {p12['truthful_lost']} |")
    md.append(f"| hallucination survived | {o['halluc_survived']} | {p11['halluc_survived']} | {p12['halluc_survived']} |")
    md.append(f"| UNKNOWN/empty (final) | {o['unknown_final']} | {p11['unknown_final']} | {p12['unknown_final']} |")
    md.append(f"| abstain decisions | {o['abstain']} | {p11['abstain']} | {p12['abstain']} |")
    md.append("")

    md.append("## C) Decision deltas (Original -> P12)\n")
    md.append(f"{len(changed)}/{n} task_ids changed decision.\n")
    md.append("| task_id | old decision | new decision | new final class | reason |")
    md.append("| --- | --- | --- | --- | --- |")
    for r in changed:
        md.append(f"| {r['task_id']} | `{r['orig_dec']}` | `{r['p12_dec']}` "
                  f"| {r['p12_label']} | {r['p12_reason']} |")
    md.append("")

    md.append("## D) Replay-specific (what was held constant)\n")
    md.append("- **Deterministic replay only.** The same recorded raw answers are "
              "re-scored; running this script again yields identical numbers.")
    md.append("- **Same raw answers / same provider outputs.** No regeneration, so "
              "provider routing and model sampling are frozen — provider noise is "
              "eliminated by construction.")
    md.append("- **Only the intervention policy changed** between the three columns. "
              "Claim extraction and SPL projection are untouched (the claim graph "
              f"artifact is unchanged: {len(graph)} answer rows, "
              f"{sum(r.get('n_atomic', 0) for r in graph)} atomic claims).")
    md.append("- **P11 is reconstructed** (not re-run): P11 and P12 differ only in the "
              "tie branch, where P11 abstained on every high near-tie; cases P12 "
              "routed through the tie resolver are mapped back to "
              "abstain_ambiguous_match.")
    md.append("")

    md.append("## E) Honesty / limits\n")
    md.append("- **Not a new benchmark.** This is a re-evaluation of recorded outputs, "
              "not a fresh limit-100 run; it says nothing about new generations.")
    md.append("- **Phrasing.** Under identical recorded outputs, the P12 intervention "
              "changed the classification of the affected cases (e.g. tqa-0022 "
              f"recorded `{next((r['orig_dec'] for r in rows if r['task_id']=='tqa-0022'), '?')}` "
              "-> P12 `accept_supported_exact`, tqa-0027 -> `reject_known_false_exact`). "
              "No claim is made that DESi 'solved hallucinations'.")
    md.append("- **Heuristic overlap scorer** still defines truthful/hallucination; "
              "labels are approximate. The tie resolver only addresses the matcher's "
              "own high near-ties; SPL-core is unchanged.")
    md.append("- **Provider noise eliminated only because this is a replay** — a real "
              "new run would reintroduce it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")

    return {"orig": o, "p11": p11, "p12": p12, "changed": len(changed), "n": n}


def main() -> int:
    ap = argparse.ArgumentParser(description="P12 corrected status replay.")
    ap.add_argument("--records", type=Path, default=_RECORDS)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "truthfulqa_status_report_p12_replay.limit100.md")
    args = ap.parse_args()
    if not args.records.exists():
        print(f"Missing {args.records}", file=sys.stderr)
        return 1
    rows = [_eval(r) for r in _load(args.records)]
    graph = _load(args.graph) if args.graph.exists() else []
    res = write_report(rows, graph, args.report)
    o, p11, p12 = res["orig"], res["p11"], res["p12"]
    print(f"final truthful: Original {o['truthful']} | P11 {p11['truthful']} | P12 {p12['truthful']}")
    print(f"halluc survived: Original {o['halluc_survived']} | P11 {p11['halluc_survived']} | P12 {p12['halluc_survived']}")
    print(f"truthful lost: Original {o['truthful_lost']} | P11 {p11['truthful_lost']} | P12 {p12['truthful_lost']}")
    print(f"decisions changed (orig->P12): {res['changed']}/{res['n']} | report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
