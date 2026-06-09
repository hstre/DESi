"""Provider registry + one adapter for local and API LLMs.

The key simplification behind "run an LLM locally in the user's network OR via an
internet API": both speak the same OpenAI-compatible ``/v1/chat/completions``
wire format. Ollama, llama.cpp, LM Studio, vLLM expose it locally; OpenRouter,
DeepSeek, OpenAI expose it remotely. So a provider is just a base URL, an
optional API key, and a locality tag — no special-casing.

The HTTP client uses only the standard library (urllib) so the router has no
hard third-party dependency and genuinely "runs locally". Live calls obviously
require a reachable endpoint; the deterministic routing layer above never needs
one.
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ModelSpec:
    id: str
    locality: str                       # "local" | "api"
    cost_per_item_usd: float = 0.0
    task_scores: dict[str, float] = field(default_factory=dict)

    @property
    def is_local(self) -> bool:
        return self.locality == "local"


@dataclass
class Provider:
    name: str
    base_url: str                       # e.g. http://localhost:11434/v1  or  https://openrouter.ai/api/v1
    api_key_env: str | None = None      # name of env var holding the key (never the key itself)
    models: list[ModelSpec] = field(default_factory=list)

    @property
    def is_local(self) -> bool:
        host = self.base_url.split("//", 1)[-1]
        return host.startswith(("localhost", "127.0.0.1", "0.0.0.0", "192.168.", "10.", "host.docker.internal"))


@dataclass
class Registry:
    providers: list[Provider]

    def all_models(self) -> list[tuple[Provider, ModelSpec]]:
        return [(p, m) for p in self.providers for m in p.models]


def load_config(path: str | Path) -> Registry:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    providers = []
    for p in raw.get("providers", []):
        models = [
            ModelSpec(
                id=m["id"],
                locality=m.get("locality", "api"),
                cost_per_item_usd=float(m.get("cost_per_item_usd", 0.0)),
                task_scores={k: float(v) for k, v in m.get("task_scores", {}).items()},
            )
            for m in p.get("models", [])
        ]
        providers.append(
            Provider(
                name=p["name"],
                base_url=p["base_url"].rstrip("/"),
                api_key_env=p.get("api_key_env"),
                models=models,
            )
        )
    return Registry(providers=providers)


class OpenAICompatibleClient:
    """Minimal OpenAI-compatible chat client over urllib (live calls only)."""

    def __init__(self, provider: Provider, timeout: float = 60.0):
        self.provider = provider
        self.timeout = timeout

    def chat(self, model: str, messages: list[dict], **params) -> str:
        key = os.environ.get(self.provider.api_key_env) if self.provider.api_key_env else None
        body = json.dumps({"model": model, "messages": messages, **params}).encode()
        req = urllib.request.Request(
            f"{self.provider.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {key}"} if key else {}),
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
