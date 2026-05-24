#!/usr/bin/env python3
"""Load the GAIA benchmark and preview tasks.

GAIA (``gaia-benchmark/GAIA``) is a *gated* dataset. Authentication is read
**only** from the ``HF_TOKEN`` (or ``HUGGINGFACE_HUB_TOKEN``) environment
variable; no credential is stored in this file or the repository.

Examples:
    export HF_TOKEN=hf_...            # accept terms at the dataset page first
    python benchmarks/gaia/load_gaia.py
    python benchmarks/gaia/load_gaia.py --config 2023_level1 --limit 5
    python benchmarks/gaia/load_gaia.py --download-attachments
"""
from __future__ import annotations

import argparse
import os
import sys
import textwrap

DATASET_ID = "gaia-benchmark/GAIA"
CONFIGS = ("2023_all", "2023_level1", "2023_level2", "2023_level3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview GAIA benchmark tasks.")
    parser.add_argument("--config", default="2023_all", choices=CONFIGS,
                        help="Dataset config (default: 2023_all).")
    parser.add_argument("--split", default="validation",
                        help="Split to load. Default 'validation'; the 'test' "
                             "split ships without public Final answers.")
    parser.add_argument("--limit", type=int, default=10,
                        help="Number of tasks to print (default: 10).")
    parser.add_argument("--download-attachments", action="store_true",
                        help="Fetch each task's attachment and print its local "
                             "cached path (otherwise only the repo path is shown).")
    return parser.parse_args()


def get_token() -> str | None:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if not token:
        print(
            "WARNING: HF_TOKEN is not set. GAIA is gated, so loading will likely "
            "fail with 401/403.\n"
            "         1. Accept the terms at "
            "https://huggingface.co/datasets/gaia-benchmark/GAIA\n"
            "         2. export HF_TOKEN=hf_...",
            file=sys.stderr,
        )
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
    except Exception as exc:  # surface a readable message instead of a traceback
        print(f"Failed to load {DATASET_ID} [{args.config}/{args.split}]: {exc}",
              file=sys.stderr)
        print("A 401/403 usually means the terms are not accepted or HF_TOKEN is "
              "missing/invalid.", file=sys.stderr)
        return 1

    hf_hub_download = None
    if args.download_attachments:
        from huggingface_hub import hf_hub_download

    count = min(args.limit, len(ds))
    print(f"Loaded {len(ds)} tasks from {DATASET_ID} [{args.config}/{args.split}]. "
          f"Showing first {count}.\n")

    for i in range(count):
        row = ds[i]
        file_name = (row.get("file_name") or "").strip()
        file_path = (row.get("file_path") or "").strip()
        question = str(row.get("Question", "")).replace("\n", " ")

        print(f"[{i + 1}] task_id: {row.get('task_id', '')}")
        print(f"    Level: {row.get('Level', '')}")
        print("    Question: " + textwrap.shorten(question, width=300))

        if file_name:
            print(f"    Attachment: {file_name}  (repo path: {file_path})")
            if args.download_attachments and file_path:
                try:
                    local = hf_hub_download(repo_id=DATASET_ID, filename=file_path,
                                            repo_type="dataset", token=token)
                    print(f"      local: {local}")
                except Exception as exc:
                    print(f"      (download failed: {exc})")
        else:
            print("    Attachment: none")

        print(f"    Final answer: {row.get('Final answer', '')}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
