"""Claude-backend adapter.

Two modes:
  - REAL: requires ANTHROPIC_API_KEY in env. Sends real /v1/messages calls.
  - UNAVAILABLE: documented status when no API key is present. No simulation, no mock —
    the harness explicitly REFUSES to fake responses, per the brief's honesty rule.

If/when this runs with a real key, ALL four primary metrics get measured from real outputs.
Until then, status is `UNAVAILABLE_in_this_env` and the report says so plainly.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_MAX_TOKENS = 1024


def is_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def call_messages(system: str, messages: list, model: str = DEFAULT_MODEL,
                  max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
    """Real Anthropic /v1/messages call. Raises if API key is not set — no silent simulation."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set; no real Claude call is possible.")
    url = (os.environ.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/") \
          + "/v1/messages"
    body = json.dumps({"model": model, "max_tokens": max_tokens, "system": system,
                       "messages": messages}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Anthropic API HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}")
    latency_ms = int((time.time() - t0) * 1000)
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return {"text": text, "latency_ms": latency_ms,
            "input_tokens": data.get("usage", {}).get("input_tokens"),
            "output_tokens": data.get("usage", {}).get("output_tokens"),
            "stop_reason": data.get("stop_reason")}
