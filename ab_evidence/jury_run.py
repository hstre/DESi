"""DESi-Jury pilot: 100 random items from the 500-item sweep, 3-method evaluation.

Methods:
  1. Jaccard (deterministic, threshold 0.25)
  2. Single GPT-4o judge (re-run on the subset to get our own copy)
  3. DESi-Jury: GPT-4o + Sonnet 4.5 + Gemini 2.5 Flash with closed-enumeration prompts

The single-judge and jury are EACH run twice on the same items to measure self-agreement.

Resume-fähig: each item written to disk after all 3 methods + repeats complete.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[0] / "src"))

from jury_prompts import JURY_SYSTEM, aggregate_jury, build_user_message, parse_review

_ITEMS_DIR = _HERE / "results" / "longmemeval_full" / "items"
_OUT_DIR = _HERE / "results" / "jury_pilot"
_OUT_DIR.mkdir(parents=True, exist_ok=True)
_OUT_ITEMS = _OUT_DIR / "items"
_OUT_ITEMS.mkdir(parents=True, exist_ok=True)

SUBSET_SEED = 42
SUBSET_N = 100
PARALLELISM = 4

JURY_MODELS = [
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4.5",
    "google/gemini-2.5-flash",
]

SINGLE_JUDGE_SYSTEM = (
    "You are an impartial grader. Compare a MODEL ANSWER to the GOLD ANSWER for a question. "
    "Respond with EXACTLY one line in this format:\n"
    "SCORE: <0|0.5|1>\n"
    "where 1 = correct, 0.5 = partial, 0 = wrong or refusal."
)


# ---------- Jaccard ----------

_STOP = frozenset(
    "the a an of to in on and or is are was were be been being that this these those it its as at by "
    "for with from has have had do does did but if then than so such into out up down over under about "
    "their they them we you i which who not no only any all per also more most some can".split()
)


def _toks(text):
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return {t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", text.lower())
            if t not in _STOP and len(t) > 2}


def jaccard_score(gold, answer, threshold=0.25):
    g = _toks(gold)
    a = _toks(answer)
    if not g and not a:
        return {"jaccard": None, "score": None}
    j = len(g & a) / len(g | a) if (g | a) else 0.0
    return {"jaccard": round(j, 3), "score": 1.0 if j >= threshold else 0.0,
            "threshold": threshold}


# ---------- HTTP ----------

def _http_post(url, headers, body, timeout=120, retries=4):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            code = e.code
            text = e.read().decode(errors="replace")[:400]
            if code in (400, 401, 403, 404):
                return {"_http_error": code, "_body": text}
            last = f"HTTP {code}: {text}"
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        time.sleep(2 ** i)
    return {"_http_error": "retry_exhausted", "_body": last}


def _call_openrouter(model, system, user, max_tokens=64):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return {"error": "no OPENROUTER_API_KEY", "text": ""}
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens,
    }).encode()
    t0 = time.time()
    d = _http_post(
        "https://openrouter.ai/api/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}",
         "Content-Type": "application/json",
         "HTTP-Referer": "https://github.com/hstre/DESi",
         "X-Title": "DESi Jury Pilot"},
        body,
    )
    latency_ms = int((time.time() - t0) * 1000)
    if "_http_error" in d:
        return {"error": f"{d['_http_error']}: {d.get('_body','')[:200]}",
                "text": "", "latency_ms": latency_ms}
    try:
        text = d["choices"][0]["message"]["content"]
        usage = d.get("usage", {}) or {}
        return {"text": text, "latency_ms": latency_ms,
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens")}
    except Exception as e:
        return {"error": f"parse: {e}", "text": "", "latency_ms": latency_ms}


# ---------- evaluators ----------

def single_judge(question, gold, answer):
    user = (f"QUESTION:\n{question}\n\nGOLD ANSWER:\n{gold}\n\n"
            f"MODEL ANSWER:\n{answer or '(empty)'}")
    r = _call_openrouter("openai/gpt-4o", SINGLE_JUDGE_SYSTEM, user, max_tokens=16)
    text = r.get("text", "") or ""
    score = None
    for line in text.splitlines():
        if line.upper().startswith("SCORE:"):
            try:
                v = float(line.split(":", 1)[1].strip())
                if v not in (0.0, 0.5, 1.0):
                    v = round(v * 2) / 2
                score = v
            except Exception:
                pass
            break
    return {"score": score, "raw": text, "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"), "error": r.get("error")}


def jury_one_reviewer(model, question, gold, answer):
    user = build_user_message(question, gold, answer)
    r = _call_openrouter(model, JURY_SYSTEM, user, max_tokens=64)
    review = parse_review(r.get("text", ""))
    review["model"] = model
    review["input_tokens"] = r.get("input_tokens")
    review["output_tokens"] = r.get("output_tokens")
    review["error"] = r.get("error")
    return review


def jury_run(question, gold, answer):
    reviews = []
    for model in JURY_MODELS:
        reviews.append(jury_one_reviewer(model, question, gold, answer))
    agg = aggregate_jury(reviews)
    return {"reviews": reviews, "aggregate": agg}


# ---------- per-item driver ----------

def run_item(item):
    qid = item["question_id"]
    out_path = _OUT_ITEMS / f"{qid}.json"
    if out_path.exists():
        return qid

    gold = item.get("answer") or item.get("gold_answer")
    rec = {
        "question_id": qid,
        "question_type": item["question_type"],
        "question": item["question"],
        "gold_answer": gold,
        "evaluations": [],
    }
    for orig_run in item["runs"]:
        ans = orig_run.get("response_text", "") or ""
        ev = {
            "model": orig_run["model"],
            "variant": orig_run["variant"],
            "answer_excerpt": ans[:500],
            "original_judge_score": orig_run.get("judge_score"),
            "original_a_error": orig_run.get("error"),
        }
        ev["jaccard"] = jaccard_score(gold, ans)
        ev["single_judge_run1"] = single_judge(item["question"], gold, ans)
        ev["single_judge_run2"] = single_judge(item["question"], gold, ans)
        ev["jury_run1"] = jury_run(item["question"], gold, ans)
        ev["jury_run2"] = jury_run(item["question"], gold, ans)
        rec["evaluations"].append(ev)

    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return qid


# ---------- main ----------

def main():
    # Load all 500 items
    all_items = []
    for p in sorted(_ITEMS_DIR.glob("*.json")):
        all_items.append(json.loads(p.read_text()))
    print(f"Loaded {len(all_items)} items from 500-item sweep", flush=True)

    # Sample 100 deterministically
    rng = random.Random(SUBSET_SEED)
    subset = rng.sample(all_items, SUBSET_N)
    subset_ids = [it["question_id"] for it in subset]
    print(f"Selected {len(subset)} items with seed {SUBSET_SEED}", flush=True)

    # Save subset manifest
    (_OUT_DIR / "subset_manifest.json").write_text(
        json.dumps({"seed": SUBSET_SEED, "n": SUBSET_N,
                    "question_ids": subset_ids}, indent=2) + "\n",
        encoding="utf-8",
    )

    # Run
    done = 0
    existing = {p.stem for p in _OUT_ITEMS.glob("*.json")}
    todo = [it for it in subset if it["question_id"] not in existing]
    print(f"Already done: {len(existing & set(subset_ids))}. To run: {len(todo)}", flush=True)

    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_item, item): item["question_id"] for item in todo}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                fut.result()
                done += 1
                if done % 5 == 0 or done <= 3:
                    print(f"  [{done}/{len(todo)}] {qid} done", flush=True)
            except Exception as e:
                print(f"  ERROR {qid}: {e}", flush=True)

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
