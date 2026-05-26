"""Model ports for the HF answering layer (PERIPHERAL).

A model port turns a prompt into a raw answer. DESi is NEVER an answer generator;
these ports are external models, attached at the periphery and decoupled from the
core. Ports read their token in-process from the environment and raise loudly if
it is missing — they never fabricate an answer.

Ports:
  * OpenRouterPort  — Granite / Claude Haiku / GPT-4.1-mini via the existing
                      desi.live_llm_validation.openrouter_client (OPENROUTER_API_KEY).
  * HFInferencePort — any HF inference model (HF_TOKEN).
  * ConstantBaselinePort — deterministic offline baseline (no token, no network);
                      for pipeline wiring/smoke runs only, NOT a model.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Protocol, runtime_checkable

_REPO = Path(__file__).resolve().parents[2]  # benchmarks/hf_answering/.. /.. = repo root
sys.path.insert(0, str(_REPO / "src"))

# OpenRouter model ids (same ones used in earlier DESi live validation).
GRANITE = "ibm-granite/granite-4.1-8b"
CLAUDE_HAIKU = "anthropic/claude-haiku-4.5"
GPT_MINI = "openai/gpt-4.1-mini"

# OpenRouter list pricing ($/token) for the optional cost estimate.
_PRICE = {
    GRANITE: (0.05e-6, 0.10e-6),
    CLAUDE_HAIKU: (1.00e-6, 5.00e-6),
    GPT_MINI: (0.40e-6, 1.60e-6),
}


@runtime_checkable
class ModelPort(Protocol):
    name: str

    def answer(self, prompt: str) -> tuple[str, int, int]:
        """Return (raw_text, prompt_tokens, completion_tokens). One call."""
        ...


class OpenRouterPort:
    """Real model answers via OpenRouter. Reads OPENROUTER_API_KEY in-process."""

    def __init__(self, model_id: str, *, max_tokens: int = 8) -> None:
        from desi.live_llm_validation.openrouter_client import api_key_present
        if not api_key_present():
            raise RuntimeError(
                "OPENROUTER_API_KEY not set; OpenRouter answering unavailable "
                "(no answer is ever fabricated)."
            )
        self.name = model_id
        self.model_id = model_id
        self.max_tokens = max_tokens

    def answer(self, prompt: str) -> tuple[str, int, int]:
        from desi.live_llm_validation.openrouter_client import chat_completion
        resp = chat_completion(
            self.model_id,
            [{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens, temperature=0.0,
        )
        text = (resp["choices"][0]["message"].get("content") or "").strip()
        usage = resp.get("usage") or {}
        return text, int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0)

    def price(self):
        return _PRICE.get(self.model_id)


class HFInferencePort:
    """Real model answers via HF inference. Reads HF_TOKEN in-process."""

    def __init__(self, model_id: str, *, max_new_tokens: int = 8,
                 token_env: str = "HF_TOKEN") -> None:
        from huggingface_hub import InferenceClient
        token = os.environ.get(token_env)
        if not token:
            raise RuntimeError(f"{token_env} not set; HF inference unavailable.")
        self.name = model_id
        self._client = InferenceClient(model=model_id, token=token)
        self.max_new_tokens = max_new_tokens

    def answer(self, prompt: str) -> tuple[str, int, int]:
        text = self._client.text_generation(prompt, max_new_tokens=self.max_new_tokens)
        return str(text).strip(), 0, 0

    def price(self):
        return None


class ConstantBaselinePort:
    """Deterministic offline baseline: predicts a constant answer for every
    example. No model, no token, no network. Used ONLY to validate the
    dataset -> port -> evaluator -> DESi-core pipeline; it is a baseline, not a
    model, and its accuracy reflects the dataset base rate, not model quality."""

    def __init__(self, value: bool = False) -> None:
        self.name = f"constant_baseline({value})"
        self._text = "yes" if value else "no"

    def answer(self, prompt: str) -> tuple[str, int, int]:
        return self._text, 0, 0

    def price(self):
        return (0.0, 0.0)


def get_port(model: str, backend: str):
    """Resolve a model port. backend: openrouter | hf | baseline."""
    ids = {"granite": GRANITE, "claude": CLAUDE_HAIKU, "gpt": GPT_MINI}
    if backend == "baseline":
        return ConstantBaselinePort(value=False)
    model_id = ids.get(model, model)
    if backend == "openrouter":
        return OpenRouterPort(model_id)
    if backend == "hf":
        return HFInferencePort(model_id)
    raise ValueError(f"unknown backend: {backend}")


__all__ = [
    "CLAUDE_HAIKU", "GPT_MINI", "GRANITE", "ConstantBaselinePort",
    "HFInferencePort", "ModelPort", "OpenRouterPort", "get_port",
]
