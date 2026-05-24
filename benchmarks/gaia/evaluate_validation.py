#!/usr/bin/env python3
"""Evaluate a GAIA submission JSONL against the validation Final answers.

Computes a simple exact-match accuracy, overall and per level. The Hugging Face
token is read **only** from ``HF_TOKEN`` / ``HUGGINGFACE_HUB_TOKEN``.

This is a SIMPLIFIED scorer (case- and whitespace-insensitive exact match). It
is *not* the official GAIA scorer (which applies number/string normalization);
use it for quick local iteration only.

Examples:
    export HF_TOKEN=hf_...
    python benchmarks/gaia/evaluate_validation.py
    python benchmarks/gaia/evaluate_validation.py --submission path/to/sub.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

DATASET_ID = "gaia-benchmark/GAIA"
DEFAULT_SUBMISSION = (
    Path(__file__).resolve().parent / "outputs" / "submission.validation.sample.jsonl"
)


def normalize(answer: object) -> str:
    """Lowercase + collapse whitespace for a lenient exact-match comparison."""
    return " ".join(str(answer).strip().casefold().split())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simple exact-match evaluation for a GAIA submission JSONL."
    )
    parser.add_argument("--submission", type=Path, default=DEFAULT_SUBMISSION,
                        help="Submission JSONL to score.")
    parser.add_argument("--config", default="2023_all",
                        help="Dataset config to read gold answers from.")
    parser.add_argument("--split", default="validation",
                        help="Split to read gold answers from (default: validation).")
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
        row["task_id"]: {"answer": row.get("Final answer", ""),
                         "level": row.get("Level", "")}
        for row in ds
    }

    total = correct = missing = 0
    per_level: dict[object, list[int]] = defaultdict(lambda: [0, 0])  # level -> [correct, total]

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
            level = gold[task_id]["level"]
            is_correct = normalize(entry.get("model_answer", "")) == normalize(gold[task_id]["answer"])
            total += 1
            correct += int(is_correct)
            per_level[level][1] += 1
            per_level[level][0] += int(is_correct)

    def pct(c: int, t: int) -> str:
        return f"{100.0 * c / t:.1f}%" if t else "n/a"

    print(f"Submission: {args.submission}")
    print(f"Gold:       {DATASET_ID} [{args.config}/{args.split}]\n")
    print(f"Overall exact-match: {correct}/{total} = {pct(correct, total)}")
    for level in sorted(per_level, key=lambda x: str(x)):
        c, t = per_level[level]
        print(f"  Level {level}: {c}/{t} = {pct(c, t)}")
    if missing:
        print(f"\n{missing} submission task_id(s) not found in the split (skipped).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
