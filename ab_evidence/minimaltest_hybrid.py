"""Hybrid evidence-grounded extractor.

Tests: Q4 + evidence-grounded hybrid state >= Q8 + Raw?

Pipeline:
  1. Embedding top-10 retrieval (vs prior k=#evidence) — addresses k=1 recall problem
  2. Per-session LLM verification: for each of the 10 candidate sessions, micro extracts
     evidence cards. Each card has {claim, quote, session_id, confidence}.
  3. Anti-hallucination: validate that quote is a verbatim substring of the session text.
     Discard cards with non-verbatim quotes.
  4. Order cards by session index in original conversation (oldest -> newest), so the
     answerer can reason about temporal supersession.
  5. Q4 answerer sees the validated, ordered cards and answers.

Same 30 stratified LongMemEval items as v1/v2 (seed=42).
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
_OUT = _HERE / "results" / "minimaltest_hybrid"
_ITEMS_OUT = _OUT / "items"
_ITEMS_OUT.mkdir(parents=True, exist_ok=True)
DATASET = _HERE / "data" / "longmemeval" / "longmemeval_s_cleaned.json"

ANSWERER_MODELS = ["ibm-granite/granite-4.1-8b", "ibm-granite/granite-4.0-h-micro"]
EXTRACTOR_MODEL = "ibm-granite/granite-4.0-h-micro"

N_PER_TYPE = 5
SEED = 42
PARALLELISM = 4
TOP_K = 10  # candidate sessions per item
MAX_CARDS_PER_SESSION = 4

SYSTEM_EXTRACT = (
    "You extract verifiable evidence from a single conversation session.\n\n"
    "Given a QUESTION and ONE conversation session, output evidence cards that are\n"
    "directly relevant to answering the question.\n\n"
    "Each card MUST have:\n"
    "- \"claim\": a short factual statement (1 sentence)\n"
    "- \"quote\": an EXACT verbatim substring from the session (5 to 250 characters)\n\n"
    "Rules:\n"
    "- Be conservative. If unsure whether the session contains relevant evidence, output [].\n"
    "- DO NOT invent quotes. Quotes must literally appear in the session text.\n"
    "- DO NOT paraphrase.\n"
    "- DO NOT answer the question.\n"
    "- Maximum 4 cards per session.\n\n"
    "Output ONLY a JSON array, no commentary. Example:\n"
    '[{"claim":"User has 3 dogs","quote":"I currently own three dogs named Rex, Buddy, and Spot"}]\n'
    "If no relevant evidence: []"
)

SYSTEM_ANSWER = (
    "You answer a question using a list of evidence cards extracted from a conversation.\n"
    "Cards are listed in CHRONOLOGICAL ORDER (oldest first, newest last).\n"
    "When cards conflict, the LATER card typically reflects an update; trust the most recent.\n"
    "Answer concisely. If the evidence does not contain the answer, say so."
)


# ------------- HTTP -------------

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
         "X-Title": "DESi Hybrid Extractor"}, body)
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


# ------------- Embedding -------------

_EMBED_MODEL = None


def embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        print("  Loading all-MiniLM-L6-v2 ...", flush=True)
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED_MODEL


def session_text(sess):
    return "\n".join(f"{t.get('role','user').upper()}: {t.get('content','')}" for t in sess)


def top_k_sessions(item, k=TOP_K):
    em = embed_model()
    sessions = item["haystack_sessions"]
    session_ids = item["haystack_session_ids"]
    if len(sessions) <= k:
        chosen = list(range(len(sessions)))
        sims = [1.0] * len(sessions)
        return chosen, sims
    sess_texts = [session_text(s) for s in sessions]
    q_emb = em.encode([item["question"]], normalize_embeddings=True)
    s_embs = em.encode(sess_texts, normalize_embeddings=True, batch_size=16, show_progress_bar=False)
    sims = (s_embs @ q_emb.T).ravel()
    idx = np.argsort(-sims)[:k].tolist()
    # Sort by ORIGINAL conversation order (oldest first), to preserve chronology
    idx_chrono = sorted(idx, key=lambda i: i)
    return idx_chrono, [float(sims[i]) for i in idx_chrono]


# ------------- Extractor: per-session evidence cards -------------

_JSON_RE = re.compile(r"\[.*\]", re.DOTALL)


def parse_cards(text):
    """Tolerant JSON parser: find first [...] block, parse, drop malformed entries."""
    if not text:
        return []
    m = _JSON_RE.search(text)
    if not m:
        return []
    try:
        arr = json.loads(m.group(0))
        if not isinstance(arr, list):
            return []
        out = []
        for entry in arr:
            if isinstance(entry, dict) and "claim" in entry and "quote" in entry:
                out.append({"claim": str(entry["claim"]),
                            "quote": str(entry["quote"])})
        return out
    except Exception:
        return []


def validate_card(card, session_str):
    """Anti-hallucination: quote must be a verbatim substring of the session.
    Allow minor whitespace normalization."""
    quote = card.get("quote", "").strip()
    if len(quote) < 5:
        return False
    # exact substring
    if quote in session_str:
        return True
    # whitespace-normalized check
    qn = re.sub(r"\s+", " ", quote)
    sn = re.sub(r"\s+", " ", session_str)
    return qn in sn


def extract_evidence_per_session(item, session_idx):
    sess = item["haystack_sessions"][session_idx]
    sid = item["haystack_session_ids"][session_idx]
    sess_str = session_text(sess)
    user = (f"QUESTION: {item['question']}\n\n"
            f"SESSION ID: {sid}\n"
            f"SESSION:\n{sess_str}\n\n"
            f"Output JSON array of evidence cards (max 4):")
    r = call_or(EXTRACTOR_MODEL, SYSTEM_EXTRACT, user, max_tokens=400)
    text = r.get("text", "") or ""
    raw_cards = parse_cards(text)
    validated = []
    rejected = []
    for c in raw_cards[:MAX_CARDS_PER_SESSION]:
        if validate_card(c, sess_str):
            c["session_id"] = sid
            c["session_idx"] = session_idx
            validated.append(c)
        else:
            rejected.append(c)
    return {
        "session_id": sid,
        "session_idx": session_idx,
        "raw_output": text[:500],
        "cards_extracted": len(raw_cards),
        "cards_validated": len(validated),
        "cards_rejected_for_hallucination": len(rejected),
        "validated_cards": validated,
        "input_tokens": r.get("input_tokens"),
        "output_tokens": r.get("output_tokens"),
        "latency_ms": r.get("latency_ms"),
        "error": r.get("error"),
    }


def build_hybrid_state(item):
    """Full hybrid extraction: embed top-10, per-session extract, validate, order chronologically."""
    chosen_idx, sims = top_k_sessions(item, TOP_K)
    per_session = []
    all_cards = []
    for i, sidx in enumerate(chosen_idx):
        res = extract_evidence_per_session(item, sidx)
        res["embedding_sim"] = sims[i]
        per_session.append(res)
        all_cards.extend(res["validated_cards"])
    # Already in chronological order because chosen_idx is sorted
    # Build context text for answerer
    if not all_cards:
        context = "(No relevant evidence cards extracted.)"
    else:
        parts = ["EVIDENCE CARDS (chronological, oldest first):"]
        for c in all_cards:
            parts.append(f"- [session {c['session_id']}] Claim: {c['claim']}")
            parts.append(f"  Quote: \"{c['quote'][:200]}\"")
        context = "\n".join(parts)
    return {
        "chosen_session_ids": [item["haystack_session_ids"][i] for i in chosen_idx],
        "evidence_recall": sum(1 for sid in [item["haystack_session_ids"][i] for i in chosen_idx]
                               if sid in set(item["answer_session_ids"])) / max(1, len(item["answer_session_ids"])),
        "per_session": per_session,
        "n_cards_total": len(all_cards),
        "context_text": context,
    }


# ------------- runner -------------

def run_item(item):
    qid = item["question_id"]
    out_path = _ITEMS_OUT / f"{qid}.json"
    if out_path.exists():
        return qid

    hybrid = build_hybrid_state(item)

    rec = {
        "question_id": qid,
        "question_type": item["question_type"],
        "question": item["question"],
        "gold_answer": item["answer"],
        "n_sessions": len(item["haystack_sessions"]),
        "n_evidence_sessions": len(item["answer_session_ids"]),
        "answer_session_ids": list(item["answer_session_ids"]),
        "hybrid_extraction": {k: v for k, v in hybrid.items() if k != "context_text"},
        "runs": [],
    }

    user = (f"=== {hybrid['context_text']}\n\n"
            f"=== QUESTION ===\n{item['question']}\n\nAnswer:")

    for model in ANSWERER_MODELS:
        r = call_or(model, SYSTEM_ANSWER, user, max_tokens=256)
        gold = item["answer"]
        score = 1.0 if (r.get("text", "") or "").lower().find(gold.lower()) >= 0 else 0.0
        rec["runs"].append({
            "model": model,
            "state_type": "hybrid",
            "response_text": r.get("text", ""),
            "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"),
            "latency_ms": r.get("latency_ms"),
            "error": r.get("error"),
            "score": score,
            "context_len_chars": len(user),
        })

    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return qid


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
    print(f"Sampled {len(sampled)} items", flush=True)
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
    print(f"\nDone. {done}/{len(sampled)} items.", flush=True)


if __name__ == "__main__":
    main()
