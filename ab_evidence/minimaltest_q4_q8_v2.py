"""Q4/Q8 × {raw, oracle, desi-llm, desi-embedding} — extended factor analysis.

Reuses the 30 sampled items from minimaltest_q4_q8 (seed 42 stratified).
Reuses the existing raw + oracle results from minimaltest_q4_q8/items/.

Adds two new state-extraction methods:
  - desi-llm: micro reads full conversation + question, outputs '- fact1\n- fact2\n...'
              State for the answerer is just the fact list (NOT the raw sessions).
  - desi-emb: top-k sessions by cosine similarity between question embedding and
              session embedding (all-MiniLM-L6-v2). k = len(answer_session_ids)
              so input size is matched to oracle.

Then runs 2 answerer models × 2 new state types = 4 new answerer conditions per item.

Scoring: substring match (case-insensitive).
"""
from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

_HERE = Path(__file__).resolve().parent
_PREV_ITEMS = _HERE / "results" / "minimaltest_q4_q8" / "items"
_OUT = _HERE / "results" / "minimaltest_q4_q8_v2"
_OUT.mkdir(parents=True, exist_ok=True)
_ITEMS_OUT = _OUT / "items"
_ITEMS_OUT.mkdir(parents=True, exist_ok=True)

DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"

MODELS = ["ibm-granite/granite-4.1-8b", "ibm-granite/granite-4.0-h-micro"]
EXTRACTOR_MODEL = "ibm-granite/granite-4.0-h-micro"  # Q4 extractor by design

N_PER_TYPE = 5
SEED = 42
PARALLELISM = 4

SYSTEM_ANSWER = ("You are an assistant who answers questions based on the provided "
                 "facts or conversation. Read carefully, then answer concisely. "
                 "If the answer isn't available, say so.")

SYSTEM_EXTRACT = ("You are a fact extractor. Read the conversation history and the question. "
                  "Output ONLY the facts from the conversation that are necessary to answer the "
                  "question.\n"
                  "- Format: one fact per line, prefixed with '- '\n"
                  "- Be terse and factual; no commentary\n"
                  "- Do NOT answer the question itself; just extract relevant facts\n"
                  "- If no relevant facts exist, output: '- No relevant facts found.'")


# ------------- prompt builders -------------

def conv_text(sessions, session_ids):
    parts = []
    for sess, sid in zip(sessions, session_ids):
        parts.append(f"\n--- session {sid} ---")
        for turn in sess:
            role = turn.get("role", "user").upper()
            parts.append(f"{role}: {turn.get('content','')}")
    return "\n".join(parts)


def session_text(sess):
    return "\n".join(f"{t.get('role','user').upper()}: {t.get('content','')}" for t in sess)


def build_extractor_user(item):
    full = conv_text(item["haystack_sessions"], item["haystack_session_ids"])
    return (f"=== CONVERSATION HISTORY ===\n{full}\n\n"
            f"=== QUESTION ===\n{item['question']}\n\n"
            f"Extract relevant facts now (one per line, prefixed with '- '):")


def build_answer_user_from_state(state_text, question):
    return (f"=== CONTEXT ===\n{state_text}\n\n"
            f"=== QUESTION ===\n{question}\n\nAnswer:")


def build_answer_user_from_conversation(sessions, session_ids, question):
    full = conv_text(sessions, session_ids)
    return (f"=== CONVERSATION HISTORY ===\n{full}\n\n"
            f"=== CURRENT QUESTION ===\n{question}")


# ------------- HTTP -------------

def _http_post(url, headers, body, timeout=240, retries=3):
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


def call_or(model, system, user, max_tokens=512):
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
         "X-Title": "DESi Q4Q8 v2"}, body)
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


def score_substring(text, gold):
    if not text:
        return 0.0
    return 1.0 if gold.lower() in text.lower() else 0.0


# ------------- DESi state extractors -------------

_EMBED_MODEL = None


def embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        print("  Loading all-MiniLM-L6-v2 ...", flush=True)
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED_MODEL


def extract_desi_emb(item, k=None):
    """Top-k sessions by embedding cosine similarity to the question."""
    em = embed_model()
    sessions = item["haystack_sessions"]
    session_ids = item["haystack_session_ids"]
    if k is None:
        k = len(item["answer_session_ids"])
    k = max(1, min(k, len(sessions)))
    sess_texts = [session_text(s) for s in sessions]
    q_emb = em.encode([item["question"]], normalize_embeddings=True)
    s_embs = em.encode(sess_texts, normalize_embeddings=True, batch_size=8, show_progress_bar=False)
    sims = (s_embs @ q_emb.T).ravel()
    top_idx = np.argsort(-sims)[:k].tolist()
    chosen_sessions = [sessions[i] for i in top_idx]
    chosen_ids = [session_ids[i] for i in top_idx]
    evidence = set(item["answer_session_ids"])
    recall = sum(1 for sid in chosen_ids if sid in evidence) / max(1, len(evidence))
    return {
        "k": k,
        "chosen_session_ids": chosen_ids,
        "similarity_scores": [float(sims[i]) for i in top_idx],
        "evidence_recall": float(recall),
        "context_text": conv_text(chosen_sessions, chosen_ids),
    }


def extract_desi_llm(item):
    """LLM-based fact extraction. Uses EXTRACTOR_MODEL (micro by default)."""
    user = build_extractor_user(item)
    r = call_or(EXTRACTOR_MODEL, SYSTEM_EXTRACT, user, max_tokens=512)
    facts = r.get("text", "") or ""
    return {
        "extractor_model": EXTRACTOR_MODEL,
        "facts_text": facts,
        "extractor_input_tokens": r.get("input_tokens"),
        "extractor_output_tokens": r.get("output_tokens"),
        "extractor_latency_ms": r.get("latency_ms"),
        "extractor_error": r.get("error"),
        "context_text": facts if facts else "- No facts extracted.",
    }


# ------------- per-item runner -------------

def run_item(item):
    qid = item["question_id"]
    out_path = _ITEMS_OUT / f"{qid}.json"
    if out_path.exists():
        return qid

    # Reuse prior raw/oracle/state results from the v1 minimaltest where possible
    prior = None
    prior_path = _PREV_ITEMS / f"{qid}.json"
    if prior_path.exists():
        prior = json.loads(prior_path.read_text())

    rec = {
        "question_id": qid,
        "question_type": item["question_type"],
        "question": item["question"],
        "gold_answer": item["answer"],
        "n_sessions": len(item["haystack_sessions"]),
        "n_evidence_sessions": len(item["answer_session_ids"]),
        "answer_session_ids": list(item["answer_session_ids"]),
        "extractions": {},
        "runs": [],
    }

    # Reuse raw + oracle (variant="raw" and "state" in v1)
    if prior:
        for r in prior["runs"]:
            v = r.get("variant")
            # v1 named state-types as "raw" and "state" (= oracle)
            mapped_state = "raw" if v == "raw" else "oracle"
            rec["runs"].append({**r, "state_type": mapped_state})

    # Extract DESi-LLM state
    desi_llm = extract_desi_llm(item)
    rec["extractions"]["desi_llm"] = {k: v for k, v in desi_llm.items() if k != "context_text"}

    # Extract DESi-Embedding state
    desi_emb = extract_desi_emb(item)
    rec["extractions"]["desi_emb"] = {k: v for k, v in desi_emb.items() if k != "context_text"}

    # Run answerers on the two new state types
    for state_type, state_ctx in [("desi_llm", desi_llm["context_text"]),
                                   ("desi_emb", desi_emb["context_text"])]:
        if state_type == "desi_llm":
            user = build_answer_user_from_state(state_ctx, item["question"])
        else:  # desi_emb: state_ctx is already the conv_text of chosen sessions
            user = (f"=== CONVERSATION HISTORY ===\n{state_ctx}\n\n"
                    f"=== CURRENT QUESTION ===\n{item['question']}")
        for model in MODELS:
            r = call_or(model, SYSTEM_ANSWER, user, max_tokens=256)
            rec["runs"].append({
                "model": model,
                "state_type": state_type,
                "variant": state_type,
                "response_text": r.get("text", ""),
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "latency_ms": r.get("latency_ms"),
                "error": r.get("error"),
                "score": score_substring(r.get("text", ""), item["answer"]),
                "context_len_chars": len(user),
            })

    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return qid


# ------------- main -------------

def sample_stratified(data, n_per_type=5, seed=42):
    by_type = defaultdict(list)
    for it in data:
        by_type[it["question_type"]].append(it)
    rng = random.Random(seed)
    out = []
    for qt in sorted(by_type):
        out.extend(rng.sample(by_type[qt], min(n_per_type, len(by_type[qt]))))
    return out


def main():
    print(f"Loading {DATASET}", flush=True)
    data = json.loads(DATASET.read_text())
    sampled = sample_stratified(data, N_PER_TYPE, SEED)
    print(f"Sampled {len(sampled)} items (stratified, seed={SEED})", flush=True)

    # Warm up embedding model so the first parallel worker doesn't all race to load
    embed_model().encode(["warmup"])

    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_item, it): it["question_id"] for it in sampled}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                fut.result()
                done += 1
                if done % 3 == 0 or done <= 2:
                    print(f"  [{done}/{len(sampled)}] {qid}", flush=True)
            except Exception as e:
                print(f"  ERROR {qid}: {type(e).__name__}: {e}", flush=True)
    print(f"\nDone. {done}/{len(sampled)} items written.", flush=True)


if __name__ == "__main__":
    main()
