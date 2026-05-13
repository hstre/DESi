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


# Auditor model identifiers. "auto" is the promoted default per paper0
# (commit 853db5d): deepseek-v4-pro on the SKEPTICAL_AUDITOR role,
# deepseek-v4-flash on the four other roles. The PASS verdict on all
# three pre-conditions (improves useful_objection_count without
# increasing false_objection_count or hallucinated_causal_claims) is
# recorded in outputs/role_policy/auditor_model_ablation.md.
AUDITOR_MODEL_FLASH = "deepseek-v4-flash"
AUDITOR_MODEL_PRO = "deepseek-v4-pro"
AUDITOR_MODE_CHOICES = ("flash", "pro", "auto")


def resolve_auditor_model(mode: str, *, default_model: str) -> str:
    """Resolve an --audit-model choice to a concrete model id.

    ``flash`` and ``pro`` are explicit overrides. ``auto`` selects the
    promoted default (pro). Any other value is treated as an explicit
    model id (e.g. someone passes a future model name directly).
    """
    if mode == "flash":
        return AUDITOR_MODEL_FLASH
    if mode == "pro":
        return AUDITOR_MODEL_PRO
    if mode == "auto":
        return AUDITOR_MODEL_PRO
    # Unknown string -> treat as explicit model id passthrough.
    return mode or default_model


@dataclass(frozen=True)
class Config:
    deepseek_api_key: str | None
    deepseek_base_url: str
    deepseek_model: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    max_retries: int
    # Auditor-specific knobs (promoted default after paper0 ablation).
    # `auditor_mode` is one of "flash" | "pro" | "auto" — see
    # `resolve_auditor_model`. `auditor_timeout_seconds` is the request
    # timeout used only for the SKEPTICAL_AUDITOR call; v4-pro reasoning
    # routinely runs 90-150s, so >=120s is required to avoid spurious
    # timeouts.
    auditor_mode: str = "auto"
    auditor_timeout_seconds: float = 120.0
    auditor_max_retries: int = 1

    def require_api_key(self) -> str:
        if not self.deepseek_api_key:
            raise ConfigError(
                "DEEPSEEK_API_KEY is not set. Copy .env.example to .env and "
                "fill in your key, or pass --no-llm to skip API calls."
            )
        return self.deepseek_api_key

    def resolved_auditor_model(self) -> str:
        return resolve_auditor_model(self.auditor_mode, default_model=self.deepseek_model)


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
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        temperature=_get_float("DESI_TEMPERATURE", 0.2),
        max_tokens=_get_int("DESI_MAX_TOKENS", 2048),
        timeout_seconds=_get_float("DESI_TIMEOUT_SECONDS", 60.0),
        max_retries=_get_int("DESI_MAX_RETRIES", 3),
        auditor_mode=os.getenv("DESI_AUDITOR_MODE", "auto"),
        auditor_timeout_seconds=_get_float("DESI_AUDITOR_TIMEOUT_SECONDS", 120.0),
        auditor_max_retries=_get_int("DESI_AUDITOR_MAX_RETRIES", 1),
    )
