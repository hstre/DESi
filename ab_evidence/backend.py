"""Claude-backend adapter.

Three modes, in priority order:
  1. ANTHROPIC native (ANTHROPIC_API_KEY)            — direct /v1/messages
  2. OpenRouter (OPENROUTER_API_KEY)                  — proxied chat-completions
  3. UNAVAILABLE                                      — documented status, no simulation

If/when this runs with a real key, ALL four primary metrics get measured from real outputs.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_MODEL_ANTHROPIC = "claude-opus-4-7"
DEFAULT_MODEL_OPENROUTER = "anthropic/claude-sonnet-4.5"
DEFAULT_MAX_TOKENS = 2048


def is_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY")) or bool(os.environ.get("OPENROUTER_API_KEY"))


def backend_label() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic_native"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    return "unavailable"


def _call_anthropic(system, messages, model, max_tokens):
    api_key = os.environ["ANTHROPIC_API_KEY"]
    url = (os.environ.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/") \
          + "/v1/messages"
    body = json.dumps({"model": model, "max_tokens": max_tokens, "system": system,
                       "messages": messages}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    latency_ms = int((time.time() - t0) * 1000)
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return {"text": text, "latency_ms": latency_ms, "backend": "anthropic_native",
            "model": model,
            "input_tokens": data.get("usage", {}).get("input_tokens"),
            "output_tokens": data.get("usage", {}).get("output_tokens"),
            "stop_reason": data.get("stop_reason")}


def _call_openrouter(system, messages, model, max_tokens):
    api_key = os.environ["OPENROUTER_API_KEY"]
    url = "https://openrouter.ai/api/v1/chat/completions"
    # OpenRouter uses chat-completions: system goes as the first message
    chat = [{"role": "system", "content": system}] + list(messages)
    body = json.dumps({"model": model, "max_tokens": max_tokens, "messages": chat}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
        "HTTP-Referer": "https://github.com/hstre/DESi",
        "X-Title": "DESi A/B Evidence Probe",
    })
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    latency_ms = int((time.time() - t0) * 1000)
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {}) or {}
    return {"text": text, "latency_ms": latency_ms, "backend": "openrouter",
            "model": model,
            "input_tokens": usage.get("prompt_tokens"),
            "output_tokens": usage.get("completion_tokens"),
            "stop_reason": data["choices"][0].get("finish_reason")}


def call_messages(system: str, messages: list, model: str | None = None,
                  max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
    """Real LLM call. Raises if no API key is set — no silent simulation."""
    try:
        if os.environ.get("ANTHROPIC_API_KEY"):
            return _call_anthropic(system, messages,
                                   model or DEFAULT_MODEL_ANTHROPIC, max_tokens)
        if os.environ.get("OPENROUTER_API_KEY"):
            return _call_openrouter(system, messages,
                                    model or DEFAULT_MODEL_OPENROUTER, max_tokens)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"backend HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}")
    raise RuntimeError(
        "No API key set; no real call is possible. "
        "Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY.")

