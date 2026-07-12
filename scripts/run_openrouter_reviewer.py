"""Run the blind red-team reviewer prompt against a real model via OpenRouter.

Fills the external slot of the background-reviewer red-team with a genuine (ideally
cross-vendor) frontier model. Reads the key from ``OPENROUTER_API_KEY`` — the key is
NEVER embedded, logged, or committed. Saves each run's RAW response verbatim under
``redteam/external_runs/<slug>/run_*.txt``, assembles a probe-keyed
``<slug>.json`` (via the blind id map), and prints the score.

Usage:
    OPENROUTER_API_KEY="$(cat keyfile)" python scripts/run_openrouter_reviewer.py \
        --model openai/gpt-5.1 --slug gpt51 --runs 5 --temperature 0.7
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from desi.case_studies.marcognity_muse_spark.redteam import bench, external_probe  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.reviewers import ExternalReviewer  # noqa: E402

RUNS_DIR = (Path(__file__).resolve().parents[1]
            / "src/desi/case_studies/marcognity_muse_spark/redteam/external_runs")


def call(model: str, prompt: str, temperature: float, key: str) -> tuple[str, dict]:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "X-Title": "desi-redteam"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    msg = data["choices"][0]["message"]
    text = msg.get("content")
    if isinstance(text, list):  # content-parts form
        text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
    usage = data.get("usage", {})
    return (text or ""), usage


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("OPENROUTER_API_KEY not set", file=sys.stderr)
        return 2

    prompt = external_probe.build_prompt()
    out_dir = RUNS_DIR / args.slug
    out_dir.mkdir(parents=True, exist_ok=True)

    runs: list[dict] = []
    tot_in = tot_out = failures = 0
    for i in range(1, args.runs + 1):
        text, usage = "", {}
        for _attempt in range(3):                      # retry transient empty content
            try:
                text, usage = call(args.model, prompt, args.temperature, key)
            except urllib.error.HTTPError as e:
                print(f"run {i}: HTTP {e.code} {e.read()[:200]!r}", file=sys.stderr)
                return 1
            if text.strip():
                break
        (out_dir / f"run_{i}.txt").write_text(text, encoding="utf-8")   # RAW, verbatim
        tot_in += usage.get("prompt_tokens", 0)
        tot_out += usage.get("completion_tokens", 0)
        parsed = external_probe.parse_answer(text)
        if not text.strip() or not any(parsed.values()) and "{" not in text:
            failures += 1
            print(f"run {i}: EMPTY/unparseable — excluded", file=sys.stderr)
            continue
        runs.append(parsed)
        print(f"run {i}: {json.dumps({k: sorted(v) for k, v in parsed.items()}, ensure_ascii=False)}")

    if not runs:
        print("no usable runs", file=sys.stderr)
        return 1
    assembled = {
        "name": args.slug, "runs": runs,
        "profile": {
            "model": args.model, "temperature": args.temperature,
            "n_runs": len(runs), "failed_runs": failures,
            "cost": f"{tot_in} in + {tot_out} out tokens across {len(runs)} usable runs (OpenRouter)",
            "compute": f"{len(runs)} blind passes of {args.model} (cross-vendor frontier LLM)",
        },
    }
    (RUNS_DIR / f"{args.slug}.json").write_text(
        json.dumps(assembled, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    s = bench.score(ExternalReviewer.from_json(RUNS_DIR / f"{args.slug}.json"))
    print(f"\n=== {args.slug} ({args.model}) ===")
    print(f"catch {s['caught']}/{s['positives']}  catch/run {s['caught_per_run']}  "
          f"FP/run {s['false_positives_per_run']} (mean {s['false_positives_mean']})  "
          f"controls {s['controls_clean']}/{s['controls_total']}  stability {s['stability']}")
    print(f"tokens: {tot_in} in + {tot_out} out")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
