#!/usr/bin/env python3
"""Hugging Face Inference backend for the GAIA pipeline.

Uses ``huggingface_hub.InferenceClient.chat_completion`` to produce a concise
final answer. The token is read **only** from the environment (``HF_TOKEN`` or
``HUGGINGFACE_HUB_TOKEN``) and the model from ``HF_INFERENCE_MODEL`` or an
explicit argument. The token is never logged, returned, or committed.

The model must be chat-completion / instruct capable.
"""
from __future__ import annotations

import os

_TOKEN_ENVS = ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN")
_MODEL_ENV = "HF_INFERENCE_MODEL"
_DEFAULT_TIMEOUT = 60.0
_DEFAULT_MAX_TOKENS = 64


def token() -> str | None:
    """Return the HF token from the environment, or None. Never logged."""
    for env in _TOKEN_ENVS:
        value = os.environ.get(env)
        if value:
            return value
    return None


def token_present() -> bool:
    return token() is not None


def resolve_model(cli_model: str | None = None) -> str | None:
    """Resolve the model id from an explicit argument or ``HF_INFERENCE_MODEL``."""
    return cli_model or os.environ.get(_MODEL_ENV) or None


def available(cli_model: str | None = None) -> bool:
    """True iff both a token and a model are configured."""
    return token_present() and bool(resolve_model(cli_model))


def chat_answer(
    question: str,
    *,
    model: str,
    instruction: str,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    temperature: float = 0.0,
    timeout: float = _DEFAULT_TIMEOUT,
) -> str:
    """Return a concise final answer from HF Inference.

    Raises ``RuntimeError`` (or the underlying client error) on failure; callers
    are expected to catch and turn it into a clean fallback. The token is read
    from the environment and never exposed.
    """
    tok = token()
    if not tok:
        raise RuntimeError(
            "no HF token: set HF_TOKEN or HUGGINGFACE_HUB_TOKEN"
        )
    if not model:
        raise RuntimeError(f"no model: set {_MODEL_ENV} or pass --model")

    from huggingface_hub import InferenceClient

    client = InferenceClient(token=tok, timeout=timeout)
    completion = client.chat_completion(
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": question},
        ],
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    content = completion.choices[0].message.content
    return (content or "").strip()


__all__ = ["available", "chat_answer", "resolve_model", "token", "token_present"]


if __name__ == "__main__":
    import sys

    model_id = resolve_model()
    # Never print the token itself — only whether it is present.
    print(f"token_present={token_present()} model={model_id!r} "
          f"available={available()}")
    if available():
        q = sys.argv[1] if len(sys.argv) > 1 else "What is 2+2?"
        try:
            print("answer:", chat_answer(
                q, model=model_id,
                instruction="Answer with ONLY the final answer, no explanation.",
            ))
        except Exception as exc:
            print("error:", repr(exc))
