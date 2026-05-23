"""Environment-driven configuration for DESi.

Loads `.env` if present. Does NOT hardcode secrets. Raises a precise error when
an API key is required but missing.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is in requirements but kept optional
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")


class ConfigError(RuntimeError):
    """Raised when configuration is incomplete or invalid."""


@dataclass(frozen=True)
class Config:
    deepseek_api_key: str | None
    deepseek_base_url: str
    deepseek_model: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    max_retries: int

    def require_api_key(self) -> str:
        if not self.deepseek_api_key:
            raise ConfigError(
                "DEEPSEEK_API_KEY is not set. Copy .env.example to .env and "
                "fill in your key, or pass --no-llm to skip API calls."
            )
        return self.deepseek_api_key


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a float, got {raw!r}") from exc


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an int, got {raw!r}") from exc


def load_config() -> Config:
    return Config(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=_get_float("DESI_TEMPERATURE", 0.2),
        max_tokens=_get_int("DESI_MAX_TOKENS", 1500),
        timeout_seconds=_get_float("DESI_TIMEOUT_SECONDS", 60.0),
        max_retries=_get_int("DESI_MAX_RETRIES", 3),
    )
