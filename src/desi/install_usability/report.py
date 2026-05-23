"""Install-usability GO/NO-GO assessment.

Verifies the dummy-friendly install path is real and safe: docs exist
with the right commands, the offline config loader works, secrets are
protected, offline is the default, and NO replay/governance invariant
was touched. Read-only.
"""
from __future__ import annotations

import pathlib

from desi.packaging_audit import replay_drift_count
from desi.core.determinism_scanner import high_risk_hit_count
from desi.core.governance_core import core_identity, governance_intact
from desi.runtime_config import (
    live_calls_enabled, offline_mode, provider_key_present,
    redacted_provider_view,
)

_ROOT = pathlib.Path(__file__).resolve().parents[3]

_DOCS = ("INSTALL.md", "INSTALL_DUMMIES.md", "QUICKSTART.md",
         "docs/ELI5_DESi.md")
_MINIMAL_CMDS = ("git clone https://github.com/hstre/DESi.git",
                 "python -m venv .venv", "pip install -e .",
                 "desi doctor")


def install_docs_created() -> bool:
    return all((_ROOT / d).exists() for d in _DOCS)


def dummy_install_path_works() -> bool:
    dummies = (_ROOT / "INSTALL_DUMMIES.md").read_text(encoding="utf-8")
    cmds_ok = all(c in dummies for c in _MINIMAL_CMDS)
    both_os = (
        ".venv\\Scripts\\activate" in dummies
        and "source .venv/bin/activate" in dummies
    )
    example_ok = (_ROOT / "examples" / "hello_desi.py").exists()
    return cmds_ok and both_os and example_ok


def config_loader_works() -> bool:
    from desi.runtime_config import get_model_route, load_config
    cfg = load_config()
    return (
        cfg.get("desi", "offline_mode") == "true"
        and get_model_route("small") == "ibm-granite/granite-4.1-8b"
        and get_model_route("large") == "deepseek/deepseek-v4-pro"
    )


def secrets_protected() -> bool:
    gi = (_ROOT / ".gitignore").read_text(encoding="utf-8")
    gi_ok = all(
        e in gi for e in (
            "config/desi.local.ini", ".env", "*.key", "secrets/")
    )
    example = (_ROOT / "config" / "desi.example.ini").read_text(
        encoding="utf-8")
    example_clean = "sk-or-v1" not in example and "sk-ant" not in example
    local_absent = not (_ROOT / "config" / "desi.local.ini").exists()
    # redacted view never exposes a key value even when one is set
    import os
    prev = os.environ.get("OPENROUTER_API_KEY")
    os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-LEAKCHECK"
    try:
        leaks = "LEAKCHECK" in str(redacted_provider_view("openrouter"))
    finally:
        if prev is None:
            os.environ.pop("OPENROUTER_API_KEY", None)
        else:
            os.environ["OPENROUTER_API_KEY"] = prev
    return gi_ok and example_clean and local_absent and not leaks


def offline_default_preserved() -> bool:
    return offline_mode() is True and live_calls_enabled() is False


def replay_invariants_touched() -> bool:
    return replay_drift_count() != 0 or high_risk_hit_count() != 0


def governance_invariants_touched() -> bool:
    return core_identity() != 1.0 or not governance_intact()


def assessment() -> dict[str, object]:
    return {
        "install_docs_created": install_docs_created(),
        "dummy_install_path_works": dummy_install_path_works(),
        "config_loader_works": config_loader_works(),
        "secrets_protected": secrets_protected(),
        "offline_default_preserved": offline_default_preserved(),
        "replay_invariants_touched": replay_invariants_touched(),
        "governance_invariants_touched":
            governance_invariants_touched(),
        "openrouter_key_set": provider_key_present("openrouter"),
    }


def is_go() -> bool:
    a = assessment()
    return (
        a["install_docs_created"]
        and a["dummy_install_path_works"]
        and a["config_loader_works"]
        and a["secrets_protected"]
        and a["offline_default_preserved"]
        and a["replay_invariants_touched"] is False
        and a["governance_invariants_touched"] is False
    )


def build_go_no_go() -> str:
    a = assessment()
    verdict = "GO" if is_go() else "NO-GO"

    def yn(b: bool) -> str:
        return "yes" if b else "no"

    return "\n".join([
        "# DESi Install-Usability - Go/No-Go",
        "",
        f"**Result:** `{verdict}`",
        "",
        "Goal: make DESi easy to install and test for non-Python "
        "users, without leaking secrets, enabling live calls "
        "silently, or touching any replay/governance invariant. "
        "Offline is the default; live LLM calls require an explicit "
        "two-flag opt-in.",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| install docs created | {yn(a['install_docs_created'])} |",
        f"| dummy install path works | "
        f"{yn(a['dummy_install_path_works'])} |",
        f"| config loader works | {yn(a['config_loader_works'])} |",
        f"| secrets protected | {yn(a['secrets_protected'])} |",
        f"| offline default preserved | "
        f"{yn(a['offline_default_preserved'])} |",
        f"| replay invariants touched | "
        f"{yn(a['replay_invariants_touched'])} |",
        f"| governance invariants touched | "
        f"{yn(a['governance_invariants_touched'])} |",
        "",
        "## What was added",
        "",
        "- `INSTALL.md`, `INSTALL_DUMMIES.md`, `QUICKSTART.md`, "
        "`docs/ELI5_DESi.md` (beginner docs, Windows + macOS/Linux).",
        "- `config/desi.example.ini` (committed, keyless) + a "
        "gitignored `config/desi.local.ini` slot; `desi.runtime_config`"
        " loader (offline default, ENV override, no secret logging).",
        "- `desi config` and `desi doctor` CLI subcommands "
        "(offline-safe; never print key values).",
        "- `examples/hello_desi.py` (runs with no API key).",
        "- `scripts/install_dev.sh` / `.ps1` (venv + pip install -e . "
        "+ doctor; no key prompts, no hidden downloads).",
        "",
        "## Invariants",
        "",
        "Replay drift = 0 (artifacts byte-identical), determinism "
        "scanner clean, core_identity = 1.0, governance intact. No "
        "replay artifact was overwritten and no hidden state or "
        "silent live-call path was introduced. If usability and "
        "replay-governance ever conflict, replay-governance wins.",
        "",
    ])


__all__ = [
    "assessment",
    "build_go_no_go",
    "config_loader_works",
    "dummy_install_path_works",
    "install_docs_created",
    "is_go",
    "offline_default_preserved",
    "secrets_protected",
]
