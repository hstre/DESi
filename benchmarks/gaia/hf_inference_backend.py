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

# GAIA is exact-match scored and wants the bare final answer. The strict prompt
# additionally tells the model not to invent verifiable facts and to emit
# UNKNOWN rather than guess when the evidence is missing.
MINIMAL_INSTRUCTION = (
    "Reply with ONLY the final answer: no explanation, no preamble, no trailing "
    "punctuation. If the answer is a number, output just the number."
)
STRICT_INSTRUCTION = (
    "Solve the task carefully and reason about it internally, but do not show "
    "your work. Use only the information given in the question and any attached "
    "file content provided in the context. "
    "Return ONLY the final answer — no explanation, no prose, no labels, and no "
    "units unless the question explicitly asks for them. "
    "Do not guess or invent verifiable facts: if the required evidence is "
    "missing or you are not confident, answer exactly UNKNOWN."
)
UNKNOWN_ANSWER = "UNKNOWN"

# Recommended models for DESi-GAIA. Granite is the open, reproducible baseline.
# These are examples only — there is NO hard default model; HF_INFERENCE_MODEL
# (or --model) must be set. Availability via HF Inference depends on the
# providers enabled for your token, so the exact id may need adjusting.
RECOMMENDED_HF_MODELS = (
    "ibm-granite/granite-3.3-8b-instruct",
    "ibm-granite/granite-3.3-2b-instruct",
    "ibm-granite/granite-3.2-8b-instruct",
)


def instruction_for(mode: str) -> str:
    """Return the system instruction for a prompt mode (``minimal``|``strict``)."""
    return STRICT_INSTRUCTION if mode == "strict" else MINIMAL_INSTRUCTION


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


def _usage_dict(usage: object) -> dict | None:
    if usage is None:
        return None
    out = {}
    for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
        v = getattr(usage, k, None)
        if v is None and isinstance(usage, dict):
            v = usage.get(k)
        if v is not None:
            out[k] = v
    return out or None


def chat_answer_with_meta(
    question: str,
    *,
    model: str,
    instruction: str,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    temperature: float = 0.0,
    timeout: float = _DEFAULT_TIMEOUT,
) -> tuple[str, dict]:
    """Return (answer, meta) from HF Inference.

    meta has provider_returned_model, finish_reason and usage. Raises on failure
    (callers turn it into a clean fallback). The token is read from the
    environment and never exposed.
    """
    tok = token()
    if not tok:
        raise RuntimeError("no HF token: set HF_TOKEN or HUGGINGFACE_HUB_TOKEN")
    if not model:
        raise RuntimeError(
            f"no model: set {_MODEL_ENV} or pass --model "
            f"(recommended: {RECOMMENDED_HF_MODELS[0]})"
        )

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
    choice = completion.choices[0]
    answer = (choice.message.content or "").strip()
    meta = {
        "provider_returned_model": getattr(completion, "model", None),
        "finish_reason": getattr(choice, "finish_reason", None),
        "usage": _usage_dict(getattr(completion, "usage", None)),
    }
    return answer, meta


def chat_answer(question: str, **kwargs) -> str:
    """Return only the concise final answer (see chat_answer_with_meta)."""
    return chat_answer_with_meta(question, **kwargs)[0]


__all__ = [
    "MINIMAL_INSTRUCTION", "RECOMMENDED_HF_MODELS", "STRICT_INSTRUCTION",
    "UNKNOWN_ANSWER", "available", "chat_answer", "chat_answer_with_meta",
    "instruction_for", "resolve_model", "token", "token_present",
]


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
                q, model=model_id, instruction=instruction_for("strict"),
            ))
        except Exception as exc:
            print("error:", repr(exc))
