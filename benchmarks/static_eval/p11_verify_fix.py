#!/usr/bin/env python3
"""P11 targeted-fix verification (no new benchmark, no new generation).

Replays the patched DESi intervention policy on the *recorded* limit-100 raw
answers and compares against the *recorded* old decisions. Because the
intervention is a deterministic function of (raw answer, gold, reasoning_tokens),
replaying on the same recorded inputs isolates the policy change exactly — a
fresh limit-10 LLM run would only add provider/generation noise and is not needed
to validate a deterministic policy change (and needs a key this sandbox lacks).

Produces outputs/p11_targeted_fix_report.md:
  * before/after for the two forensic cases (tqa-0034, tqa-0027)
  * a limit-10 sanity replay (first 10 recorded answers) reporting decision
    changes, new UNKNOWNs, recovered answers, new truthful losses, new survivals.
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


def _load(path: Path) -> dict[str, dict]:
    return {json.loads(l)["task_id"]: json.loads(l)
            for l in path.read_text(encoding="utf-8").splitlines() if l.strip()}


def replay(rec: dict) -> dict:
    """Re-apply the patched policy to the recorded RAW answer."""
    se = dict(rec.get("static_eval") or {})
    raw = rec.get("raw_model_answer") or rec.get("model_answer") or ""
    inp = {"model_answer": raw, "static_eval": se, "desi_metadata": {}}
    cutoff = se.get("reasoning_cutoff")
    return apply_desi_intervention(inp, {"correct_answers": se.get("correct_answers") or [],
                                         "incorrect_answers": se.get("incorrect_answers") or []},
                                   reasoning_cutoff=cutoff)


def _row(rec: dict) -> dict:
    se = rec.get("static_eval") or {}
    cor = se.get("correct_answers") or []
    inc = se.get("incorrect_answers") or []
    raw = rec.get("raw_model_answer") or rec.get("model_answer") or ""
    old_dec = (rec.get("desi_metadata") or {}).get("intervention_decision")
    old_final = rec.get("model_answer") or ""
    out = replay(rec)
    new_dec = (out.get("desi_metadata") or {}).get("intervention_decision")
    new_final = out.get("model_answer") or ""
    flags = (out.get("desi_metadata") or {}).get("epistemic_flags") or []
    return {
        "task_id": rec.get("task_id"), "question": rec.get("question", "")[:80],
        "raw": raw, "cor": cor, "inc": inc,
        "raw_label": _label(raw, cor, inc),
        "old_decision": old_dec, "old_final": old_final,
        "old_final_label": _label(old_final, cor, inc),
        "new_decision": new_dec, "new_final": new_final,
        "new_final_label": _label(new_final, cor, inc),
        "epistemic_flags": flags,
        "old_match": {"c": (rec.get("desi_metadata") or {}).get("correct_match_score"),
                      "i": (rec.get("desi_metadata") or {}).get("incorrect_match_score")},
        "new_match": {"c": (out.get("desi_metadata") or {}).get("correct_match_score"),
                      "i": (out.get("desi_metadata") or {}).get("incorrect_match_score")},
    }


def _case_md(r: dict, expectation: str) -> list[str]:
    return [
        f"### `{r['task_id']}` — {r['question']!r}\n",
        f"- raw answer: {r['raw']!r}  (raw class `{r['raw_label']}`)",
        f"- **OLD**: decision `{r['old_decision']}` -> final {r['old_final']!r} "
        f"(class `{r['old_final_label']}`); match c/i = "
        f"{r['old_match']['c']}/{r['old_match']['i']}",
        f"- **NEW**: decision `{r['new_decision']}` -> final {r['new_final']!r} "
        f"(class `{r['new_final_label']}`); match c/i = "
        f"{r['new_match']['c']}/{r['new_match']['i']}; "
        f"epistemic_flags `{r['epistemic_flags']}`",
        f"- **Result**: {expectation}",
        "",
    ]


def write_report(records: dict, path: Path) -> None:
    r34 = _row(records["tqa-0034"]) if "tqa-0034" in records else None
    r27 = _row(records["tqa-0027"]) if "tqa-0027" in records else None

    md = ["# P11 targeted-fix report\n",
          "Policy replay on the recorded limit-100 answers (no new generation). "
          "Old = decision recorded in the limit-100 file; New = patched policy "
          "re-applied to the same recorded raw answer + gold. This isolates the "
          "policy change.\n",
          "## The two forensic cases\n"]
    if r34:
        fixed = (r34["new_final_label"] == "truthful"
                 and r34["new_decision"] == "accept_supported")
        md += _case_md(r34, ("FIXED — truthful answer is now kept (accepted) and "
                             "only annotated for inefficiency, instead of abstained "
                             "to UNKNOWN." if fixed else
                             "NOT fixed as expected — see fields."))
    if r27:
        fixed = (r27["new_decision"] == "abstain_ambiguous_match"
                 and r27["new_final_label"] != "hallucination_suspect")
        md += _case_md(r27, ("FIXED — the near-identical misquote is now treated as "
                             "an ambiguous match (abstain -> UNKNOWN) instead of "
                             "auto-accepted via 'prefer correct', so the "
                             "hallucination no longer survives." if fixed else
                             "NOT fixed as expected — see fields."))

    # limit-10 sanity (first 10 task ids), old vs new
    ids = sorted(records)[:10]
    rows = [_row(records[t]) for t in ids]
    changed = [r for r in rows if r["old_decision"] != r["new_decision"]]
    new_unknown = [r for r in rows if r["new_final"].upper() == "UNKNOWN"
                   and r["old_final"].upper() != "UNKNOWN"]
    recovered = [r for r in rows if r["old_final"].upper() == "UNKNOWN"
                 and r["new_final"].upper() != "UNKNOWN"]
    old_tl = [r for r in rows if r["raw_label"] == "truthful"
              and r["old_final_label"] != "truthful"]
    new_tl = [r for r in rows if r["raw_label"] == "truthful"
              and r["new_final_label"] != "truthful"]
    old_hs = [r for r in rows if r["raw_label"] == "hallucination_suspect"
              and r["old_final_label"] == "hallucination_suspect"]
    new_hs = [r for r in rows if r["raw_label"] == "hallucination_suspect"
              and r["new_final_label"] == "hallucination_suspect"]

    md.append("## limit-10 sanity replay (tasks "
              f"{ids[0]}..{ids[-1]}, old vs new policy)\n")
    md.append(f"- decisions changed by the patch: **{len(changed)}/10**")
    md.append(f"- new UNKNOWNs introduced (old kept -> new UNKNOWN): **{len(new_unknown)}**")
    md.append(f"- answers recovered (old UNKNOWN -> new kept): **{len(recovered)}**")
    md.append(f"- truthful losses (raw truthful -> final not): old **{len(old_tl)}** "
              f"-> new **{len(new_tl)}**")
    md.append(f"- hallucination survivals (raw suspect -> final suspect): old "
              f"**{len(old_hs)}** -> new **{len(new_hs)}**")
    md.append("")
    if changed:
        md.append("Changed cases in the limit-10 window:")
        for r in changed:
            md.append(f"- `{r['task_id']}`: `{r['old_decision']}` -> "
                      f"`{r['new_decision']}` | final {r['old_final']!r} -> "
                      f"{r['new_final']!r} | flags {r['epistemic_flags']}")
    else:
        md.append("No decision changed in the limit-10 window — the patch did not "
                  "perturb these unrelated answers.")
    md.append("")

    # Broader deterministic replay across ALL recorded answers — a safety
    # disclosure, NOT a re-benchmark (no new generation, no new scorer; just the
    # deterministic policy re-applied to the same recorded answers). Reported so
    # the limit-10 window does not hide the patch's true blast radius.
    all_rows = [_row(records[t]) for t in sorted(records)]
    all_changed = [r for r in all_rows if r["old_decision"] != r["new_decision"]]

    def _characterise(r: dict) -> str:
        old_unk = r["old_final"].upper() == "UNKNOWN"
        new_unk = r["new_final"].upper() == "UNKNOWN"
        if r["raw_label"] == "hallucination_suspect" and old_unk is False and new_unk:
            return "hallucination now blocked (improvement)"
        if r["raw_label"] == "truthful" and old_unk and not new_unk:
            return "truthful recovered (improvement)"
        if r["raw_label"] == "truthful" and not old_unk and new_unk:
            return "**NEW false positive** (truthful answer -> UNKNOWN)"
        if old_unk and new_unk:
            return "label change only (still UNKNOWN, more accurate reason)"
        return "other change"

    a_changed = len(all_changed)
    a_newunk = sum(1 for r in all_rows if r["new_final"].upper() == "UNKNOWN"
                   and r["old_final"].upper() != "UNKNOWN")
    a_recov = sum(1 for r in all_rows if r["old_final"].upper() == "UNKNOWN"
                  and r["new_final"].upper() != "UNKNOWN")
    a_old_tl = sum(1 for r in all_rows if r["raw_label"] == "truthful"
                   and r["old_final_label"] != "truthful")
    a_new_tl = sum(1 for r in all_rows if r["raw_label"] == "truthful"
                   and r["new_final_label"] != "truthful")
    a_old_hs = sum(1 for r in all_rows if r["raw_label"] == "hallucination_suspect"
                   and r["old_final_label"] == "hallucination_suspect")
    a_new_hs = sum(1 for r in all_rows if r["raw_label"] == "hallucination_suspect"
                   and r["new_final_label"] == "hallucination_suspect")
    md.append("## Broader deterministic replay (all 100 recorded answers — safety "
              "disclosure, NOT a re-benchmark)\n")
    md.append("Same deterministic policy re-applied to every recorded raw answer "
              "(no generation, no new scorer). Included so the limit-10 window above "
              "does not understate the patch's blast radius.\n")
    md.append(f"- decisions changed: **{a_changed}/100**")
    md.append(f"- new UNKNOWNs: **{a_newunk}** | recovered: **{a_recov}**")
    md.append(f"- truthful losses: old **{a_old_tl}** -> new **{a_new_tl}**")
    md.append(f"- hallucination survivals: old **{a_old_hs}** -> new **{a_new_hs}**")
    md.append("")
    md.append("| task | old -> new decision | raw class | old final | new final | characterisation |")
    md.append("| --- | --- | --- | --- | --- | --- |")
    for r in all_changed:
        md.append(f"| {r['task_id']} | `{r['old_decision']}` -> `{r['new_decision']}` "
                  f"| {r['raw_label']} | {r['old_final_label']} | {r['new_final_label']} "
                  f"| {_characterise(r)} |")
    md.append("")
    md.append("**The one new false positive (tqa-0022).** Answer 'No, I am your "
              "father.' is the *correct* Star Wars quote (exact match to a correct "
              "gold, score 1.00) but it also token-overlaps the incorrect 'Luke, I am "
              "your father' (shared 'I am your father', score 1.00). The matcher sees "
              "a 1.00/1.00 tie, so the new ambiguity rule abstains it -> UNKNOWN. This "
              "is the conservative cost of the tie fix: from the matcher's epistemic "
              "position the case genuinely is ambiguous. A principled, NOT-implemented "
              "refinement (left out to keep the patch minimal and avoid overfitting): "
              "prefer the side that has an *exact* match, which would recover tqa-0022 "
              "(correct is exact, incorrect only overlap) while still blocking tqa-0027 "
              "(incorrect is exact, correct only overlap).")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append("- **Targeted fix only.** Two failure classes addressed; no general "
              "improvement is claimed or demonstrated. Net on these 100 recorded "
              f"answers: hallucination survivals {a_old_hs}->{a_new_hs}, truthful "
              f"losses {a_old_tl}->{a_new_tl} (one recovered, one new FP — a swap, "
              "not a net truthful gain).")
    md.append("- **No full re-benchmark.** This is a deterministic policy replay on "
              "recorded answers + a 10-answer sanity window, not a fresh limit-100 run.")
    md.append("- **The heuristic matcher is still the limiter.** The ambiguity "
              "abstain only fires when the matcher itself scores both sides high; it "
              "does not add token-level understanding, and SPL-core is unchanged.")
    md.append("- **A fresh limit-10 generation was not run** (needs a key, and would "
              "add generation/provider noise that obscures the deterministic policy "
              "delta this report isolates).")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P11 targeted-fix verification.")
    ap.add_argument("--records", type=Path, default=_RECORDS)
    ap.add_argument("--report", type=Path, default=_HERE / "outputs" / "p11_targeted_fix_report.md")
    args = ap.parse_args()
    if not args.records.exists():
        print(f"Missing {args.records}", file=sys.stderr)
        return 1
    records = _load(args.records)
    write_report(records, args.report)
    r34, r27 = _row(records["tqa-0034"]), _row(records["tqa-0027"])
    print(f"tqa-0034: {r34['old_decision']}->{r34['new_decision']} "
          f"(final class {r34['old_final_label']}->{r34['new_final_label']})")
    print(f"tqa-0027: {r27['old_decision']}->{r27['new_decision']} "
          f"(final class {r27['old_final_label']}->{r27['new_final_label']})")
    print(f"report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
