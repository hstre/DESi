#!/usr/bin/env python3
"""Aggregate the human manual-review annotations for corrected-FEVER errors.

Reads fever_manual_review_annotations.jsonl. If no annotations are filled yet, it
prints a warning and STOPS (it does not compute anything). Once a human has filled
HUMAN_JUDGMENT values, it aggregates the judgment distribution and separates:
confirmed artifacts / probable benchmark issues / probable true model failures.

It does NOT compute adjusted accuracy (deferred by instruction) and never
relabels or reruns.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ANNOT = _HERE / "fever_manual_review_annotations.jsonl"
_REPORTS = _HERE / "reports"

# how each human judgment rolls up
_ARTIFACT = {"DATA_ARTIFACT"}
_BENCHMARK = {"GOLD_QUESTIONABLE", "BENCHMARK_CONVENTION", "UNDERDETERMINED"}
_TRUE_MISS = {"MODEL_CLEARLY_WRONG"}
_OTHER = {"AMBIGUOUS"}


def aggregate():
    if not _ANNOT.exists():
        print("WARNING: no annotation file found "
              f"({_ANNOT.name}). Run fever_manual_review.py first, then annotate. Stopping.")
        return 1
    rows = [json.loads(l) for l in _ANNOT.read_text().splitlines() if l.strip()]
    filled = [r for r in rows if str(r.get("HUMAN_JUDGMENT", "")).strip()]
    if not filled:
        print(f"WARNING: {len(rows)} items present but 0 annotated. Fill HUMAN_JUDGMENT in "
              f"{_ANNOT.name} first. Refusing to aggregate empty annotations. Stopping.")
        return 1

    by_judg = Counter(r["HUMAN_JUDGMENT"].strip().upper() for r in filled)
    artifacts = sum(v for k, v in by_judg.items() if k in _ARTIFACT)
    benchmark = sum(v for k, v in by_judg.items() if k in _BENCHMARK)
    true_miss = sum(v for k, v in by_judg.items() if k in _TRUE_MISS)
    other = sum(v for k, v in by_judg.items() if k in _OTHER)
    md = [
        "# Corrected-FEVER manual-review aggregate (post-annotation)\n",
        f"Annotated items: {len(filled)} of {len(rows)}.\n",
        "## Human judgment distribution\n", "| judgment | count |", "| --- | --- |",
        *[f"| {k} | {v} |" for k, v in sorted(by_judg.items())], "",
        "## Separation\n",
        f"- **Confirmed data artifacts**: {artifacts}",
        f"- **Probable benchmark / underdetermined-label issues**: {benchmark}",
        f"- **Probable true model failures**: {true_miss}",
        f"- **Ambiguous / unresolved**: {other}",
        "",
        "Adjusted accuracy is intentionally NOT computed here (deferred). No relabeling.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "fever_manual_review_aggregate.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"aggregate -> fever_manual_review_aggregate.md "
          f"(artifacts={artifacts}, benchmark={benchmark}, true_miss={true_miss}, other={other})")
    return 0


if __name__ == "__main__":
    raise SystemExit(aggregate())
