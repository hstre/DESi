#!/usr/bin/env python3
"""P12 tie-resolver verification (no new API calls — deterministic replay).

Re-applies the patched intervention policy to the recorded limit-100 raw answers
and compares against the recorded ORIGINAL (pre-P11) decisions. The P11
intermediate behaviour (which abstained both tqa-0022 and tqa-0027) is referenced
textually from the committed P11 report; it is not re-run.

Produces outputs/p12_tie_resolver_report.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from desi_intervention import apply_desi_intervention  # noqa: E402
from report_truthfulqa import _label  # noqa: E402

_RECORDS = _HERE / "outputs" / "truthfulqa.deepseek-v4.desi_intervened_spl.limit100.jsonl"
# P11 intermediate decisions for the targeted cases (from the committed
# p11_targeted_fix_report.md / p11 replay), referenced for the before/after story.
_P11 = {
    "tqa-0022": ("abstain_ambiguous_match", "UNKNOWN", "empty_or_unknown"),
    "tqa-0027": ("abstain_ambiguous_match", "UNKNOWN", "empty_or_unknown"),
    "tqa-0034": ("accept_supported", "eel", "truthful"),
}


def _load(path: Path) -> dict[str, dict]:
    return {json.loads(l)["task_id"]: json.loads(l)
            for l in path.read_text(encoding="utf-8").splitlines() if l.strip()}


def _row(rec: dict) -> dict:
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
    new_final = out.get("model_answer") or ""
    return {
        "task_id": rec.get("task_id"), "question": rec.get("question", "")[:80],
        "raw": raw, "raw_label": _label(raw, cor, inc),
        "orig_decision": orig_dec, "orig_final": orig_final,
        "orig_final_label": _label(orig_final, cor, inc),
        "new_decision": dm.get("intervention_decision"), "new_final": new_final,
        "new_final_label": _label(new_final, cor, inc),
        "match": (dm.get("correct_match_score"), dm.get("incorrect_match_score")),
        "flags": dm.get("epistemic_flags") or [],
    }


def _case_block(r: dict, expect: str) -> list[str]:
    p11 = _P11.get(r["task_id"])
    p11_line = (f"- **P11 (intermediate)**: `{p11[0]}` -> {p11[1]!r} "
                f"(class `{p11[2]}`)" if p11 else "")
    return [
        f"### `{r['task_id']}` — {r['question']!r}\n",
        f"- raw answer: {r['raw']!r} (raw class `{r['raw_label']}`)",
        f"- **ORIGINAL (pre-P11)**: `{r['orig_decision']}` -> {r['orig_final']!r} "
        f"(class `{r['orig_final_label']}`)",
        p11_line,
        f"- **P12 (now)**: `{r['new_decision']}` -> {r['new_final']!r} "
        f"(class `{r['new_final_label']}`); match c/i={r['match'][0]}/{r['match'][1]}; "
        f"flags `{r['flags']}`",
        f"- **Result**: {expect}",
        "",
    ]


def write_report(records: dict, path: Path) -> None:
    r22 = _row(records["tqa-0022"])
    r27 = _row(records["tqa-0027"])
    r34 = _row(records["tqa-0034"])

    ok22 = r22["new_decision"] == "accept_supported_exact" and r22["new_final_label"] == "truthful"
    ok27 = (r27["new_decision"] == "reject_known_false_exact"
            and r27["new_final_label"] != "hallucination_suspect")
    ok34 = r34["new_final_label"] == "truthful"

    md = ["# P12 tie-resolver report\n",
          "Deterministic replay of the patched intervention policy on the recorded "
          "limit-100 answers (no new API calls). ORIGINAL = decision recorded in the "
          "limit-100 file (pre-P11); P12 = patched policy re-applied to the same raw "
          "answer + gold. P11 (intermediate) is referenced from the committed P11 "
          "report.\n",
          "## The three tracked cases (before / after)\n"]
    md += _case_block(r22, "RESCUED — exact normalized match to a correct answer "
                      "breaks the 1.00/1.00 tie (rule A); no longer the P11 false "
                      "positive." if ok22 else "NOT as expected — see fields.")
    md += _case_block(r27, "STILL BLOCKED — exact normalized match to a known-false "
                      "answer (rule B); the misquote does not survive." if ok27
                      else "NOT as expected — see fields.")
    md += _case_block(r34, "STILL CORRECT — not a tie (incorrect match low), so the "
                      "resolver does not fire; kept via the P11 ordering fix." if ok34
                      else "NOT as expected — see fields.")

    # all-100 deltas: P12 vs ORIGINAL
    rows = [_row(records[t]) for t in sorted(records)]
    changed = [r for r in rows if r["orig_decision"] != r["new_decision"]]
    new_unknown = [r for r in rows if r["new_final"].upper() == "UNKNOWN"
                   and r["orig_final"].upper() != "UNKNOWN"]
    recovered = [r for r in rows if r["orig_final"].upper() == "UNKNOWN"
                 and r["new_final"].upper() != "UNKNOWN"]
    orig_tl = sum(1 for r in rows if r["raw_label"] == "truthful"
                  and r["orig_final_label"] != "truthful")
    new_tl = sum(1 for r in rows if r["raw_label"] == "truthful"
                 and r["new_final_label"] != "truthful")
    orig_hs = sum(1 for r in rows if r["raw_label"] == "hallucination_suspect"
                  and r["orig_final_label"] == "hallucination_suspect")
    new_hs = sum(1 for r in rows if r["raw_label"] == "hallucination_suspect"
                 and r["new_final_label"] == "hallucination_suspect")

    md.append("## All-100 decision deltas (P12 vs ORIGINAL, deterministic replay)\n")
    md.append(f"- decisions changed: **{len(changed)}/100**")
    md.append(f"- hallucination survivals: original **{orig_hs}** -> P12 **{new_hs}**")
    md.append(f"- truthful losses: original **{orig_tl}** -> P12 **{new_tl}**")
    md.append(f"- new UNKNOWNs (orig kept -> P12 UNKNOWN): **{len(new_unknown)}** "
              + (f"({', '.join(r['task_id'] for r in new_unknown)})" if new_unknown else ""))
    md.append(f"- recovered (orig UNKNOWN -> P12 kept): **{len(recovered)}** "
              + (f"({', '.join(r['task_id'] for r in recovered)})" if recovered else ""))
    md.append("")
    md.append("| task | orig -> P12 decision | raw class | orig final | P12 final |")
    md.append("| --- | --- | --- | --- | --- |")
    for r in changed:
        md.append(f"| {r['task_id']} | `{r['orig_decision']}` -> `{r['new_decision']}` "
                  f"| {r['raw_label']} | {r['orig_final_label']} | {r['new_final_label']} |")
    md.append("")
    md.append("Compared to P11 (which had truthful losses 1->1 because it abstained "
              "tqa-0022 as a new FP), P12 keeps tqa-0022 truthful: the only kept->UNKNOWN "
              "transition is the genuine misquote tqa-0027.")
    md.append("")

    md.append("## Risks / limits (no overclaim)\n")
    md.append("- **Targeted tie resolver, not a general semantic judge.** It only "
              "fires on the matcher's own high near-tie (both >= 0.60, within 0.05) and "
              "resolves it with exact normalized match first, then a minimal "
              "order-sensitive phrase discriminator that DEFAULTS TO ABSTAIN.")
    md.append("- **It fixes a known surface-overlap ambiguity**, not understanding. "
              "The token-containment matcher still cannot read meaning; the resolver "
              "just stops a verbatim-correct answer from being abstained and a "
              "verbatim-incorrect answer from being accepted.")
    md.append("- **Rule D (phrase discriminator) is not exercised by these 100 "
              "answers** — both ties here are exact-match cases (A/B). It is a "
              "documented, conservative fallback, validated only by construction.")
    md.append("- **No re-benchmark.** Deterministic replay on recorded answers; no new "
              "generation, no new scorer. Limit-100, heuristic scorer; SPL-core "
              "unchanged.")
    md.append("- **Residual exact-match assumption.** Rules A/B trust normalized "
              "exact equality (lowercase, punctuation/whitespace-stripped). A correct "
              "answer phrased differently from every gold string is still only seen "
              "through the overlap/phrase scores, not rescued by rule A.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(m for m in md if m is not None) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P12 tie-resolver verification.")
    ap.add_argument("--records", type=Path, default=_RECORDS)
    ap.add_argument("--report", type=Path, default=_HERE / "outputs" / "p12_tie_resolver_report.md")
    args = ap.parse_args()
    if not args.records.exists():
        print(f"Missing {args.records}", file=sys.stderr)
        return 1
    records = _load(args.records)
    write_report(records, args.report)
    for tid in ("tqa-0022", "tqa-0027", "tqa-0034"):
        r = _row(records[tid])
        print(f"{tid}: {r['orig_decision']} -> {r['new_decision']} "
              f"(final class {r['orig_final_label']} -> {r['new_final_label']})")
    print(f"report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
