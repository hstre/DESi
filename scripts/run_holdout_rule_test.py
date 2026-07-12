"""Blind hold-out test of the FROZEN DESi rules: Granite-8B alone vs + rules.

The rules (``redteam/hard2/rules.py``) were frozen by commit before this hold-out was
authored. This harness runs Granite-4.1-8b on the hold-out in batches of <=10 excerpts
(its calibrated k*=10 evidence band), applies the frozen rules as a post-layer, and
reports every requested metric SEPARATELY: significance recall, overclaim FP reduction,
newly-created FN, overall F1/P/R, rule coverage + escalation rate, variance, cost.

No rule edits, no gold peeking. Key from OPENROUTER_API_KEY (env only).

    OPENROUTER_API_KEY="$(cat keyfile)" python scripts/run_holdout_rule_test.py --runs 5
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
from desi.case_studies.marcognity_muse_spark.redteam.hard2 import rules  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.hard2.items import Flag2  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.hard2_holdout import prompt  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.hard2_holdout.items import (  # noqa: E402
    HOLDOUT_ITEMS,
)

# the cheap tier (blended $/Mtok as documented in the hard2 scorecard); granite-8b is
# already measured and its raw runs are reused, not re-run.
CHEAP_MODELS = [
    ("ibm-granite/granite-4.1-8b", "granite_8b", 0.10),
    ("ibm-granite/granite-4.0-h-micro", "granite_micro", 0.11),
    ("google/gemma-3-12b-it", "gemma3_12b", 0.15),
    ("deepseek/deepseek-v4-flash", "deepseek_v4_flash", 0.15),
    ("mistralai/ministral-8b-2512", "ministral_8b", 0.15),
    ("google/gemma-4-31b-it", "gemma4_31b", 0.16),
    ("qwen/qwen3-30b-a3b", "qwen3_30b", 0.19),
]
_BASE = (Path(__file__).resolve().parents[1]
         / "src/desi/case_studies/marcognity_muse_spark/redteam/hard2_holdout")
_TEXT = {it.id: it.text for it in HOLDOUT_ITEMS}
_GOLD = {it.id: set(it.gold) for it in HOLDOUT_ITEMS}


def call(model: str, text_prompt: str, key: str, temperature: float) -> tuple[str, dict]:
    body = json.dumps({"model": model, "temperature": temperature,
                       "messages": [{"role": "user", "content": text_prompt}]}).encode()
    for attempt in range(6):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "X-Title": "desi-holdout"})
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
    txt = msg.get("content") or ""
    if isinstance(txt, list):
        txt = "".join(p.get("text", "") for p in txt if isinstance(p, dict))
    return txt, data.get("usage", {})


def one_run(model: str, slug: str, run_i: int, key: str, temperature: float) -> tuple[dict, int]:
    """Run one model over all batches; return (item->flags, total tokens). Resumable."""
    raw_dir = _BASE / "external_runs" / slug
    raw_dir.mkdir(parents=True, exist_ok=True)
    flags: dict[str, set] = {}
    tokens = 0
    for b, (ptext, id_map) in enumerate(prompt.build_prompts(), 1):
        raw_path = raw_dir / f"run_{run_i}_batch_{b}.txt"
        if raw_path.exists() and raw_path.read_text().strip():
            text = raw_path.read_text()
        else:
            text, usage = "", {}
            for _ in range(3):
                text, usage = call(model, ptext, key, temperature)
                if text.strip():
                    break
            raw_path.write_text(text, encoding="utf-8")
            tokens += usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        flags.update(prompt.parse_answer(text, id_map))
    return flags, tokens


def _recall(runs, flag):
    tp = fn = 0
    for it in HOLDOUT_ITEMS:
        if flag in it.gold:
            for r in runs:
                tp += flag in r.get(it.id, set())
                fn += flag not in r.get(it.id, set())
    return round(tp / (tp + fn), 3) if tp + fn else None


def _fp(runs, flag):
    return sum(flag in r.get(it.id, set())
              for it in HOLDOUT_ITEMS if flag not in it.gold for r in runs)


def _new_fn(base_runs, aug_runs):
    """gold flags present in baseline output but lost after the rule (collateral)."""
    n = 0
    for br, ar in zip(base_runs, aug_runs):
        for it in HOLDOUT_ITEMS:
            lost = (set(br.get(it.id, set())) & it.gold) - set(ar.get(it.id, set()))
            n += len(lost)
    return n


def _new_fp(base_runs, aug_runs):
    """non-gold flags the rule ADDED that the baseline did not have (collateral)."""
    n = 0
    for br, ar in zip(base_runs, aug_runs):
        for it in HOLDOUT_ITEMS:
            added = (set(ar.get(it.id, set())) - set(br.get(it.id, set()))) - it.gold
            n += len(added)
    return n


def _coverage_escalation(base_runs, aug_runs):
    """coverage: rule intervened (add/remove). escalation: rule conflicts with the LLM
    (removed an LLM flag, or added SIG where the LLM already raised overclaim) — the
    boundary cases a pipeline would route to a stronger reviewer / human."""
    n = len(base_runs) * len(HOLDOUT_ITEMS)
    cov = esc = 0
    for br, ar in zip(base_runs, aug_runs):
        for it in HOLDOUT_ITEMS:
            b, a = set(br.get(it.id, set())), set(ar.get(it.id, set()))
            if a != b:
                cov += 1
            removed = b - a
            added = a - b
            if removed or (Flag2.SIGNIFICANCE_NOT_IMPORTANCE in added and Flag2.OVERCLAIM in b):
                esc += 1
    return round(cov / n, 3), round(esc / n, 3)


def evaluate(model: str, slug: str, price: float, runs: int, key: str, temp: float,
             apply_fn=rules.apply_rules) -> dict:
    base_runs, tokens = [], 0
    for i in range(1, runs + 1):
        fl, tok = one_run(model, slug, i, key, temp)
        base_runs.append(fl)
        tokens += tok
    aug_runs = [{iid: apply_fn(_TEXT[iid], fl) for iid, fl in r.items()}
                for r in base_runs]
    b = score.score_runs(slug, base_runs, HOLDOUT_ITEMS)
    a = score.score_runs(f"{slug}+rule", aug_runs, HOLDOUT_ITEMS)
    cov, esc = _coverage_escalation(base_runs, aug_runs)
    n_reviews = runs * len(HOLDOUT_ITEMS)
    cpr = (tokens / 1e6 * price / n_reviews) if tokens else None
    return {
        "model": model, "slug": slug, "runs": runs, "batch_size": prompt.BATCH_SIZE,
        "significance_recall": {"baseline": _recall(base_runs, Flag2.SIGNIFICANCE_NOT_IMPORTANCE),
                                "with_rule": _recall(aug_runs, Flag2.SIGNIFICANCE_NOT_IMPORTANCE)},
        "overclaim_fp": {"baseline": _fp(base_runs, Flag2.OVERCLAIM),
                         "with_rule": _fp(aug_runs, Flag2.OVERCLAIM)},
        "new_false_negatives_from_rule": _new_fn(base_runs, aug_runs),
        "new_false_positives_from_rule": _new_fp(base_runs, aug_runs),
        "overall": {
            "baseline": {k: b[k] for k in ("f1_mean", "f1_stdev", "precision_mean", "recall_mean")},
            "with_rule": {k: a[k] for k in ("f1_mean", "f1_stdev", "precision_mean", "recall_mean")},
        },
        "rule_coverage": cov, "escalation_rate": esc,
        "variance_f1_stdev": {"baseline": b["f1_stdev"], "with_rule": a["f1_stdev"]},
        "cost": {"tokens_total": tokens,
                 "usd_per_review_model": round(cpr, 8) if cpr else None,
                 "usd_per_review_rule": 0.0},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--models", default="cheap",
                    help="'cheap' for the built-in cheap tier, or 'id:slug:price,...'")
    ap.add_argument("--rules", choices=("v1", "v2"), default="v1",
                    help="which frozen R1 to wire into the post-layer")
    args = ap.parse_args()
    apply_fn = rules.apply_rules_v2 if args.rules == "v2" else rules.apply_rules
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("OPENROUTER_API_KEY not set", file=sys.stderr)
        return 2

    if args.models == "cheap":
        specs = CHEAP_MODELS
    else:
        specs = [(s.split(":")[0], s.split(":")[1], float(s.split(":")[2]))
                 for s in args.models.split(",")]

    cards = []
    for model, slug, price in specs:
        try:
            r = evaluate(model, slug, price, args.runs, key, args.temperature, apply_fn)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"{slug}: FAILED ({e}) — skipped", file=sys.stderr)
            continue
        cards.append(r)
        o = r["overall"]
        print(f"{slug:18s} F1 {o['baseline']['f1_mean']:.3f} -> {o['with_rule']['f1_mean']:.3f} "
              f"(Δ {o['with_rule']['f1_mean'] - o['baseline']['f1_mean']:+.3f})  "
              f"sig-R {r['significance_recall']['baseline']}->{r['significance_recall']['with_rule']}  "
              f"newFN {r['new_false_negatives_from_rule']} newFP {r['new_false_positives_from_rule']}",
              file=sys.stderr)

    suffix = "" if args.rules == "v1" else f"_{args.rules}"
    (_BASE / f"holdout_rule_scorecard_all{suffix}.json").write_text(
        json.dumps({"n_items": len(HOLDOUT_ITEMS), "rules": args.rules, "cards": cards},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"cards": cards}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
