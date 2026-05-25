#!/usr/bin/env python3
"""Run TruthfulQA through a DESi-governed LLM and write a JSONL.

TruthfulQA (`truthfulqa/truthful_qa`, config `generation`) is a static, offline
truthfulness benchmark: each question has a `best_answer` plus lists of
`correct_answers` and `incorrect_answers` (the common false beliefs). We reuse
the GAIA adapter (`solve_gaia_task`) for backend selection + DESi governance
(replay / claim tracking / run_desi) and the model-resolution + usage metadata.

`--reasoning-cutoff` flags answers as reasoning-inefficient when the response
was truncated (`finish_reason == "length"`) or the reasoning-token count exceeds
the threshold — DESi cares about reasoning efficiency, not just correctness.

The HF/LLM tokens are read **only** from the environment by the adapter; none
are stored here.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Reuse the GAIA adapter (backend selection + DESi governance + usage metadata).
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gaia"))
from desi_gaia_adapter import raw_llm_answer, solve_gaia_task  # noqa: E402
from desi_intervention import apply_desi_intervention  # noqa: E402

DATASET_ID = "truthfulqa/truthful_qa"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "outputs" / "truthfulqa.sample.jsonl"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run TruthfulQA through DESi.")
    p.add_argument("--config", default="generation")
    p.add_argument("--split", default="validation")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--mode", default="desi_governed",
                   choices=("desi_governed", "llm_only", "desi_intervened"),
                   help="desi_governed (default): DESi adapter + governance "
                        "metadata. llm_only: same call, no governance. "
                        "desi_intervened: governed call, then DESi decides to "
                        "accept/abstain/reject and may replace the answer.")
    p.add_argument("--backend", default="auto",
                   choices=("auto", "hf", "openrouter", "deepseek", "none"))
    p.add_argument("--model", default=None, help="Model id for the backend.")
    p.add_argument("--prompt-mode", default="strict", choices=("strict", "minimal"))
    p.add_argument("--reasoning-cutoff", type=int, default=1500,
                   help="Flag answers as inefficient when reasoning_tokens exceed "
                        "this (or finish_reason==length). Default 1500.")
    p.add_argument("--general-checks", action=argparse.BooleanOptionalAction,
                   default=True,
                   help="Enable dataset-independent epistemic risk checks "
                        "(desi_intervened mode only). Default on.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return p.parse_args()


def main() -> int:
    args = parse_args()
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

    count = min(args.limit, len(ds))
    records: list[str] = []

    _PROVIDER_KEYS = ("backend", "requested_model", "resolved_model",
                      "provider_returned_model", "provider", "finish_reason",
                      "usage")

    for i in range(count):
        row = ds[i]
        question = str(row.get("question", ""))
        task = {"task_id": f"tqa-{i:04d}", "Question": question}  # no attachment

        if args.mode in ("desi_governed", "desi_intervened"):
            result = solve_gaia_task(
                task, backend=args.backend, model=args.model,
                prompt_mode=args.prompt_mode, dry_run=args.dry_run,
            )
            answer = result.get("model_answer", "")
            meta = result.get("desi_metadata", {})
            reasoning_trace = result.get("reasoning_trace", "")
            provider_meta = {k: meta.get(k) for k in _PROVIDER_KEYS}
            desi_metadata = meta
        else:  # llm_only — same path, no DESi governance
            result = raw_llm_answer(
                task, backend=args.backend, model=args.model,
                prompt_mode=args.prompt_mode, dry_run=args.dry_run,
            )
            answer = result.get("model_answer", "")
            reasoning_trace = ""
            provider_meta = result.get("provider_meta", {})
            desi_metadata = None

        usage = provider_meta.get("usage") or {}
        reasoning_tokens = usage.get("reasoning_tokens")
        finish_reason = provider_meta.get("finish_reason")
        inefficient = bool(
            finish_reason == "length"
            or (reasoning_tokens is not None and reasoning_tokens > args.reasoning_cutoff)
        )

        record = {
            "task_id": task["task_id"],
            "question": question,
            "mode": args.mode,
            "model_answer": answer,
            "reasoning_trace": reasoning_trace,
            "provider_meta": provider_meta,
            "desi_metadata": desi_metadata,
            "static_eval": {
                "benchmark": "truthfulqa",
                "category": row.get("category"),
                "best_answer": row.get("best_answer"),
                "correct_answers": list(row.get("correct_answers", []) or []),
                "incorrect_answers": list(row.get("incorrect_answers", []) or []),
                "answer_chars": len(answer),
                "answer_words": len(answer.split()),
                "finish_reason": finish_reason,
                "reasoning_tokens": reasoning_tokens,
                "reasoning_cutoff": args.reasoning_cutoff,
                "reasoning_inefficient": inefficient,
            },
        }
        if args.mode == "desi_intervened":
            record = apply_desi_intervention(
                record,
                {"correct_answers": record["static_eval"]["correct_answers"],
                 "incorrect_answers": record["static_eval"]["incorrect_answers"]},
                reasoning_cutoff=args.reasoning_cutoff,
                general_checks=args.general_checks,
            )
        records.append(json.dumps(record, ensure_ascii=False))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(records) + "\n", encoding="utf-8")
    print(f"Mode: {args.mode} | {DATASET_ID} [{args.config}/{args.split}]")
    print(f"Wrote {len(records)} record(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
