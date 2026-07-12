"""Run the HARD epistemic-failure benchmark against cross-vendor frontier models.

Blind (neutral ids, no gold labels). Reads the key from OPENROUTER_API_KEY — never
embedded/logged/committed. Saves each run's RAW response verbatim, then scores
multi-label (precision/recall/F1, exact-match, per-difficulty, per-item).

    OPENROUTER_API_KEY="$(cat keyfile)" python scripts/run_hard_benchmark.py \
        --models openai/gpt-5.1:gpt51,google/gemini-2.5-pro:gemini25pro,x-ai/grok-4.5:grok45 \
        --runs 5 --temperature 0.7
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from desi.case_studies.marcognity_muse_spark.redteam.hard import score  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.hard import prompt as hard_prompt  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.hard.items import HARD_ITEMS  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.hard2 import prompt as hard2_prompt  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.hard2.items import HARD2_ITEMS  # noqa: E402

_BASE = Path(__file__).resolve().parents[1] / "src/desi/case_studies/marcognity_muse_spark/redteam"
_BENCH = {
    "hard": (hard_prompt, HARD_ITEMS, _BASE / "hard"),
    "hard2": (hard2_prompt, HARD2_ITEMS, _BASE / "hard2"),
}


def call(model: str, text_prompt: str, temperature: float, key: str) -> tuple[str, dict]:
    body = json.dumps({"model": model, "temperature": temperature,
                       "messages": [{"role": "user", "content": text_prompt}]}).encode()
    # retry on rate-limit (429, common on :free) and transient 5xx, with backoff
    for attempt in range(6):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "X-Title": "desi-redteam-hard"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 5:
                time.sleep(min(3 * (attempt + 1), 20))
                continue
            raise
    msg = data["choices"][0]["message"]
    txt = msg.get("content")
    if isinstance(txt, list):
        txt = "".join(p.get("text", "") for p in txt if isinstance(p, dict))
    return (txt or ""), data.get("usage", {})


def run_model(model: str, slug: str, n: int, temp: float, key: str,
              prompt_mod, items, runs_dir: Path) -> dict:
    p = prompt_mod.build_prompt()
    out_dir = runs_dir / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    runs: list[dict] = []
    tin = tout = 0
    for i in range(1, n + 1):
        text, usage = "", {}
        for _ in range(3):
            text, usage = call(model, p, temp, key)
            if text.strip():
                break
        (out_dir / f"run_{i}.txt").write_text(text, encoding="utf-8")
        tin += usage.get("prompt_tokens", 0)
        tout += usage.get("completion_tokens", 0)
        parsed = prompt_mod.parse_answer(text)
        if not text.strip() or "{" not in text:
            print(f"  {slug} run {i}: EMPTY/unparseable — excluded", file=sys.stderr)
            continue
        runs.append({k: v for k, v in parsed.items()})
    s = score.score_runs(slug, runs, items)
    s["model"] = model
    s["tokens"] = {"in": tin, "out": tout, "per_run": round((tin + tout) / max(len(runs), 1))}
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", choices=list(_BENCH), default="hard")
    ap.add_argument("--models", default="openai/gpt-5.1:gpt51,"
                    "google/gemini-2.5-pro:gemini25pro,x-ai/grok-4.5:grok45")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("OPENROUTER_API_KEY not set", file=sys.stderr)
        return 2

    prompt_mod, items, bench_dir = _BENCH[args.benchmark]
    runs_dir = bench_dir / "external_runs"
    scores = []
    for spec in args.models.split(","):
        model, slug = spec.rsplit(":", 1) if spec.count(":") > 1 else spec.split(":")
        try:
            s = run_model(model, slug, args.runs, args.temperature, key,
                          prompt_mod, items, runs_dir)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"{slug}: FAILED ({e}) — skipped", file=sys.stderr)
            continue
        scores.append(s)
        print(f"{slug:<20} F1 {s['f1_mean']}±{s['f1_stdev']}  exact {s['exact_match_mean']}  "
              f"P {s['precision_mean']}  R {s['recall_mean']}  "
              f"tok/run {s['tokens']['per_run']}")

    card = bench_dir / f"{args.benchmark}_scorecard.json"
    score.write_scorecard(card, scores, items)
    print(f"\nscorecard -> {card}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
