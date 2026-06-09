"""Paper-Audit Minimaltest using SciFact.

30 stratified scientific claims (10 SUPPORT, 10 CONTRADICT, 10 NEI).

For each claim:
  - Build haystack: cited abstract + 8 distractor abstracts (random from corpus)
  - 3 state types × 2 models = 6 conditions:
    - raw: all 9 abstracts
    - oracle: only cited abstract
    - retrieval: embedding top-3 by claim similarity
  - Question: classify the claim as SUPPORT / CONTRADICT / NEI relative to the abstracts
  - Score: 1.0 if correctly classified, 0.0 otherwise (strict 3-way)

This tests the "scattered scientific evidence" pattern with a known benchmark,
larger haystack (~2000 tokens average) than the code-review test, and
question specificity (the claim text is very specific).
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
_OUT = _HERE / "results" / "minimaltest_paper_audit"
_ITEMS_OUT = _OUT / "items"
_ITEMS_OUT.mkdir(parents=True, exist_ok=True)
SCIFACT = _HERE / "data" / "scifact" / "data"

MODELS = ["ibm-granite/granite-4.1-8b", "ibm-granite/granite-4.0-h-micro"]
PARALLELISM = 4
N_PER_LABEL = 10
N_DISTRACTORS = 8
SEED = 42

SYSTEM = (
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
    "Then you may explain in 1-2 sentences which abstract(s) support your verdict and why."
)


def load_scifact():
    claims = [json.loads(l) for l in open(SCIFACT / "claims_train.jsonl")]
    corpus = {d["doc_id"]: d for d in (json.loads(l) for l in open(SCIFACT / "corpus.jsonl"))}
    return claims, corpus


def claim_label(claim, corpus):
    """Resolve the gold label for a claim. Returns (label, cited_doc_id, evidence_sentences)."""
    cited = claim["cited_doc_ids"]
    if not cited:
        return None, None, None
    cited_id = cited[0]
    if cited_id not in corpus:
        return None, None, None
    if not claim["evidence"]:
        return "NEI", cited_id, []
    ev = claim["evidence"].get(str(cited_id), [])
    if not ev:
        return "NEI", cited_id, []
    labels = {e["label"] for e in ev}
    if "SUPPORT" in labels:
        label = "SUPPORT"
    elif "CONTRADICT" in labels:
        label = "CONTRADICT"
    else:
        return None, None, None
    sentences = []
    for e in ev:
        sentences.extend(e.get("sentences", []))
    return label, cited_id, sentences


def sample_stratified(claims, corpus, n_per_label, seed):
    rng = random.Random(seed)
    by_label = defaultdict(list)
    for c in claims:
        label, cited_id, ev_sents = claim_label(c, corpus)
        if label is None:
            continue
        by_label[label].append((c, cited_id, ev_sents))
    out = []
    for label in ("SUPPORT", "CONTRADICT", "NEI"):
        pool = by_label[label]
        chosen = rng.sample(pool, min(n_per_label, len(pool)))
        for c, cited_id, ev_sents in chosen:
            out.append({"claim_obj": c, "label": label, "cited_doc_id": cited_id,
                        "evidence_sentences": ev_sents})
    rng.shuffle(out)
    return out


def render_abstract(doc):
    sents = doc.get("abstract") or []
    if isinstance(sents, list):
        body = " ".join(sents)
    else:
        body = sents
    return f"[doc_id {doc['doc_id']}] Title: {doc.get('title','(no title)')}\nAbstract: {body}"


def build_user(claim_text, abstracts):
    parts = []
    for d in abstracts:
        parts.append(render_abstract(d))
    return ("=== ABSTRACTS ===\n\n" + "\n\n".join(parts)
            + f"\n\n=== CLAIM ===\n{claim_text}\n\n"
            "Respond with VERDICT: SUPPORT | CONTRADICT | NEI on the first line, "
            "then brief reasoning.")


_VERDICT_RE = re.compile(r"VERDICT:\s*(SUPPORT|CONTRADICT|NEI)", re.IGNORECASE)


def parse_verdict(text):
    if not text:
        return None
    m = _VERDICT_RE.search(text)
    if not m:
        # Fallback heuristic: first occurrence of one of the labels
        for label in ("CONTRADICT", "SUPPORT", "NEI"):
            if re.search(rf"\b{label}\b", text, re.IGNORECASE):
                return label.upper()
        return None
    return m.group(1).upper()


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


def call_or(model, system, user, max_tokens=200):
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
         "X-Title": "DESi PaperAudit"}, body)
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


_EMBED_MODEL = None


def embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED_MODEL


def topk_abstracts(claim_text, abstracts, k=3):
    em = embed_model()
    texts = [d.get("title", "") + " " + " ".join(d.get("abstract") or []) for d in abstracts]
    q = em.encode([claim_text], normalize_embeddings=True)
    es = em.encode(texts, normalize_embeddings=True, batch_size=8, show_progress_bar=False)
    sims = (es @ q.T).ravel()
    idx = np.argsort(-sims)[:k].tolist()
    return [abstracts[i] for i in idx], [float(sims[i]) for i in idx]


def run_one(sampled_item, corpus, all_doc_ids, idx):
    out_path = _ITEMS_OUT / f"claim_{idx:03d}.json"
    if out_path.exists():
        return idx

    claim = sampled_item["claim_obj"]
    label = sampled_item["label"]
    cited_id = sampled_item["cited_doc_id"]

    # Build haystack: cited + N_DISTRACTORS random distractors
    rng = random.Random(SEED + idx)
    other_ids = [did for did in all_doc_ids if did != cited_id]
    distractors = rng.sample(other_ids, N_DISTRACTORS)
    haystack_ids = [cited_id] + distractors
    rng.shuffle(haystack_ids)
    abstracts = [corpus[did] for did in haystack_ids if did in corpus]

    # Build user prompts
    user_raw = build_user(claim["claim"], abstracts)
    user_oracle = build_user(claim["claim"], [corpus[cited_id]])
    chosen, sims = topk_abstracts(claim["claim"], abstracts, k=3)
    chosen_ids = [d["doc_id"] for d in chosen]
    user_retr = build_user(claim["claim"], chosen)
    retrieval_recall = 1.0 if cited_id in chosen_ids else 0.0

    rec = {
        "claim_id": claim["id"],
        "claim_text": claim["claim"],
        "gold_label": label,
        "cited_doc_id": cited_id,
        "haystack_doc_ids": haystack_ids,
        "retrieval_chosen_ids": chosen_ids,
        "retrieval_sims": sims,
        "retrieval_recall": retrieval_recall,
        "runs": [],
    }

    for state_type, user in [("raw", user_raw), ("oracle", user_oracle), ("retrieval", user_retr)]:
        for model in MODELS:
            r = call_or(model, SYSTEM, user, max_tokens=200)
            text = r.get("text", "") or ""
            verdict = parse_verdict(text)
            score = 1.0 if verdict == label else 0.0
            rec["runs"].append({
                "model": model,
                "state_type": state_type,
                "response_text": text,
                "verdict": verdict,
                "score": score,
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "latency_ms": r.get("latency_ms"),
                "error": r.get("error"),
            })

    out_path.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return idx


def main():
    print("Loading SciFact...", flush=True)
    claims, corpus = load_scifact()
    print(f"  {len(claims)} claims, {len(corpus)} corpus abstracts", flush=True)
    sampled = sample_stratified(claims, corpus, N_PER_LABEL, SEED)
    print(f"  Sampled {len(sampled)} stratified claims (seed={SEED})", flush=True)
    by_label = defaultdict(int)
    for s in sampled:
        by_label[s["label"]] += 1
    for label, n in sorted(by_label.items()):
        print(f"    {label}: {n}", flush=True)

    all_doc_ids = list(corpus.keys())
    embed_model().encode(["warmup"])

    done = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as ex:
        futs = {ex.submit(run_one, s, corpus, all_doc_ids, i): i for i, s in enumerate(sampled)}
        for fut in as_completed(futs):
            idx = futs[fut]
            try:
                fut.result()
                done += 1
                if done % 3 == 0 or done <= 2:
                    print(f"  [{done}/{len(sampled)}] claim_{idx:03d}", flush=True)
            except Exception as e:
                print(f"  ERROR claim_{idx:03d}: {type(e).__name__}: {e}", flush=True)
    print(f"\nDone. {done}/{len(sampled)}", flush=True)


if __name__ == "__main__":
    main()
