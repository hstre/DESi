"""v38.0 - OpenRouter client (the only network boundary).

All models run exclusively over OpenRouter; there are no
provider-specific paths in the core. Authentication is ENV-based
(OPENROUTER_API_KEY) - no key ever lives in the repo. The client is
used only during the capture phase (the stochastic input layer);
deterministic evaluation reads captured raw outputs and never calls
the network.
"""
from __future__ import annotations

import json
import os
import urllib.request

_BASE = "https://openrouter.ai/api/v1"
_API_KEY_ENV = "OPENROUTER_API_KEY"


def api_key_present() -> bool:
    return bool(os.environ.get(_API_KEY_ENV))


def _require_key() -> str:
    key = os.environ.get(_API_KEY_ENV)
    if not key:
        raise RuntimeError(
            f"{_API_KEY_ENV} is not set; live inference is "
            "unavailable. No response will be fabricated."
        )
    return key


def list_models(timeout: int = 20) -> list[dict]:
    """GET /models - public, no key required."""
    req = urllib.request.Request(
        f"{_BASE}/models",
        headers={"User-Agent": "DESi-live-llm-validation/38"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("data", [])


def chat_completion(
    model: str,
    messages: list[dict],
    *,
    max_tokens: int = 256,
    temperature: float = 0.0,
    timeout: int = 60,
) -> dict:
    """POST /chat/completions - real authenticated inference. Returns
    the raw OpenRouter response dict. Raises if no key is present
    (never fabricates a response)."""
    key = _require_key()
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{_BASE}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "DESi-live-llm-validation/38",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


__all__ = [
    "api_key_present",
    "chat_completion",
    "list_models",
]
