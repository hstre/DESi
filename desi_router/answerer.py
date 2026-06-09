"""DESi answerer — runs the routed model and extracts self-confidence.

Wraps a single LLM call so the pipeline can:
  1. Call the model with the chosen (model, k, strategy)
  2. Ask it to suffix with [CONFIDENCE: high/medium/low]
  3. Return answer + parsed confidence so the pipeline can escalate
     when confidence is 'low'.

This is intentionally minimal — it doesn't read logprobs (most OpenRouter
providers don't expose them); it relies on the model's self-report. That's
known-noisy but cheap and universal.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Literal


Confidence = Literal["high", "medium", "low", "unknown"]


_BASE_SYSTEM = (
    "You are an assistant. Answer concisely based on the provided context. "
    "Be specific and direct. If a question asks 'find any bugs', name the function "
    "and describe the bug. If a question asks for SUPPORT/CONTRADICT/NEI, give "
    "exactly that verdict. Do NOT add a CONFIDENCE tag — answer cleanly."
)


@dataclass
class Answer:
    text: str
    confidence: Confidence
    confidence_raw: str  # the matched substring, for audit
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    cost_usd: float
    error: str | None = None


_CONF_RE = re.compile(r"\[CONFIDENCE:\s*(high|medium|low)\s*\]", re.IGNORECASE)

# Heuristic confidence detection: scan response for refusal / hedging markers.
_LOW_CONF_MARKERS = [
    r"\bi don't (?:have|know)\b",
    r"\bi cannot (?:determine|tell|find)\b",
    r"\bno (?:relevant|specific) (?:facts?|information|bugs?|issues?) (?:found|in)\b",
    r"\bunable to (?:determine|verify|find)\b",
    r"\binsufficient (?:information|context|evidence)\b",
    r"\bnot enough (?:information|context|evidence)\b",
    r"\bdo(?:es)? not (?:contain|provide|specify|mention)\b",
    r"\bappears? to be (?:correct|fine|free of (?:bugs?|issues?))\b",
    r"\bno apparent (?:bugs?|issues?|problems?)\b",
    r"\bcould you (?:provide|clarify|specify)\b",  # asking for more info instead of answering
    r"\bdon't have (?:access|enough)\b",
    r"\b\(empty\)\b",
]
_LOW_CONF_RE = re.compile("|".join(_LOW_CONF_MARKERS), re.IGNORECASE)


def _heuristic_confidence(text: str) -> Confidence:
    """Derive confidence from response heuristics when no [CONFIDENCE:] tag present."""
    if not text or len(text.strip()) < 10:
        return "low"
    if _LOW_CONF_RE.search(text):
        return "low"
    # Hedging markers indicate medium
    if re.search(r"\b(?:might be|possibly|perhaps|may not|seems to|appears)\b",
                 text, re.IGNORECASE):
        return "medium"
    return "high"


def _http_post(url, headers, body, timeout=180, retries=2):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:200]
            if e.code in (400, 401, 403, 404):
                return {"_http_error": e.code, "_body": text}
            last = f"HTTP {e.code}: {text}"
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        time.sleep(2 ** i)
    return {"_http_error": "retry_exhausted", "_body": last}


# Pricing per model — keep in sync with routing_table.json
# (price_in_per_M_tokens, price_out_per_M_tokens) in USD
_PRICES = {
    # Measured (in tasks.<task>.cells)
    "ibm-granite/granite-4.0-h-micro": (0.017, 0.112),
    "ibm-granite/granite-4.1-8b": (0.05, 0.10),
    "meta-llama/llama-3.2-3b-instruct": (0.051, 0.335),
    "meta-llama/llama-3.1-8b-instruct": (0.020, 0.050),
    "qwen/qwen-2.5-7b-instruct": (0.040, 0.100),
    "mistralai/ministral-3b-2512": (0.100, 0.100),
    # Provisional frontier-tier (pricing real, scores not yet measured)
    "anthropic/claude-haiku-4.5": (1.00, 5.00),
    "anthropic/claude-sonnet-4.6": (3.00, 15.00),
    "anthropic/claude-opus-4.8": (5.00, 25.00),
    "openai/gpt-5-nano": (0.05, 0.40),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-5": (1.25, 10.00),
    "openai/gpt-5-pro": (15.00, 120.00),
    "google/gemini-2.5-flash-lite": (0.10, 0.40),
    "google/gemini-2.5-flash": (0.30, 2.50),
    "google/gemini-2.5-pro": (1.25, 10.00),
    "deepseek/deepseek-v4-flash": (0.098, 0.197),
    "deepseek/deepseek-v4-pro": (0.435, 0.870),
    "deepseek/deepseek-v3.2": (0.229, 0.343),
    "deepseek/deepseek-chat-v3.1": (0.210, 0.790),
    "deepseek/deepseek-chat-v3-0324": (0.200, 0.770),
}


def answer(model: str, context_block: str, question: str,
           extra_system: str | None = None, max_tokens: int = 256) -> Answer:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return Answer(text="", confidence="unknown", confidence_raw="",
                      model=model, input_tokens=None, output_tokens=None,
                      latency_ms=0, cost_usd=0.0, error="no OPENROUTER_API_KEY")
    system = _BASE_SYSTEM if not extra_system else f"{_BASE_SYSTEM}\n\n{extra_system}"
    user = f"{context_block}\n\n=== QUESTION ===\n{question}\n\nAnswer:"
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
         "X-Title": "DESi Answerer"}, body)
    lat = int((time.time() - t0) * 1000)
    if "_http_error" in d:
        return Answer(text="", confidence="unknown", confidence_raw="",
                      model=model, input_tokens=None, output_tokens=None,
                      latency_ms=lat, cost_usd=0.0,
                      error=f"{d['_http_error']}: {d.get('_body','')[:200]}")
    try:
        text = d["choices"][0]["message"]["content"] or ""
        u = d.get("usage", {}) or {}
        in_t = u.get("prompt_tokens", 0) or 0
        out_t = u.get("completion_tokens", 0) or 0
        in_p, out_p = _PRICES.get(model, (0.05, 0.10))
        cost = in_t / 1e6 * in_p + out_t / 1e6 * out_p
        # Prefer explicit tag if the model emitted one; otherwise heuristic
        m = _CONF_RE.search(text)
        if m:
            conf: Confidence = m.group(1).lower()  # type: ignore
            conf_raw = m.group(0)
        else:
            conf = _heuristic_confidence(text)
            conf_raw = "(heuristic)"
        return Answer(
            text=text, confidence=conf,
            confidence_raw=conf_raw,
            model=model, input_tokens=in_t, output_tokens=out_t,
            latency_ms=lat, cost_usd=cost,
        )
    except Exception as e:
        return Answer(text="", confidence="unknown", confidence_raw="",
                      model=model, input_tokens=None, output_tokens=None,
                      latency_ms=lat, cost_usd=0.0, error=f"parse: {e}")
