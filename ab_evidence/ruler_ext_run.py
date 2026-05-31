"""RULER-Extended A/B run: 3 long lengths (32k/64k/131k) × 3 niah tasks × 20 items × 2 models.

Same A/B design as ruler_run.py, but uses MaxJeblick/Ruler (gated) for extreme-length splits.
Schema differs (input/outputs/answer_start vs context/answer/answer_prefix), so a separate runner.

Variant A: full RULER context (32k/64k/131k tokens).
Variant B: deterministic needle window — sentence containing gold answer plus up to 2 sentences before and after.

Designed to run on GitHub Actions Ubuntu runner with secrets:
  OPENROUTER_API_KEY, DEEPSEEK_API_KEY, HF_TOKEN (required — dataset is gated).
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
_OUT_DIR = _HERE / "results" / "ruler_ext_bench"
_ITEMS_DIR = _OUT_DIR / "items"
_OUT_DIR.mkdir(parents=True, exist_ok=True)
_ITEMS_DIR.mkdir(parents=True, exist_ok=True)
_CACHE = _HERE / "data" / "ruler_ext"
_CACHE.mkdir(parents=True, exist_ok=True)

LENGTHS = ["32768", "65536", "131072"]
TASKS = ["niah_single_1", "niah_multikey_2", "niah_single_3"]
N_PER_TASK = 20
PARALLELISM = 4

MODELS = {
    "deepseek/deepseek-v4-pro": "deepseek_direct",
    "ibm-granite/granite-4.1-8b": "openrouter",
}

SEED = 42


# ---------- HF dataset loading ----------

def load_split(length: str, task: str):
    """Download (if needed) and load one (length, task) parquet from MaxJeblick/Ruler.

    File pattern: data/{length}_{task}-00000-of-00001.parquet
    Schema: index, input, question, outputs, length, answer_start
    """
    from huggingface_hub import hf_hub_download
    fname = f"data/{length}_{task}-00000-of-00001.parquet"
    local = _CACHE / f"{length}_{task}-00000-of-00001.parquet"
    if not local.exists():
        token = os.environ.get("HF_TOKEN")
        kwargs = {"repo_type": "dataset"}
        if token:
            kwargs["token"] = token
        p = hf_hub_download("MaxJeblick/Ruler", fname, **kwargs)
        local = Path(p)
    return pd.read_parquet(local)


# ---------- Variant B: needle-window extraction (same as ruler_run.py) ----------

def extract_needle_window(context: str, gold_answer: str, sentences_around: int = 2) -> str:
    if not gold_answer:
        return context[:1000]
    idx = context.find(gold_answer)
    if idx < 0:
        return context[:1500]
    before = context[:idx]
    after = context[idx:]
    before_sentences = re.split(r"(?<=[.!?])\s+", before)
    after_sentences = re.split(r"(?<=[.!?])\s+", after)
    take_before = before_sentences[-(sentences_around + 1):] if len(before_sentences) > 0 else []
    take_after = after_sentences[:sentences_around + 1] if len(after_sentences) > 0 else []
    window = " ".join(take_before + take_after)
    if len(window) > 1500:
        window = window[:1500]
    return window


# ---------- HTTP (timeout raised for long inputs at 131k) ----------

def _http_post(url, headers, body, timeout=300, retries=4):
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


def _call_deepseek(model, system, user, max_tokens=128):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return {"error": "no DEEPSEEK_API_KEY", "text": ""}
    body = json.dumps({
        "model": model.split("/", 1)[-1],
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens,
    }).encode()
    t0 = time.time()
    d = _http_post("https://api.deepseek.com/v1/chat/completions",
                   {"Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"}, body)
    lat = int((time.time() - t0) * 1000)
    if "_http_error" in d:
        return {"error": f"{d['_http_error']}: {d.get('_body','')[:200]}", "text": "",
                "latency_ms": lat}
    try:
        text = d["choices"][0]["message"]["content"]
        u = d.get("usage", {}) or {}
        return {"text": text, "latency_ms": lat,
                "input_tokens": u.get("prompt_tokens"),
                "output_tokens": u.get("completion_tokens")}
    except Exception as e:
        return {"error": f"parse: {e}", "text": "", "latency_ms": lat}


def _call_openrouter(model, system, user, max_tokens=128):
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
    d = _http_post("https://openrouter.ai/api/v1/chat/completions",
                   {"Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/hstre/DESi",
                    "X-Title": "DESi RULER-Ext Benchmark"}, body)
    lat = int((time.time() - t0) * 1000)
    if "_http_error" in d:
        return {"error": f"{d['_http_error']}: {d.get('_body','')[:200]}", "text": "",
                "latency_ms": lat}
    try:
        text = d["choices"][0]["message"]["content"]
        u = d.get("usage", {}) or {}
        return {"text": text, "latency_ms": lat,
                "input_tokens": u.get("prompt_tokens"),
                "output_tokens": u.get("completion_tokens")}
    except Exception as e:
        return {"error": f"parse: {e}", "text": "", "latency_ms": lat}


def call_model(model, backend, system, user, max_tokens=128):
    if backend == "deepseek_direct":
        return _call_deepseek(model, system, user, max_tokens)
    return _call_openrouter(model, system, user, max_tokens)


# ---------- scoring (same as ruler_run.py) ----------

def score_response(response_text: str, gold_answer) -> float:
    if not response_text:
        return 0.0
    rt = response_text.lower()
    if isinstance(gold_answer, str):
        gold_list = [gold_answer]
    else:
        gold_list = list(gold_answer)
    if not gold_list:
        return 0.0
    hits = sum(1 for g in gold_list if str(g).lower() in rt)
    return round(hits / len(gold_list), 3)


# ---------- prompt ----------

SYSTEM = ("You are answering a question based on the provided context. "
          "Read the context carefully and answer concisely. Do not include explanations "
          "unless asked.")


def build_user_message(context: str, question: str) -> str:
    return f"{context}\n\n{question}\n\nAnswer:"


# ---------- per-item ----------

def run_item(item_key: str, row: dict):
    out_path = _ITEMS_DIR / f"{item_key}.json"
    if out_path.exists():
        return item_key

    context = row["input"]
    question = row["question"]
    gold = row["outputs"]
    gold_list = list(gold) if not isinstance(gold, str) else [gold]

    primary_gold = str(gold_list[0]) if gold_list else ""
    window = extract_needle_window(context, primary_gold)

    user_A = build_user_message(context, question)
    user_B = build_user_message(window, question)

    rec = {
        "item_key": item_key,
        "length": row["_length"],
        "task": row["_task"],
        "question": question,
        "gold_answer": gold_list,
        "context_len_chars": len(context),
        "window_len_chars": len(window),
        "runs": [],
    }

    for model, backend in MODELS.items():
        for variant, user in (("A", user_A), ("B", user_B)):
            r = call_model(model, backend, SYSTEM, user, max_tokens=128)
            s = score_response(r.get("text", ""), gold_list)
            rec["runs"].append({
                "model": model, "variant": variant,
                "response_text": r.get("text", ""),
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "latency_ms": r.get("latency_ms"),
                "error": r.get("error"),
                "score": s,
            })

    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return item_key


# ---------- main ----------

def main():
    print(f"Loading RULER-Ext splits: {LENGTHS} x {TASKS}", flush=True)
    import random
    rng = random.Random(SEED)

    todo = []
    for length in LENGTHS:
        for task in TASKS:
            df = load_split(length, task)
            n = len(df)
            idxs = rng.sample(range(n), min(N_PER_TASK, n))
            for i in idxs:
                row = df.iloc[i].to_dict()
                row["_length"] = length
                row["_task"] = task
                if "outputs" in row and hasattr(row["outputs"], "tolist"):
                    row["outputs"] = row["outputs"].tolist()
                key = f"{length}_{task}_{i:04d}"
                todo.append((key, row))

    existing = {p.stem for p in _ITEMS_DIR.glob("*.json")}
    pending = [(k, r) for k, r in todo if k not in existing]
    already_done = len(existing & {k for k, _ in todo})
    print(f"Total: {len(todo)}  Already done: {already_done}  "
          f"Pending: {len(pending)}", flush=True)

    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_item, k, r): k for k, r in pending}
        for fut in as_completed(futs):
            k = futs[fut]
            try:
                fut.result()
                done += 1
                if done % 10 == 0 or done <= 3:
                    print(f"  [{done}/{len(pending)}] {k} done", flush=True)
            except Exception as e:
                print(f"  ERROR {k}: {e}", flush=True)

    print(f"\nDone. {done}/{len(pending)} new items written.", flush=True)


if __name__ == "__main__":
    main()
