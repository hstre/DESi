"""Retrieval baselines R1/R2/R3 over the SAME source material the full-chat baseline (A) sees.

These answer "does DESi beat plain retrieval, or behave like ordinary top-k context selection?".
Each retriever chunks the chat into sentences, scores them against the follow-up query, and greedily
packs the top chunks into a context block sized to ≈ B's token budget. The block carries NO DESi
governance metadata — just retrieved text — so this isolates *selection* from *epistemic structure*.

  R1 — BM25 (Okapi) top-k          : the standard sparse lexical retriever.
  R2 — TF-IDF cosine top-k         : a classical VECTOR-SPACE retriever. NOTE: a NEURAL embedder is
                                     not available in this environment (no sentence-transformers /
                                     fastembed / numpy), so this is an embedding-FREE vector baseline;
                                     a dense-embedding R2 is a documented follow-up, not run here.
  R3 — hybrid (RRF of R1+R2)       : reciprocal-rank fusion of the two, cheap.

All pure-Python and deterministic (fixed tokeniser, stable sort). No new dependency.
"""
from __future__ import annotations

import math
import re

from _tok import token_count
from build_state import load_chat
from follow_up_tasks import FOLLOW_UPS

RETRIEVAL = ("R1_bm25", "R2_tfidf", "R3_hybrid")

_SYSTEM_BASE = (
    "You are continuing prior work. Answer the user's question using ONLY the context you have. "
    "Do not invent facts. If a category has no entries, write 'none'."
)
_SYSTEM_R_EXTRA = (" The original chat is NOT included in full. Below the question are the most "
                   "relevant excerpts retrieved from it.")

_STOP = frozenset((
    "the a an of to in on and or is are was were be been being that this these those it its as at "
    "by for with from has have had do does did but if then than so such into out up down over under "
    "about their they them we you i which who not no only any all per also more most some can").split())


def _toks(s: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", (s or "").lower())
            if t not in _STOP and len(t) > 2]


def _chunks(case_id: str) -> list[str]:
    """Sentence-level chunks across all chat turns (the retrievable corpus = the chat A sees)."""
    out: list[str] = []
    for turn in load_chat(case_id):
        for s in re.split(r"(?<=[.!?])\s+", (turn.get("content") or "").strip()):
            s = s.strip()
            if len(s) > 15:
                out.append(s)
    return out


def _bm25_scores(chunks, query, *, k1=1.5, b=0.75):
    docs = [_toks(c) for c in chunks]
    n = len(docs)
    avgdl = sum(len(d) for d in docs) / n if n else 0.0
    df: dict[str, int] = {}
    for d in docs:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    q = _toks(query)
    scores = []
    for d in docs:
        tf: dict[str, int] = {}
        for t in d:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        for t in q:
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * (tf[t] * (k1 + 1)) / (tf[t] + k1 * (1 - b + b * (len(d) / avgdl if avgdl else 0)))
        scores.append(s)
    return scores


def _tfidf_cosine_scores(chunks, query):
    docs = [_toks(c) for c in chunks]
    n = len(docs)
    df: dict[str, int] = {}
    for d in docs:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}

    def vec(tokens):
        tf: dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0.0) + 1.0
        return {t: (f / len(tokens)) * idf.get(t, 0.0) for t, f in tf.items()} if tokens else {}

    qv = vec(_toks(query))
    qn = math.sqrt(sum(v * v for v in qv.values())) or 1.0
    scores = []
    for d in docs:
        dv = vec(d)
        dot = sum(dv.get(t, 0.0) * qv.get(t, 0.0) for t in qv)
        dn = math.sqrt(sum(v * v for v in dv.values())) or 1.0
        scores.append(dot / (dn * qn))
    return scores


_EMBEDDER = None


def _embedder():
    """Lazy, fail-closed neural embedder (fastembed BAAI/bge-small-en-v1.5). None if unavailable."""
    global _EMBEDDER
    if _EMBEDDER is None:
        try:
            from fastembed import TextEmbedding
            _EMBEDDER = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except Exception:  # noqa: BLE001 - no embedder installed -> R2n simply unavailable
            _EMBEDDER = False
    return _EMBEDDER or None


def neural_available() -> bool:
    return _embedder() is not None


def _neural_scores(chunks, query):
    emb = _embedder()
    vecs = [[float(x) for x in v] for v in emb.embed(list(chunks) + [query])]
    q = vecs[-1]
    qn = math.sqrt(sum(x * x for x in q)) or 1.0
    out = []
    for v in vecs[:-1]:
        dot = sum(a * b for a, b in zip(v, q, strict=False))
        vn = math.sqrt(sum(a * a for a in v)) or 1.0
        out.append(dot / (vn * qn))
    return out


def _rank(scores):
    # indices sorted by score desc, ties broken by original order (stable, deterministic)
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))


def _select_to_budget(case_id: str, ranked: list[int], chunks: list[str], target: int) -> str:
    follow = FOLLOW_UPS[case_id]
    base = token_count(_SYSTEM_BASE + _SYSTEM_R_EXTRA) + token_count(follow) + 8
    picked: list[int] = []
    used = base
    for i in ranked:
        c_tok = token_count(chunks[i]) + 2
        if used + c_tok > target and picked:
            break
        picked.append(i)
        used += c_tok
    picked.sort()                                   # present excerpts in original chat order
    block = "\n".join(f"- {chunks[i]}" for i in picked)
    return f"{follow}\n\n---\nRetrieved excerpts:\n{block}\n---"


def build_retrieval(case_id: str, method: str, *, target_tokens: int) -> dict:
    chunks = _chunks(case_id)
    query = FOLLOW_UPS[case_id]
    if method == "R1_bm25":
        ranked = _rank(_bm25_scores(chunks, query))
    elif method == "R2_tfidf":
        ranked = _rank(_tfidf_cosine_scores(chunks, query))
    elif method == "R2n_neural":
        ranked = _rank(_neural_scores(chunks, query))
    elif method == "R3_hybrid":
        r1 = {i: r for r, i in enumerate(_rank(_bm25_scores(chunks, query)))}
        r2 = {i: r for r, i in enumerate(_rank(_tfidf_cosine_scores(chunks, query)))}
        rrf = [1.0 / (60 + r1[i]) + 1.0 / (60 + r2[i]) for i in range(len(chunks))]
        ranked = _rank(rrf)
    else:
        raise ValueError(method)
    user = _select_to_budget(case_id, ranked, chunks, target_tokens)
    payload = {"condition": method, "system": _SYSTEM_BASE + _SYSTEM_R_EXTRA,
               "messages": [{"role": "user", "content": user}], "slice_source": "chat_retrieval",
               "case_id": case_id, "n_messages": 1}
    payload["input_token_estimate"] = (token_count(payload["system"])
                                       + token_count(user))
    return payload
