"""Frontier-tier calibration: measure 8 new models on the 3 DESi task classes.

Models tested:
  Cheap (4):
    anthropic/claude-haiku-4.5
    openai/gpt-5-nano
    openai/gpt-4o-mini
    google/gemini-2.5-flash-lite
  Mid (4):
    anthropic/claude-sonnet-4.6
    openai/gpt-5
    google/gemini-2.5-flash
    google/gemini-2.5-pro

Tests per model:
  - LongMemEval-S k-curve at k = {3, 5, 8, 10} on 25 scorable items
  - Code-audit (raw codebase, Granite-winning state) on 15 planted bugs
  - Paper-audit (top-3 retrieval, Granite-winning state) on 30 SciFact claims

Output: ab_evidence/results/minimaltest_frontier_calibration/
  longmemeval_items/<qid>.json  — per-item: runs_by_k[k][model] = run record
  code_audit_items/<bug_id>.json — per-bug: runs[model] = run record
  paper_audit_items/<claim_id>.json — per-claim: runs[model] = run record

Cost estimate: ~$15 across all 8 models for full calibration.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
from code_review_bugs import BUGS, DISTRACTORS

_OUT = _HERE / "results" / "minimaltest_frontier_calibration"
(_OUT / "longmemeval_items").mkdir(parents=True, exist_ok=True)
(_OUT / "code_audit_items").mkdir(parents=True, exist_ok=True)
(_OUT / "paper_audit_items").mkdir(parents=True, exist_ok=True)

_HYBRID = _HERE / "results" / "minimaltest_hybrid" / "items"
_PA_ORIG = _HERE / "results" / "minimaltest_paper_audit" / "items"
DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"
SCIFACT = _HERE / "data" / "scifact" / "data"

FRONTIER_MODELS = [
    # Cheap tier
    "anthropic/claude-haiku-4.5",
    "openai/gpt-5-nano",
    "openai/gpt-4o-mini",
    "google/gemini-2.5-flash-lite",
    # Mid tier
    "anthropic/claude-sonnet-4.6",
    "openai/gpt-5",
    "google/gemini-2.5-flash",
    "google/gemini-2.5-pro",
]

K_VALUES = [3, 5, 8, 10]
PARALLELISM = 4

# Pricing (must match desi/answerer.py and routing_table.json)
PRICES = {
    "anthropic/claude-haiku-4.5": (1.00, 5.00),
    "anthropic/claude-sonnet-4.6": (3.00, 15.00),
    "openai/gpt-5-nano": (0.05, 0.40),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-5": (1.25, 10.00),
    "google/gemini-2.5-flash-lite": (0.10, 0.40),
    "google/gemini-2.5-flash": (0.30, 2.50),
    "google/gemini-2.5-pro": (1.25, 10.00),
}

ANSWER_SYSTEM = (
    "You are an assistant. Answer concisely based on the provided context. "
    "Be specific and direct. If a question asks 'find any bugs', name the function "
    "and describe the bug. If a question asks for SUPPORT/CONTRADICT/NEI, give "
    "exactly that verdict. Do NOT add a CONFIDENCE tag — answer cleanly."
)


def _http_post(url, headers, body, timeout=180, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:300]
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
         "X-Title": "DESi Frontier Calibration"}, body)
    lat = int((time.time() - t0) * 1000)
    if "_http_error" in d:
        return {"error": f"{d['_http_error']}: {d.get('_body','')[:200]}", "text": "", "latency_ms": lat}
    try:
        text = d["choices"][0]["message"]["content"] or ""
        u = d.get("usage", {}) or {}
        return {"text": text, "latency_ms": lat,
                "input_tokens": u.get("prompt_tokens"),
                "output_tokens": u.get("completion_tokens")}
    except Exception as e:
        return {"error": f"parse: {e}", "text": "", "latency_ms": lat}


_EMBED = None


def embed():
    global _EMBED
    if _EMBED is None:
        _EMBED = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED


# ---------------- LongMemEval k-curve ----------------

def session_text(sess):
    return "\n".join(f"{t.get('role','user').upper()}: {t.get('content','')}" for t in sess)


def conv_text(sessions, ids):
    parts = ["=== CONVERSATION EXCERPTS (chronological) ==="]
    for s, sid in zip(sessions, ids):
        parts.append(f"\n--- session {sid} ---")
        for t in s:
            parts.append(f"{t.get('role','user').upper()}: {t.get('content','')}")
    return "\n".join(parts)


def topk_chronological(item_raw, hybrid_item, k):
    per = hybrid_item["hybrid_extraction"]["per_session"]
    top_ids = [s["session_id"] for s in sorted(per, key=lambda x: -x["embedding_sim"])[:k]]
    sids = item_raw["haystack_session_ids"]
    idx_chrono = sorted(i for i, sid in enumerate(sids) if sid in top_ids)
    return ([item_raw["haystack_sessions"][i] for i in idx_chrono],
            [sids[i] for i in idx_chrono])


def run_lme_item(item_raw, hybrid_item):
    qid = item_raw["question_id"]
    out_path = _OUT / "longmemeval_items" / f"{qid}.json"
    if out_path.exists():
        rec = json.loads(out_path.read_text())
    else:
        rec = {"question_id": qid, "question_type": item_raw["question_type"],
               "question": item_raw["question"], "gold": item_raw["answer"],
               "runs_by_k": {}}
    gold = item_raw["answer"]
    for k in K_VALUES:
        kstr = str(k)
        if kstr not in rec["runs_by_k"]:
            sess, ids = topk_chronological(item_raw, hybrid_item, k)
            rec["runs_by_k"][kstr] = {"chosen_session_ids": ids, "runs": []}
        existing_models = {r["model"] for r in rec["runs_by_k"][kstr]["runs"]}
        sess, ids = topk_chronological(item_raw, hybrid_item, k)
        ctx = conv_text(sess, ids)
        user = f"{ctx}\n\n=== QUESTION ===\n{item_raw['question']}\n\nAnswer:"
        for model in FRONTIER_MODELS:
            if model in existing_models:
                continue
            r = call_or(model, ANSWER_SYSTEM, user, max_tokens=256)
            text = r.get("text", "") or ""
            score = 1.0 if gold.lower() in text.lower() else 0.0
            rec["runs_by_k"][kstr]["runs"].append({
                "model": model, "response_text": text[:500],
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "latency_ms": r.get("latency_ms"),
                "error": r.get("error"), "score": score,
            })
    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return qid


# ---------------- Code audit ----------------

def render_modules(modules):
    return "\n".join(f"# === {name} ===\n{src}" for name, src in modules)


CR_QUESTION = ("Audit the following Python code. Find any bugs, security issues, "
               "or subtle correctness problems. Name the function and explain what is wrong.")
CR_SYSTEM = (
    "You are a code reviewer. You will be shown a small Python codebase. "
    "Read it carefully. Identify any bug, security issue, or code smell. "
    "Be specific: name the function and explain the issue in 1-3 sentences. "
    "If you find no issue, say so explicitly."
)


def score_cr(text, must_contain, function_name):
    if not text:
        return 0.0
    t = text.lower()
    loc = function_name.lower() in t
    desc = any(m.lower() in t for m in must_contain)
    if loc and desc:
        return 1.0
    elif loc or desc:
        return 0.5
    return 0.0


def run_cr_item(bug):
    out_path = _OUT / "code_audit_items" / f"{bug['id']}.json"
    if out_path.exists():
        rec = json.loads(out_path.read_text())
    else:
        rec = {"bug_id": bug["id"], "bug_type": bug["bug_type"],
               "function": bug["function"], "must_contain": bug["must_contain"],
               "runs": []}
    modules = [(f"{bug['function']}.py", bug["buggy_source"])] + list(DISTRACTORS)
    user = f"{render_modules(modules)}\n\n=== TASK ===\n{CR_QUESTION}"
    existing = {r["model"] for r in rec["runs"]}
    for model in FRONTIER_MODELS:
        if model in existing:
            continue
        r = call_or(model, CR_SYSTEM, user, max_tokens=400)
        text = r.get("text", "") or ""
        score = score_cr(text, bug["must_contain"], bug["function"])
        rec["runs"].append({
            "model": model, "response_text": text[:500],
            "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"),
            "latency_ms": r.get("latency_ms"),
            "error": r.get("error"), "score": score,
        })
    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return bug["id"]


# ---------------- Paper audit ----------------

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


def run_pa_item(orig_item, corpus):
    out_path = _OUT / "paper_audit_items" / f"claim_{orig_item['claim_id']:04d}.json"
    if out_path.exists():
        rec = json.loads(out_path.read_text())
    else:
        rec = {"claim_id": orig_item["claim_id"],
               "claim_text": orig_item["claim_text"],
               "gold_label": orig_item["gold_label"], "runs": []}
    chosen_ids = orig_item["retrieval_chosen_ids"]
    abstracts = [corpus[did] for did in chosen_ids if did in corpus]
    user = ("=== ABSTRACTS ===\n\n" + "\n\n".join(render_abstract(d) for d in abstracts)
            + f"\n\n=== CLAIM ===\n{orig_item['claim_text']}\n\n"
            "Respond with VERDICT: SUPPORT | CONTRADICT | NEI on the first line, "
            "then brief reasoning.")
    gold = orig_item["gold_label"]
    existing = {r["model"] for r in rec["runs"]}
    for model in FRONTIER_MODELS:
        if model in existing:
            continue
        r = call_or(model, PA_SYSTEM, user, max_tokens=200)
        text = r.get("text", "") or ""
        v = parse_verdict(text)
        score = 1.0 if v == gold else 0.0
        rec["runs"].append({
            "model": model, "response_text": text[:500],
            "verdict": v, "score": score,
            "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"),
            "latency_ms": r.get("latency_ms"),
            "error": r.get("error"),
        })
    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return orig_item["claim_id"]


def main():
    print("=== Loading data ===", flush=True)
    data = json.loads(DATASET.read_text())
    by_qid = {it["question_id"]: it for it in data}
    hybrid = sorted(_HYBRID.glob("*.json"))
    hybrid_items = [json.loads(p.read_text()) for p in hybrid]
    # Filter scorable
    lme_pairs = []
    for h in hybrid_items:
        qid = h["question_id"]
        if qid not in by_qid:
            continue
        if by_qid[qid].get("question_type") == "single-session-preference":
            continue
        lme_pairs.append((by_qid[qid], h))
    print(f"  LongMemEval scorable items: {len(lme_pairs)}", flush=True)

    pa_items = [json.loads(p.read_text()) for p in sorted(_PA_ORIG.glob("*.json"))]
    print(f"  Paper-audit items: {len(pa_items)}", flush=True)
    corpus = {d["doc_id"]: d for d in (json.loads(l) for l in open(SCIFACT / "corpus.jsonl"))}
    print(f"  SciFact corpus: {len(corpus)} abstracts", flush=True)
    print(f"  Code-audit bugs: {len(BUGS)}", flush=True)
    print(f"  Frontier models to test: {len(FRONTIER_MODELS)}", flush=True)
    print(f"  Total calls estimate: {len(lme_pairs)*4*len(FRONTIER_MODELS) + len(BUGS)*len(FRONTIER_MODELS) + len(pa_items)*len(FRONTIER_MODELS)}", flush=True)

    embed().encode(["warmup"])

    # ---- LongMemEval k-curve ----
    print(f"\n=== LongMemEval k-curve: {len(lme_pairs)} items x {len(FRONTIER_MODELS)} models x 4 k = {len(lme_pairs)*len(FRONTIER_MODELS)*4} calls ===", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_lme_item, raw, h): raw["question_id"]
                for raw, h in lme_pairs}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                fut.result(); done += 1
                if done % 5 == 0 or done <= 2:
                    print(f"  LME [{done}/{len(lme_pairs)}] {qid}", flush=True)
            except Exception as e:
                print(f"  ERROR {qid}: {type(e).__name__}: {e}", flush=True)

    # ---- Code audit ----
    print(f"\n=== Code audit: {len(BUGS)} bugs x {len(FRONTIER_MODELS)} models = {len(BUGS)*len(FRONTIER_MODELS)} calls ===", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_cr_item, b): b["id"] for b in BUGS}
        for fut in as_completed(futs):
            bid = futs[fut]
            try:
                fut.result(); done += 1
                if done % 3 == 0:
                    print(f"  CR [{done}/{len(BUGS)}] {bid}", flush=True)
            except Exception as e:
                print(f"  ERROR {bid}: {type(e).__name__}: {e}", flush=True)

    # ---- Paper audit ----
    print(f"\n=== Paper audit: {len(pa_items)} claims x {len(FRONTIER_MODELS)} models = {len(pa_items)*len(FRONTIER_MODELS)} calls ===", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_pa_item, it, corpus): it["claim_id"] for it in pa_items}
        for fut in as_completed(futs):
            cid = futs[fut]
            try:
                fut.result(); done += 1
                if done % 5 == 0:
                    print(f"  PA [{done}/{len(pa_items)}] claim_{cid:04d}", flush=True)
            except Exception as e:
                print(f"  ERROR {cid}: {type(e).__name__}: {e}", flush=True)

    print("\nAll done.", flush=True)


if __name__ == "__main__":
    main()
