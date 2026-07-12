"""DESi runtime configuration (user-facing INI loader).

Separate from the prototype `desi.config` (which is env-driven and
kept unchanged). This loader powers the dummy-friendly install path
and the `desi config` / `desi doctor` CLI.

Safety rules (never violated):
* OFFLINE by default. Live LLM calls require an explicit opt-in
  (`allow_live_llm_calls = true` AND `offline_mode = false`).
* Secrets are never logged and never written to artifacts. The public
  views expose only whether a key is present, never its value.
* Load order: config/desi.local.ini (gitignored) -> config/
  desi.example.ini -> built-in offline defaults. ENV always overrides.
* If nothing is configured, DESi runs fully offline.
"""
from __future__ import annotations

import configparser
import os
import pathlib
import re
from dataclasses import dataclass

# Empirical floor for DESi's small language layer. On the hard epistemic-detection
# benchmark a ~3B model (granite-4.0-h-micro) collapses (F1 0.54, over-flags the
# adversarial controls) while granite-4.1-8b holds (F1 0.89) and >=30B free/cheap
# models saturate near 1.0. So the small model must be >= ~8B. See
# src/desi/case_studies/marcognity_muse_spark/redteam/hard/REDTEAM_HARD_RESULT.md
SMALL_MODEL_FLOOR_B = 8
SMALL_MODEL_FLOOR_NOTE = (
    "DESi's small language layer must be >= ~8B: on the hard epistemic-detection "
    "benchmark a ~3B model collapses (F1 0.54) while an 8B holds (0.89). "
    "See redteam/hard/REDTEAM_HARD_RESULT.md."
)
_BELOW_FLOOR_TOKENS = ("micro", "nano")

# Built-in safe defaults (used if no INI is found).
_DEFAULTS: dict[str, dict[str, str]] = {
    "openrouter": {
        "api_key": "",
        "base_url": "https://openrouter.ai/api/v1",
        "default_small_model": "ibm-granite/granite-4.1-8b",
        "default_large_model": "deepseek/deepseek-v4-pro",
    },
    "openai": {"api_key": "", "default_model": ""},
    "anthropic": {"api_key": "", "default_model": ""},
    "local": {"enabled": "false", "base_url": "", "default_model": ""},
    "desi": {
        "offline_mode": "true",
        "allow_live_llm_calls": "false",
        "write_live_captures": "false",
    },
}

# ENV overrides: env var -> (section, key)
_ENV_MAP: dict[str, tuple[str, str]] = {
    "OPENROUTER_API_KEY": ("openrouter", "api_key"),
    "OPENROUTER_BASE_URL": ("openrouter", "base_url"),
    "OPENAI_API_KEY": ("openai", "api_key"),
    "ANTHROPIC_API_KEY": ("anthropic", "api_key"),
    "DESI_OFFLINE_MODE": ("desi", "offline_mode"),
    "DESI_ALLOW_LIVE_LLM_CALLS": ("desi", "allow_live_llm_calls"),
    "DESI_WRITE_LIVE_CAPTURES": ("desi", "write_live_captures"),
}

_SECRET_KEYS = frozenset({"api_key"})


def _config_dirs() -> list[pathlib.Path]:
    """Search the current working directory and the repo root."""
    here = pathlib.Path(__file__).resolve()
    candidates = [
        pathlib.Path.cwd() / "config",
        here.parents[2] / "config",  # repo root when running from src
    ]
    seen: list[pathlib.Path] = []
    for c in candidates:
        if c not in seen:
            seen.append(c)
    return seen


def config_source() -> str:
    """Which INI (if any) is the active source - for display only."""
    for d in _config_dirs():
        if (d / "desi.local.ini").exists():
            return str(d / "desi.local.ini")
    for d in _config_dirs():
        if (d / "desi.example.ini").exists():
            return str(d / "desi.example.ini")
    return "built-in-defaults"


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    _data: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]
    source: str

    def section(self, name: str) -> dict[str, str]:
        for sec, items in self._data:
            if sec == name:
                return {k: v for k, v in items}
        return {}

    def get(self, section: str, key: str, default: str = "") -> str:
        return self.section(section).get(key, default)


def load_config() -> Config:
    """Load merged config: defaults <- INI <- ENV. Never logs."""
    parser = configparser.ConfigParser()
    # start from defaults
    merged: dict[str, dict[str, str]] = {
        s: dict(v) for s, v in _DEFAULTS.items()
    }
    # overlay INI (local preferred, else example)
    src = config_source()
    if src != "built-in-defaults":
        parser.read(src, encoding="utf-8")
        for sec in parser.sections():
            merged.setdefault(sec, {})
            for k, v in parser.items(sec):
                merged[sec][k] = v
    # overlay ENV
    for env, (sec, key) in _ENV_MAP.items():
        val = os.environ.get(env)
        if val is not None and val != "":
            merged.setdefault(sec, {})[key] = val
    data = tuple(
        (sec, tuple(sorted(items.items())))
        for sec, items in sorted(merged.items())
    )
    return Config(_data=data, source=src)


def get_provider_config(provider: str) -> dict[str, str]:
    """Full provider section (may include the api_key for live calls).

    Callers MUST NOT log this; use `redacted_provider_view` for
    display.
    """
    return load_config().section(provider)


def provider_key_present(provider: str) -> bool:
    return bool(get_provider_config(provider).get("api_key", "").strip())


def redacted_provider_view(provider: str) -> dict[str, object]:
    """Display-safe view: never exposes the key value."""
    cfg = get_provider_config(provider)
    view: dict[str, object] = {"api_key_set": provider_key_present(provider)}
    for k, v in cfg.items():
        if k not in _SECRET_KEYS:
            view[k] = v
    return view


def offline_mode() -> bool:
    return _truthy(load_config().get("desi", "offline_mode", "true"))


def live_calls_enabled() -> bool:
    """Live LLM calls require BOTH an explicit allow flag AND offline
    mode being off. Default is False (safe)."""
    cfg = load_config()
    allow = _truthy(cfg.get("desi", "allow_live_llm_calls", "false"))
    off = _truthy(cfg.get("desi", "offline_mode", "true"))
    return allow and not off


def write_live_captures_enabled() -> bool:
    return (
        live_calls_enabled()
        and _truthy(load_config().get(
            "desi", "write_live_captures", "false"))
    )


def get_model_route(task_type: str) -> str:
    """Route a task to a model id. 'small'/'structured' -> small
    model; 'large'/'semantic'/'reasoning' -> large model."""
    orc = get_provider_config("openrouter")
    small = orc.get("default_small_model", "")
    large = orc.get("default_large_model", "")
    t = task_type.strip().lower()
    if t in {"large", "semantic", "reasoning", "hard", "deepseek"}:
        return large
    return small


def small_model_meets_floor(model_id: str) -> bool:
    """Heuristic advisory: is the small model at/above the ~8B floor?

    Flags known-too-small models (a 'micro'/'nano' tag, or an explicit size token
    below 8B such as '-3b'). Unknown/unsized ids are assumed OK (frontier/named
    models). This is advisory (surfaced by ``desi doctor``); it does not block
    routing.
    """
    mid = (model_id or "").lower()
    if any(t in mid for t in _BELOW_FLOOR_TOKENS):
        return False
    m = re.search(r"(\d+(?:\.\d+)?)b\b", mid)     # size like -8b, -3b, -31b, -80b
    if m:
        try:
            return float(m.group(1)) >= SMALL_MODEL_FLOOR_B
        except ValueError:
            return True
    return True


def small_model_floor_ok() -> bool:
    """Whether the configured small model meets the empirical ~8B floor."""
    small = get_provider_config("openrouter").get("default_small_model", "")
    return small_model_meets_floor(small)


def configured_providers() -> tuple[str, ...]:
    return tuple(
        p for p in ("openrouter", "openai", "anthropic")
        if provider_key_present(p)
    )


__all__ = [
    "Config",
    "SMALL_MODEL_FLOOR_B",
    "SMALL_MODEL_FLOOR_NOTE",
    "config_source",
    "configured_providers",
    "get_model_route",
    "get_provider_config",
    "live_calls_enabled",
    "load_config",
    "offline_mode",
    "provider_key_present",
    "redacted_provider_view",
    "small_model_floor_ok",
    "small_model_meets_floor",
    "write_live_captures_enabled",
]
