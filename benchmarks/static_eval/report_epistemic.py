#!/usr/bin/env python3
"""Report dataset-independent epistemic flags for a TruthfulQA run.

Reads a run JSONL (desi_intervened with --general-checks on), tallies flag
frequencies, their relationship to the raw hallucination-suspect / truthful
labels (heuristic overlap, the same independent scorer), shows examples per
flag, and writes a Markdown report. Self-contained; no network.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_truthfulqa import _label  # independent overlap scorer

FLAGS = ("unsupported_certainty", "reasoning_inefficiency",
         "contradiction", "evasive_answer")
DEFAULT = Path(__file__).resolve().parent / "outputs" / \
    "truthfulqa.deepseek-v4.desi_intervened.refined.general.limit50.jsonl"


def main() -> int:
    p = argparse.ArgumentParser(description="Report general epistemic flags.")
    p.add_argument("--submission", type=Path, default=DEFAULT)
    p.add_argument("--report", type=Path, default=None)
    args = p.parse_args()
    if not args.submission.exists():
        print(f"Submission not found: {args.submission}", file=sys.stderr)
        return 1

    total = with_any = 0
    flag_counts = Counter()
    flag_label = defaultdict(Counter)     # flag -> Counter(label)
    label_total = Counter()               # raw label totals
    halluc_with_flag = truthful_with_flag = 0
    decisions = Counter()
    risk_bucket = Counter()
    examples = defaultdict(list)

    for line in args.submission.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        m = e.get("desi_metadata") or {}
        se = e.get("static_eval", {})
        raw = e.get("raw_model_answer", e.get("model_answer", ""))
        lab = _label(raw, se.get("correct_answers", []), se.get("incorrect_answers", []))
        flags = m.get("epistemic_flags", []) or []
        risk = m.get("epistemic_risk_score")
        decisions[m.get("intervention_decision", "?")] += 1

        total += 1
        label_total[lab] += 1
        if flags:
            with_any += 1
            if lab == "hallucination_suspect":
                halluc_with_flag += 1
            if lab == "truthful":
                truthful_with_flag += 1
        if risk is not None:
            b = "0.0" if risk == 0 else "0.0-0.3" if risk < 0.3 else \
                "0.3-0.6" if risk < 0.6 else "0.6+"
            risk_bucket[b] += 1
        for f in flags:
            flag_counts[f] += 1
            flag_label[f][lab] += 1
            if len(examples[f]) < 3:
                examples[f].append((e.get("task_id", ""), raw[:60]))

    md = [f"# General epistemic checks — {args.submission.name}\n",
          f"- Total answers: **{total}**",
          f"- Answers with >=1 epistemic flag: **{with_any}** "
          f"({100.0*with_any/total:.0f}%)\n" if total else ""]

    md.append("## Flag frequency\n")
    md.append("| flag | count | of flagged: halluc | truthful | other/empty |")
    md.append("| --- | --- | --- | --- | --- |")
    for f in FLAGS:
        c = flag_counts[f]
        bl = flag_label[f]
        md.append(f"| {f} | {c} | {bl['hallucination_suspect']} | "
                  f"{bl['truthful']} | {bl['other'] + bl['empty_or_unknown']} |")
    md.append("")

    md.append("## Relationship to hallucination-suspect / truthful (raw answers)\n")
    md.append(f"- raw hallucination-suspect total: **{label_total['hallucination_suspect']}**, "
              f"of which flagged: **{halluc_with_flag}**")
    md.append(f"- raw truthful total: **{label_total['truthful']}**, "
              f"of which flagged: **{truthful_with_flag}**")
    md.append(f"- epistemic_risk_score buckets: `{dict(risk_bucket)}`")
    md.append(f"- intervention decisions: `{dict(decisions)}`\n")

    md.append("## Examples per flag\n")
    for f in FLAGS:
        if not examples[f]:
            md.append(f"- **{f}**: (none)")
            continue
        md.append(f"- **{f}**:")
        for tid, ex in examples[f]:
            md.append(f"    - `{tid}` {ex!r}")
    md.append("")
    md.append("> Heuristic, surface-level signals — epistemic *risk* flags, not "
              "a truth oracle. They flag/downgrade only; they never set UNKNOWN.")

    out = "\n".join(x for x in md if x is not None) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(out, encoding="utf-8")
        print(f"Wrote epistemic report to {args.report}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
