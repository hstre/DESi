"""Extend Code-Review and Paper-Audit tests with the 4 additional models
to build the cross-task routing table.

For each new model:
  Code-Review: only the 'raw' state (winner for Granite)
  Paper-Audit: only the 'retrieval' top-3 state (winner for Granite)

Reuses the existing 15 code bugs + 30 SciFact claims and their retrievals/haystacks.
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

_HERE = Path(__file__).resolve().parent

NEW_MODELS = [
    "meta-llama/llama-3.2-3b-instruct",
    "meta-llama/llama-3.1-8b-instruct",
    "qwen/qwen-2.5-7b-instruct",
    "mistralai/ministral-3b-2512",
]
PARALLELISM = 4


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
         "X-Title": "DESi Routing"}, body)
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


# ---------------- CODE REVIEW ----------------

from code_review_bugs import BUGS, DISTRACTORS

CR_OUT = _HERE / "results" / "minimaltest_code_review_extended"
CR_OUT.mkdir(parents=True, exist_ok=True)
(CR_OUT / "items").mkdir(exist_ok=True)

CR_SYSTEM = (
    "You are a code reviewer. You will be shown a small Python codebase. "
    "Read it carefully. Identify any bug, security issue, or code smell. "
    "Be specific: name the function and explain the issue in 1-3 sentences. "
    "If you find no issue, say so explicitly."
)
CR_QUESTION = (
    "Audit the following Python code. Find any bugs, security issues, or "
    "subtle correctness problems. Name the function and explain what is wrong."
)


def render_modules(modules):
    return "\n".join(f"# === {name} ===\n{src}" for name, src in modules)


def score_response_cr(text, must_contain, function_name):
    if not text:
        return {"score": 0.0, "bug_localized": False, "bug_described": False}
    t = text.lower()
    loc = function_name.lower() in t
    desc = any(m.lower() in t for m in must_contain)
    if loc and desc:
        s = 1.0
    elif loc or desc:
        s = 0.5
    else:
        s = 0.0
    return {"score": s, "bug_localized": loc, "bug_described": desc}


def run_cr_bug(bug):
    out_path = CR_OUT / "items" / f"{bug['id']}.json"
    if out_path.exists():
        return bug['id']
    modules = [(f"{bug['function']}.py", bug['buggy_source'])] + list(DISTRACTORS)
    user = f"{render_modules(modules)}\n\n=== TASK ===\n{CR_QUESTION}"
    rec = {"bug_id": bug["id"], "function": bug["function"], "runs": []}
    for model in NEW_MODELS:
        r = call_or(model, CR_SYSTEM, user, max_tokens=400)
        text = r.get("text", "") or ""
        sc = score_response_cr(text, bug["must_contain"], bug["function"])
        rec["runs"].append({
            "model": model, "state_type": "raw",
            "response_text": text, **sc,
            "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"),
            "latency_ms": r.get("latency_ms"),
            "error": r.get("error"),
        })
    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return bug["id"]


# ---------------- PAPER AUDIT ----------------

PA_OUT = _HERE / "results" / "minimaltest_paper_audit_extended"
PA_OUT.mkdir(parents=True, exist_ok=True)
(PA_OUT / "items").mkdir(exist_ok=True)
PA_ORIG = _HERE / "results" / "minimaltest_paper_audit" / "items"
SCIFACT = _HERE / "data" / "scifact" / "data"

PA_SYSTEM = (
    "You are a scientific reviewer. You will be given a CLAIM and a set of "
    "scientific paper ABSTRACTS. Your task is to classify the claim relative "
    "to the abstracts as exactly ONE of:\n"
    "  SUPPORT   - the abstracts contain evidence that directly supports the claim\n"
    "  CONTRADICT - the abstracts contain evidence that directly contradicts the claim\n"
    "  NEI       - the abstracts do not provide enough information to support or contradict\n\n"
    "Your entire response must START with a single line in exactly this format:\n"
    "VERDICT: SUPPORT\n"
    "VERDICT: CONTRADICT\n"
    "VERDICT: NEI\n"
    "Then you may explain in 1-2 sentences."
)

import re
_VERDICT_RE = re.compile(r"VERDICT:\s*(SUPPORT|CONTRADICT|NEI)", re.IGNORECASE)


def parse_verdict(text):
    if not text:
        return None
    m = _VERDICT_RE.search(text)
    if m:
        return m.group(1).upper()
    for label in ("CONTRADICT", "SUPPORT", "NEI"):
        if re.search(rf"\b{label}\b", text, re.IGNORECASE):
            return label
    return None


def render_abstract(doc):
    sents = doc.get("abstract") or []
    body = " ".join(sents) if isinstance(sents, list) else sents
    return f"[doc_id {doc['doc_id']}] Title: {doc.get('title','(no title)')}\nAbstract: {body}"


def build_pa_user(claim_text, abstracts):
    parts = [render_abstract(d) for d in abstracts]
    return ("=== ABSTRACTS ===\n\n" + "\n\n".join(parts)
            + f"\n\n=== CLAIM ===\n{claim_text}\n\n"
            "Respond with VERDICT: SUPPORT | CONTRADICT | NEI on the first line, "
            "then brief reasoning.")


def run_pa_item(orig_item, corpus):
    out_path = PA_OUT / "items" / f"claim_{orig_item['claim_id']:04d}.json"
    if out_path.exists():
        return orig_item['claim_id']
    # Use retrieval chosen abstracts
    chosen_ids = orig_item['retrieval_chosen_ids']
    abstracts = [corpus[did] for did in chosen_ids if did in corpus]
    user = build_pa_user(orig_item['claim_text'], abstracts)
    gold = orig_item['gold_label']
    rec = {
        "claim_id": orig_item['claim_id'],
        "claim_text": orig_item['claim_text'],
        "gold_label": gold,
        "retrieval_chosen_ids": chosen_ids,
        "runs": [],
    }
    for model in NEW_MODELS:
        r = call_or(model, PA_SYSTEM, user, max_tokens=200)
        text = r.get("text", "") or ""
        v = parse_verdict(text)
        score = 1.0 if v == gold else 0.0
        rec["runs"].append({
            "model": model, "state_type": "retrieval",
            "response_text": text, "verdict": v, "score": score,
            "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"),
            "latency_ms": r.get("latency_ms"),
            "error": r.get("error"),
        })
    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return orig_item['claim_id']


def main():
    print("=== CODE REVIEW (15 bugs × 4 new models, raw state) ===", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_cr_bug, b): b['id'] for b in BUGS}
        for fut in as_completed(futs):
            try:
                fut.result(); done += 1
                if done % 3 == 0:
                    print(f"  CR [{done}/{len(BUGS)}]", flush=True)
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)

    print("\n=== PAPER AUDIT (30 claims × 4 new models, retrieval state) ===", flush=True)
    corpus = {d['doc_id']: d for d in (json.loads(l) for l in open(SCIFACT / "corpus.jsonl"))}
    pa_items = [json.loads(open(p).read()) for p in sorted(PA_ORIG.glob("*.json"))]
    print(f"  {len(pa_items)} original claims loaded", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_pa_item, it, corpus): it['claim_id'] for it in pa_items}
        for fut in as_completed(futs):
            try:
                fut.result(); done += 1
                if done % 5 == 0:
                    print(f"  PA [{done}/{len(pa_items)}]", flush=True)
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)

    print("\nAll done.", flush=True)


if __name__ == "__main__":
    main()
