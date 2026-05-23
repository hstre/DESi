"""v38.0 - model registry over the captured OpenRouter catalog.

Maps DESi's two roles to real OpenRouter models and exposes their
real captured versions and pricing. The catalog snapshot is a real
capture of the public OpenRouter models endpoint (committed, replay
source) - no provider-specific paths, everything via OpenRouter.
"""
from __future__ import annotations

import json
import pathlib
from functools import lru_cache

ROLE_GRANITE = "granite_structured"
ROLE_DEEPSEEK = "deepseek_semantic"

_ROLE_MODEL: dict[str, str] = {
    ROLE_GRANITE: "ibm-granite/granite-4.1-8b",
    ROLE_DEEPSEEK: "deepseek/deepseek-v4-pro",
}

_CATALOG = (
    pathlib.Path(__file__).resolve().parent
    / "captures" / "models_catalog.json"
)


@lru_cache(maxsize=1)
def catalog() -> dict:
    return json.loads(_CATALOG.read_text(encoding="utf-8"))


def catalog_models() -> dict[str, dict]:
    return {m["id"]: m for m in catalog().get("models", [])}


def roles() -> tuple[str, ...]:
    return (ROLE_GRANITE, ROLE_DEEPSEEK)


def model_for_role(role: str) -> str:
    return _ROLE_MODEL[role]


def pricing_for(model_id: str) -> dict:
    return catalog_models().get(model_id, {}).get("pricing", {})


def model_present(model_id: str) -> bool:
    return model_id in catalog_models()


def completion_price(model_id: str) -> float:
    p = pricing_for(model_id).get("completion")
    return float(p) if p is not None else 0.0


def prompt_price(model_id: str) -> float:
    p = pricing_for(model_id).get("prompt")
    return float(p) if p is not None else 0.0


__all__ = [
    "ROLE_DEEPSEEK",
    "ROLE_GRANITE",
    "catalog",
    "catalog_models",
    "completion_price",
    "model_for_role",
    "model_present",
    "pricing_for",
    "prompt_price",
    "roles",
]
