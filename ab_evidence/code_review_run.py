"""Code-Review Minimaltest: Q4/Q8 × Raw-Codebase vs Retrieval-Top-3.

For each of 15 buggy modules:
  1. Build a "codebase" = the buggy module + 8 distractor modules
  2. Question: "Audit this codebase. Find any bug and explain it."
  3. Conditions:
     - Q4/Q8 + raw codebase (all 9 modules in full)
     - Q4/Q8 + retrieval top-3 (by embedding similarity to the question)
  4. Score: does the response contain ANY of the bug's must_contain markers?

  Plus a bonus condition: Oracle = just the buggy module.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from code_review_bugs import BUGS, DISTRACTORS

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "results" / "minimaltest_code_review"
_ITEMS_OUT = _OUT / "items"
_ITEMS_OUT.mkdir(parents=True, exist_ok=True)

MODELS = ["ibm-granite/granite-4.1-8b", "ibm-granite/granite-4.0-h-micro"]
PARALLELISM = 4
TOP_K = 3

SYSTEM = (
    "You are a code reviewer. You will be shown a small Python codebase. "
    "Read it carefully. Identify any bug, security issue, or code smell. "
    "Be specific: name the function and explain the issue in 1-3 sentences. "
    "If you find no issue, say so explicitly."
)

QUESTION = (
    "Audit the following Python code. Find any bugs, security issues, or "
    "subtle correctness problems. Name the function and explain what is wrong."
)


def _http_post(url, headers, body, timeout=180, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:400]
            if e.code in (400, 401, 403, 404):
                return {"_http_error": e.code, "_body": text}
            last = f"HTTP {e.code}: {text}"
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        time.sleep(2 ** i)
    return {"_http_error": "retry_exhausted", "_body": last}


def call_or(model, system, user, max_tokens=400):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
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
        {"Authorization": f"Bearer {key}",
         "Content-Type": "application/json",
         "HTTP-Referer": "https://github.com/hstre/DESi",
         "X-Title": "DESi CodeReview"}, body)
    lat = int((time.time() - t0) * 1000)
    if "_http_error" in d:
        return {"error": f"{d['_http_error']}: {d.get('_body','')[:200]}", "text": "", "latency_ms": lat}
    try:
        text = d["choices"][0]["message"]["content"]
        u = d.get("usage", {}) or {}
        return {"text": text, "latency_ms": lat,
                "input_tokens": u.get("prompt_tokens"),
                "output_tokens": u.get("completion_tokens")}
    except Exception as e:
        return {"error": f"parse: {e}", "text": "", "latency_ms": lat}


def score_response(text: str, must_contain: list[str], function_name: str) -> dict:
    """Score by:
      - bug_localized: does response mention the buggy function name?
      - bug_described: does response contain any of the must_contain markers?
      - score: 1.0 if both, 0.5 if only function name, 0.0 if neither
    """
    if not text:
        return {"score": 0.0, "bug_localized": False, "bug_described": False}
    t = text.lower()
    bug_localized = function_name.lower() in t
    bug_described = any(m.lower() in t for m in must_contain)
    if bug_localized and bug_described:
        score = 1.0
    elif bug_localized or bug_described:
        score = 0.5
    else:
        score = 0.0
    return {"score": score, "bug_localized": bug_localized, "bug_described": bug_described}


def build_codebase(bug, distractors):
    """Build the 9-module codebase: 1 buggy + 8 distractors."""
    modules = [(f"{bug['function']}.py", bug["buggy_source"])]
    for name, src in distractors:
        modules.append((name, src))
    return modules


def render_modules(modules):
    parts = []
    for name, src in modules:
        parts.append(f"# === {name} ===\n{src}")
    return "\n".join(parts)


_EMBED_MODEL = None


def embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED_MODEL


def topk_modules(modules, question, k=3):
    em = embed_model()
    texts = [src for _, src in modules]
    q_emb = em.encode([question], normalize_embeddings=True)
    m_embs = em.encode(texts, normalize_embeddings=True, batch_size=8, show_progress_bar=False)
    sims = (m_embs @ q_emb.T).ravel()
    top_idx = np.argsort(-sims)[:k].tolist()
    return [modules[i] for i in top_idx], [float(sims[i]) for i in top_idx], top_idx


def run_one_bug(bug):
    out_path = _ITEMS_OUT / f"{bug['id']}.json"
    if out_path.exists():
        return bug["id"]

    modules = build_codebase(bug, DISTRACTORS)
    rec = {
        "bug_id": bug["id"],
        "bug_type": bug["bug_type"],
        "function": bug["function"],
        "n_modules_total": len(modules),
        "must_contain": bug["must_contain"],
        "runs": [],
    }

    # === Raw: full codebase ===
    raw_ctx = render_modules(modules)
    raw_user = f"{raw_ctx}\n\n=== TASK ===\n{QUESTION}"

    # === Oracle: just the buggy module ===
    oracle_ctx = render_modules([modules[0]])
    oracle_user = f"{oracle_ctx}\n\n=== TASK ===\n{QUESTION}"

    # === Retrieval: top-3 by embedding similarity ===
    chosen, sims, idx = topk_modules(modules, QUESTION, TOP_K)
    chosen_names = [name for name, _ in chosen]
    buggy_in_top_k = bug["function"] + ".py" in chosen_names
    retr_ctx = render_modules(chosen)
    retr_user = f"{retr_ctx}\n\n=== TASK ===\n{QUESTION}"

    rec["retrieval"] = {
        "chosen": chosen_names,
        "similarities": sims,
        "buggy_module_in_top_k": buggy_in_top_k,
    }

    for state_type, user_msg in [("raw", raw_user), ("oracle", oracle_user), ("retrieval", retr_user)]:
        for model in MODELS:
            r = call_or(model, SYSTEM, user_msg, max_tokens=400)
            text = r.get("text", "") or ""
            scoring = score_response(text, bug["must_contain"], bug["function"])
            rec["runs"].append({
                "model": model,
                "state_type": state_type,
                "response_text": text,
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "latency_ms": r.get("latency_ms"),
                "error": r.get("error"),
                **scoring,
            })

    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return bug["id"]


def main():
    print(f"Running {len(BUGS)} bug cases x 3 state types x 2 models = {len(BUGS)*6} API calls", flush=True)
    embed_model().encode(["warmup"])
    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_one_bug, b): b["id"] for b in BUGS}
        for fut in as_completed(futs):
            bid = futs[fut]
            try:
                fut.result()
                done += 1
                if done % 3 == 0 or done <= 2:
                    print(f"  [{done}/{len(BUGS)}] {bid}", flush=True)
            except Exception as e:
                print(f"  ERROR {bid}: {type(e).__name__}: {e}", flush=True)
    print(f"\nDone. {done}/{len(BUGS)}", flush=True)


if __name__ == "__main__":
    main()
