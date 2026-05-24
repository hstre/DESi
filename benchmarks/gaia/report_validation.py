#!/usr/bin/env python3
"""Summarise a GAIA validation run: attachment split, accuracy, and UNKNOWNs.

Reads the submission JSONL and the gold validation split and reports overall /
text-only accuracy, per-level accuracy, and how many answers were empty/UNKNOWN.
The HF token is read **only** from the environment.

Example:
    export HF_TOKEN=...
    python benchmarks/gaia/report_validation.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_validation import normalize  # reuse the same lenient comparison

DATASET_ID = "gaia-benchmark/GAIA"
DEFAULT_SUBMISSION = (
    Path(__file__).resolve().parent / "outputs" / "submission.validation.sample.jsonl"
)


def _is_unknown_or_empty(answer: str) -> bool:
    a = str(answer).strip()
    return a == "" or a.upper() == "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser(description="Report stats for a GAIA run.")
    parser.add_argument("--submission", type=Path, default=DEFAULT_SUBMISSION)
    parser.add_argument("--config", default="2023_all")
    parser.add_argument("--split", default="validation")
    args = parser.parse_args()

    if not args.submission.exists():
        print(f"Submission not found: {args.submission}", file=sys.stderr)
        return 1

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    try:
        from datasets import load_dataset
    except ModuleNotFoundError:
        print("Missing dependency. Install with: pip install datasets", file=sys.stderr)
        return 1
    try:
        ds = load_dataset(DATASET_ID, args.config, split=args.split, token=token)
    except Exception as exc:
        print(f"Failed to load {DATASET_ID} [{args.config}/{args.split}]: {exc}",
              file=sys.stderr)
        return 1

    gold = {
        row["task_id"]: {
            "answer": row.get("Final answer", ""),
            "level": row.get("Level", ""),
            "has_attachment": bool((row.get("file_name") or "").strip()),
        }
        for row in ds
    }

    total = correct = 0
    with_attach = without_attach = 0
    correct_no_attach = 0
    unknown_or_empty = 0
    missing = 0
    per_level = defaultdict(lambda: [0, 0])  # level -> [correct, total]

    with args.submission.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            task_id = entry.get("task_id", "")
            if task_id not in gold:
                missing += 1
                continue
            g = gold[task_id]
            answer = entry.get("model_answer", "")
            is_correct = (not _is_unknown_or_empty(answer)
                          and normalize(answer) == normalize(g["answer"]))

            total += 1
            correct += int(is_correct)
            per_level[g["level"]][1] += 1
            per_level[g["level"]][0] += int(is_correct)
            if _is_unknown_or_empty(answer):
                unknown_or_empty += 1
            if g["has_attachment"]:
                with_attach += 1
            else:
                without_attach += 1
                correct_no_attach += int(is_correct)

    def pct(c: int, t: int) -> str:
        return f"{100.0 * c / t:.1f}%" if t else "n/a"

    print(f"Submission: {args.submission}")
    print(f"Gold:       {DATASET_ID} [{args.config}/{args.split}]\n")
    print(f"Total tasks scored      : {total}")
    print(f"  with attachment       : {with_attach}")
    print(f"  without attachment    : {without_attach}")
    print(f"UNKNOWN / empty answers : {unknown_or_empty}\n")
    print(f"Accuracy (overall)         : {correct}/{total} = {pct(correct, total)}")
    print(f"Accuracy (text-only tasks) : {correct_no_attach}/{without_attach} = "
          f"{pct(correct_no_attach, without_attach)}")
    print("Accuracy per level:")
    for level in sorted(per_level, key=lambda x: str(x)):
        c, t = per_level[level]
        print(f"  Level {level}: {c}/{t} = {pct(c, t)}")
    if missing:
        print(f"\n{missing} submission task_id(s) not found in the split (skipped).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
