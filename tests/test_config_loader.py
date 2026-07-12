"""Tests for the dummy-friendly runtime config loader.

Confirms offline-by-default, secret protection, and routing - without
ever exposing a key value.
"""
from __future__ import annotations

import pathlib

import desi.runtime_config as rc

_ROOT = pathlib.Path(__file__).resolve().parents[1]


# --- offline by default -------------------------
def test_offline_mode_default_true() -> None:
    assert rc.offline_mode() is True


def test_live_calls_disabled_by_default() -> None:
    assert rc.live_calls_enabled() is False


def test_example_ini_has_no_real_keys() -> None:
    ini = (_ROOT / "config" / "desi.example.ini").read_text(
        encoding="utf-8")
    # every api_key line is blank in the committed example
    for line in ini.splitlines():
        s = line.strip()
        if s.startswith("api_key"):
            assert s in ("api_key =", "api_key="), line
    assert "sk-or-v1" not in ini
    assert "sk-ant" not in ini


def test_local_ini_is_gitignored_and_absent() -> None:
    gi = (_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "config/desi.local.ini" in gi
    # it must never be committed
    assert not (_ROOT / "config" / "desi.local.ini").exists()


def test_gitignore_covers_secret_paths() -> None:
    gi = (_ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in (".env", ".env.local", "*.key", "secrets/"):
        assert entry in gi, entry


# --- loader behaviour ---------------------------
def test_load_config_returns_sections() -> None:
    cfg = rc.load_config()
    assert cfg.section("openrouter")["base_url"].startswith("https://")
    assert cfg.get("desi", "offline_mode") == "true"


def test_model_routing() -> None:
    assert rc.get_model_route("small") == "ibm-granite/granite-4.1-8b"
    assert rc.get_model_route("structured") == (
        "ibm-granite/granite-4.1-8b")
    assert rc.get_model_route("large") == "deepseek/deepseek-v4-pro"
    assert rc.get_model_route("semantic") == "deepseek/deepseek-v4-pro"


def test_small_model_floor() -> None:
    # the default small model meets the >= ~8B floor
    assert rc.small_model_floor_ok() is True
    assert rc.get_model_route("small") == "ibm-granite/granite-4.1-8b"
    # the retired 3B micro is below the floor; >=8B / >=30B are fine
    assert rc.small_model_meets_floor("ibm-granite/granite-4.0-h-micro") is False
    assert rc.small_model_meets_floor("mistralai/ministral-3b-2512") is False
    assert rc.small_model_meets_floor("gpt-5-nano") is False
    assert rc.small_model_meets_floor("ibm-granite/granite-4.1-8b") is True
    assert rc.small_model_meets_floor("google/gemma-4-31b-it:free") is True
    assert rc.small_model_meets_floor("qwen/qwen3-next-80b-a3b-instruct") is True


# --- secrets never leak -------------------------
def test_env_key_overrides_but_redacted_view_hides_it(
    monkeypatch,
) -> None:
    fake = "sk-or-v1-THISKEYMUSTNOTLEAK000"
    monkeypatch.setenv("OPENROUTER_API_KEY", fake)
    # the key IS available for live calls...
    assert rc.get_provider_config("openrouter")["api_key"] == fake
    assert rc.provider_key_present("openrouter") is True
    # ...but the display view never contains the value
    view = rc.redacted_provider_view("openrouter")
    assert view["api_key_set"] is True
    assert fake not in str(view)
    assert "api_key" not in view  # only api_key_set is exposed


def test_env_can_enable_live_only_with_both_flags(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DESI_ALLOW_LIVE_LLM_CALLS", "true")
    # allow flag alone is not enough while offline_mode stays true
    assert rc.live_calls_enabled() is False
    monkeypatch.setenv("DESI_OFFLINE_MODE", "false")
    assert rc.live_calls_enabled() is True
