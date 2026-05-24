#!/usr/bin/env python3
"""Run the DESi solver over GAIA and write a submission JSONL.

Loads the gated ``gaia-benchmark/GAIA`` dataset, solves each task via
``desi_gaia_adapter.solve_gaia_task`` (which connects to the real DESi runtime),
and writes one submission line per task. The Hugging Face token is read **only**
from the ``HF_TOKEN`` / ``HUGGINGFACE_HUB_TOKEN`` environment variable; no
credential is stored in this file or the repository.

If the adapter cannot be imported, a local fallback keeps the pipeline running.
The adapter itself reports a ``desi_adapter_fallback`` result when the real DESi
runtime cannot produce an answer (see desi_gaia_adapter.py).

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
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent / "outputs" / "submission.validation.sample.jsonl"
)

# Import the DESi adapter (sibling module). If it cannot be imported, fall back
# locally so the pipeline never aborts.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from desi_gaia_adapter import solve_gaia_task
    _ADAPTER_IMPORT_ERROR: str | None = None
except Exception as exc:  # adapter module itself failed to import
    solve_gaia_task = None  # type: ignore[assignment]
    _ADAPTER_IMPORT_ERROR = repr(exc)


def _local_fallback(error: str) -> dict:
    """Last-resort result used only when the adapter cannot be imported/run."""
    return {
        "model_answer": "",
        "reasoning_trace": f"solve_gaia_local_fallback: {error}",
        "desi_metadata": {"solver": "solve_gaia_local_fallback", "error": error},
    }


def run_solver(task: dict, backend: str, dry_run: bool) -> dict:
    """Solve one task via the adapter, degrading to a local fallback on failure."""
    if solve_gaia_task is None:
        return _local_fallback(f"adapter import failed: {_ADAPTER_IMPORT_ERROR}")
    try:
        return solve_gaia_task(task, backend=backend, dry_run=dry_run)
    except Exception as exc:  # adapter must not abort the run
        return _local_fallback(f"adapter raised: {exc!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the DESi solver over GAIA and write a submission JSONL."
    )
    parser.add_argument("--config", default="2023_all", choices=CONFIGS,
                        help="Dataset config (default: 2023_all).")
    parser.add_argument("--split", default="validation",
                        help="Split to solve (default: validation).")
    parser.add_argument("--limit", type=int, default=5,
                        help="Number of tasks to solve (default: 5).")
    parser.add_argument("--backend", default="auto",
                        choices=("auto", "deepseek", "openrouter", "none"),
                        help="LLM backend (default: auto; 'none' forces the "
                             "DESi-only fallback).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Resolve the backend and run DESi wiring but skip "
                             "the actual LLM network call.")
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

        result = run_solver(dict(row), args.backend, args.dry_run)

        # Run-context metadata, then merge the adapter's solver-specific fields
        # (solver, desi_version_or_commit, governance/replay/claim flags,
        # attachment_seen, error) on top.
        desi_metadata = {
            "config": args.config,
            "split": args.split,
            "level": row.get("Level", ""),
            "has_attachment": bool(file_name),
            "file_name": file_name,
            "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        desi_metadata.update(result.get("desi_metadata", {}))

        record = {
            "task_id": row.get("task_id", ""),
            "model_answer": result.get("model_answer", ""),
            "reasoning_trace": result.get("reasoning_trace", ""),
            "desi_metadata": desi_metadata,
        }
        records.append(json.dumps(record, ensure_ascii=False))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(records) + "\n", encoding="utf-8")

    solver_used = json.loads(records[0])["desi_metadata"].get("solver") if records else "n/a"
    print(f"Solver: {solver_used} | {DATASET_ID} [{args.config}/{args.split}]")
    print(f"Wrote {len(records)} submission line(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
