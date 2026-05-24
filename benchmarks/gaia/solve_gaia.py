#!/usr/bin/env python3
"""Run a (stub) DESi solver over GAIA and write a submission JSONL.

Loads the gated ``gaia-benchmark/GAIA`` dataset, runs ``solve_task`` on each
task, and writes one submission line per task. The Hugging Face token is read
**only** from the ``HF_TOKEN`` / ``HUGGINGFACE_HUB_TOKEN`` environment variable;
no credential is stored in this file or the repository.

IMPORTANT: ``solve_task`` is currently a STUB. It does not solve GAIA tasks; it
exists to validate the end-to-end pipeline (load -> solve -> serialize ->
evaluate). Replace it with a real DESi-governed solver later.

Examples:
    export HF_TOKEN=hf_...
    python benchmarks/gaia/solve_gaia.py
    python benchmarks/gaia/solve_gaia.py --limit 20 --download-attachments
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

DATASET_ID = "gaia-benchmark/GAIA"
CONFIGS = ("2023_all", "2023_level1", "2023_level2", "2023_level3")
SOLVER_NAME = "stub"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent / "outputs" / "submission.validation.sample.jsonl"
)


# --------------------------------------------------------------------------- #
# STUB SOLVER -- replace with a real DESi-governed solver.
#
# This does NOT attempt to answer the task. A real implementation would route
# task["Question"] (plus any attachment referenced by task["file_path"]) through
# a DESi-governed solver and return the produced answer together with its
# reasoning / tool-use trace.
# --------------------------------------------------------------------------- #
def solve_task(task: dict) -> dict:
    """Return a placeholder answer and a trace marking this as a stub."""
    return {
        "model_answer": "",
        "reasoning_trace": (
            "STUB solver: no reasoning performed. Pipeline validation only — "
            "replace solve_task() with a real DESi-governed solver."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the (stub) DESi solver over GAIA and write a submission JSONL."
    )
    parser.add_argument("--config", default="2023_all", choices=CONFIGS,
                        help="Dataset config (default: 2023_all).")
    parser.add_argument("--split", default="validation",
                        help="Split to solve (default: validation).")
    parser.add_argument("--limit", type=int, default=5,
                        help="Number of tasks to solve (default: 5).")
    parser.add_argument("--download-attachments", action="store_true",
                        help="Cache each task's attachment locally before solving.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Output JSONL path (default: outputs/submission.validation.sample.jsonl).")
    return parser.parse_args()


def get_token() -> str | None:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if not token:
        print("WARNING: HF_TOKEN is not set; GAIA is gated and loading will likely "
              "fail. Accept the terms and export HF_TOKEN=hf_...", file=sys.stderr)
    return token


def main() -> int:
    args = parse_args()
    token = get_token()

    try:
        from datasets import load_dataset
    except ModuleNotFoundError:
        print("Missing dependency. Install with: "
              "pip install datasets huggingface_hub", file=sys.stderr)
        return 1

    try:
        ds = load_dataset(DATASET_ID, args.config, split=args.split, token=token)
    except Exception as exc:
        print(f"Failed to load {DATASET_ID} [{args.config}/{args.split}]: {exc}",
              file=sys.stderr)
        return 1

    if args.download_attachments:
        from huggingface_hub import hf_hub_download

    count = min(args.limit, len(ds))
    records: list[str] = []

    for i in range(count):
        row = ds[i]
        file_name = (row.get("file_name") or "").strip()
        file_path = (row.get("file_path") or "").strip()

        if args.download_attachments and file_path:
            try:
                hf_hub_download(repo_id=DATASET_ID, filename=file_path,
                                repo_type="dataset", token=token)
            except Exception as exc:
                print(f"  warn: attachment download failed for "
                      f"{row.get('task_id')}: {exc}", file=sys.stderr)

        result = solve_task(dict(row))
        record = {
            "task_id": row.get("task_id", ""),
            "model_answer": result.get("model_answer", ""),
            "reasoning_trace": result.get("reasoning_trace", ""),
            "desi_metadata": {
                "solver": SOLVER_NAME,
                "config": args.config,
                "split": args.split,
                "level": row.get("Level", ""),
                "has_attachment": bool(file_name),
                "file_name": file_name,
                "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            },
        }
        records.append(json.dumps(record, ensure_ascii=False))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(records) + "\n", encoding="utf-8")

    print(f"Solver: {SOLVER_NAME} (STUB) | {DATASET_ID} [{args.config}/{args.split}]")
    print(f"Wrote {len(records)} submission line(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
