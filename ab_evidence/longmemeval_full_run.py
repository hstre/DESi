"""Full LongMemEval-s sweep — 500 items, DeepSeek v4-pro + Granite 4.1.

Resume-fähig: speichert nach jedem Item ein eigenes JSON unter
ab_evidence/results/longmemeval_full/items/<question_id>.json.
Beim Neustart werden bereits-fertige Items übersprungen.

Parallelism: ThreadPoolExecutor mit 4 Workern auf Item-Ebene.
Innerhalb eines Items: sequentiell (Sonnet A, Sonnet B, ..., 4 Judge-Calls).
"""
from __future__ import annotations

import ijson
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_DATA = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"
_OUT_DIR = _HERE / "results" / "longmemeval_full"
_ITEMS_DIR = _OUT_DIR / "items"

PARALLELISM = 4

MODELS = {
    "deepseek/deepseek-v4-pro": "deepseek_direct",
    "ibm-granite/granite-4.1-8b": "openrouter",
}
JUDGE_MODEL = "openai/gpt-4o"
JUDGE_BACKEND = "openrouter"

SYSTEM = (
    "You are continuing a long-running conversation. The user will ask a question that "
    "depends on what was said earlier in this conversation. Use ONLY the conversation history "
    "below to answer. If the answer is not in the history, say 'I don't know'."
)
JUDGE_SYSTEM = (
    "You are an impartial grader. Compare a MODEL ANSWER to the GOLD ANSWER for a question. "
    "Respond with EXACTLY one line in this format:\n"
    "SCORE: <0|0.5|1>\n"
    "where 1 = correct (semantically equivalent to gold), 0.5 = partially correct (touches "
    "the right facts but misses or adds material), 0 = wrong or refuses ('I don't know')."
)


# ---------------- HTTP layer ----------------

def _http_post(url, headers, body, timeout=180, retries=4):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            code = e.code
            text = e.read().decode(errors="replace")[:400]
            # 400 (context-too-long etc) = don't retry
            if code in (400, 401, 403, 404):
                return {"_http_error": code, "_body": text}
            last = f"HTTP {code}: {text}"
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        time.sleep(2 ** i)
    return {"_http_error": "retry_exhausted", "_body": last}


def _call_deepseek(model, system, user, max_tokens=512):
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
        return {"error": f"parse: {e}", "text": "", "latency_ms": latency_ms,
                "raw": str(d)[:300]}


def _call_openrouter(model, system, user, max_tokens=512):
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
                    "X-Title": "DESi LongMemEval Benchmark"}, body)
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
        return {"error": f"parse: {e}", "text": "", "latency_ms": latency_ms,
                "raw": str(d)[:300]}


def _call(model, backend, system, user, max_tokens=512):
    if backend == "deepseek_direct":
        return _call_deepseek(model, system, user, max_tokens)
    return _call_openrouter(model, system, user, max_tokens)


# ---------------- prompt construction ----------------

def build_user_message(item, variant):
    sessions = item["haystack_sessions"]
    session_ids = item["haystack_session_ids"]
    evidence = set(item["answer_session_ids"])
    if variant == "A":
        chosen = list(zip(sessions, session_ids))
    else:
        chosen = [(s, sid) for s, sid in zip(sessions, session_ids) if sid in evidence]
    parts = ["=== CONVERSATION HISTORY ==="]
    for sess, sid in chosen:
        parts.append(f"\n--- session {sid} ---")
        for turn in sess:
            role = turn.get("role", "user").upper()
            parts.append(f"{role}: {turn.get('content','')}")
    parts.append("\n=== CURRENT QUESTION ===")
    parts.append(item["question"])
    return "\n".join(parts)


# ---------------- judge ----------------

def judge(question, gold, response_text):
    user = (f"QUESTION:\n{question}\n\nGOLD ANSWER:\n{gold}\n\n"
            f"MODEL ANSWER:\n{response_text or '(empty)'}")
    r = _call(JUDGE_MODEL, JUDGE_BACKEND, JUDGE_SYSTEM, user, max_tokens=24)
    text = r.get("text", "") or ""
    score = None
    for line in text.splitlines():
        if line.upper().startswith("SCORE:"):
            try:
                score = float(line.split(":", 1)[1].strip())
                if score not in (0.0, 0.5, 1.0):
                    score = round(score * 2) / 2
            except Exception:
                pass
            break
    return {"judge_text": text, "score": score, "judge_error": r.get("error")}


# ---------------- per-item runner ----------------

def run_item(item, item_path):
    if item_path.exists():
        # already done
        return None
    res = {
        "question_id": item["question_id"],
        "question_type": item["question_type"],
        "question": item["question"],
        "gold_answer": item["answer"],
        "n_sessions": len(item["haystack_sessions"]),
        "n_evidence_sessions": sum(1 for sid in item["haystack_session_ids"]
                                   if sid in set(item["answer_session_ids"])),
        "runs": [],
    }
    for model, backend in MODELS.items():
        for variant in ("A", "B"):
            user = build_user_message(item, variant)
            r = _call(model, backend, SYSTEM, user, max_tokens=512)
            judged = judge(item["question"], item["answer"], r.get("text", ""))
            res["runs"].append({
                "model": model, "variant": variant, "backend": backend,
                "response_text": r.get("text", ""),
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "latency_ms": r.get("latency_ms"),
                "error": r.get("error"),
                "judge_score": judged["score"],
                "judge_text": judged["judge_text"],
                "judge_error": judged.get("judge_error"),
            })
    item_path.write_text(json.dumps(res, ensure_ascii=False) + "\n", encoding="utf-8")
    return res["question_id"]


# ---------------- driver ----------------

def main():
    _ITEMS_DIR.mkdir(parents=True, exist_ok=True)
    existing = {p.stem for p in _ITEMS_DIR.glob("*.json")}
    print(f"already done: {len(existing)}", flush=True)

    todo = []
    with open(_DATA, "rb") as f:
        for obj in ijson.items(f, "item"):
            if obj["question_id"] in existing:
                continue
            todo.append(obj)
    print(f"to run: {len(todo)}", flush=True)

    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_item, item,
                          _ITEMS_DIR / f"{item['question_id']}.json"): item["question_id"]
                for item in todo}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                fut.result()
                done += 1
                if done % 10 == 0 or done <= 5:
                    print(f"  [{done}/{len(todo)}] {qid} done", flush=True)
            except Exception as e:
                print(f"  ERROR {qid}: {e}", flush=True)


if __name__ == "__main__":
    main()
