"""DESi governance CLI (`desi`).

Minimal, real subcommands over the in-place implementations - no fake
output, no marketing. Each subcommand invokes genuine functions and
prints a deterministic summary.

    desi replay      - replay-stability + determinism check
    desi audit       - documentation overreach audit (README self-review)
    desi benchmark   - external benchmark verdict summary
    desi review      - role-based skeptical reviewer summary
    desi config      - show configured providers + offline/live mode
    desi doctor      - environment readiness check (offline-safe)

This CLI does not mutate state, does not write artifacts, never makes
live LLM calls, and never auto-fixes. It reports. Secrets are never
printed.
"""
from __future__ import annotations

import argparse
import json
import sys


def _cmd_replay(_args: argparse.Namespace) -> int:
    from desi.core.determinism_scanner import determinism_clean
    from desi.core.governance_core import core_identity
    from desi.core.replay_kernel import is_replay_stable, replay_hash

    probe = {"phase": "replay-probe", "values": [1, 2, 3], "x": 0.611}
    stable = is_replay_stable(probe)
    out = {
        "replay_hash_of_probe": replay_hash(probe),
        "replay_stable": stable,
        "determinism_clean": determinism_clean(),
        "core_identity": core_identity(),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if (stable and out["determinism_clean"]
                 and out["core_identity"] == 1.0) else 1


def _cmd_audit(_args: argparse.Namespace) -> int:
    from desi.readme_self_review import (
        gate_failing_conditions, gate_passes_all, recommendation,
    )
    out = {
        "audit": "README / system-paper internal overreach audit",
        "recommendation": recommendation(),
        "gate_passes_all": gate_passes_all(),
        "failing_conditions": list(gate_failing_conditions()),
        "note": (
            "DESi performs an internal consistency and overreach "
            "audit of its own documentation; it does not validate "
            "itself."
        ),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def _cmd_benchmark(_args: argparse.Namespace) -> int:
    from desi.external_benchmarks_verdict import (
        aggregate, classify_corpus, gate_passes_all,
    )
    out = {
        "phase": "v35.4 real external benchmark verdict",
        "metrics": aggregate().to_dict(),
        "classification": classify_corpus(),
        "gate_passes_all": gate_passes_all(),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def _cmd_review(_args: argparse.Namespace) -> int:
    from desi.reviewer.reviewer_port import (
        IMPLEMENTED_BY, recommendation, role_review_report,
    )
    rep = role_review_report()
    out = {
        "reviewer_port_implemented_by": list(IMPLEMENTED_BY),
        "documentation_audit_recommendation": recommendation(),
        "role_reviewer_recommendation": rep.recommendation,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def _cmd_config(_args: argparse.Namespace) -> int:
    from desi.runtime_config import (
        config_source, configured_providers, get_model_route,
        live_calls_enabled, offline_mode, redacted_provider_view,
    )
    out = {
        "config_source": config_source(),
        "offline_mode": offline_mode(),
        "live_calls_enabled": live_calls_enabled(),
        "configured_providers": list(configured_providers()),
        "providers": {
            p: redacted_provider_view(p)
            for p in ("openrouter", "openai", "anthropic")
        },
        "model_routes": {
            "small/structured": get_model_route("small"),
            "large/semantic": get_model_route("large"),
        },
        "note": "API key values are never printed; only api_key_set.",
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def _cmd_doctor(_args: argparse.Namespace) -> int:
    import importlib.util
    import pathlib

    from desi.runtime_config import (
        config_source, live_calls_enabled, offline_mode,
        provider_key_present,
    )

    checks: list[tuple[str, bool, str]] = []

    py_ok = sys.version_info >= (3, 11)
    checks.append((
        "Python", py_ok,
        f"{sys.version_info.major}.{sys.version_info.minor} "
        f"({'>= 3.11' if py_ok else 'NEED >= 3.11'})"))

    pkg_ok = importlib.util.find_spec("desi") is not None
    checks.append(("Package", pkg_ok, "import desi"))

    cli_ok = True  # this code is the CLI, running
    checks.append(("CLI", cli_ok, "desi entrypoint"))

    src = config_source()
    checks.append(("Config", True, src))

    key_set = provider_key_present("openrouter")
    off = offline_mode()
    api_ok = key_set or off
    checks.append((
        "OpenRouter key", api_ok,
        "set" if key_set else (
            "not set (offline mode ON)" if off
            else "NOT set and offline mode OFF")))

    examples_dir = (
        pathlib.Path(__file__).resolve().parents[2] / "examples"
    )
    ex_ok = (examples_dir / "hello_desi.py").exists()
    checks.append(("Examples", ex_ok, "examples/hello_desi.py"))

    try:
        from desi.core.replay_kernel import is_replay_stable
        from desi.core.determinism_scanner import high_risk_hit_count
        replay_ok = (
            is_replay_stable({"probe": [1, 2, 3]})
            and high_risk_hit_count() == 0
        )
    except Exception:
        replay_ok = False
    checks.append(("Replay test", replay_ok, "deterministic + clean"))

    print("DESi Doctor")
    for name, ok, detail in checks:
        print(f"{name}: {'OK' if ok else 'FAIL'}  ({detail})")
    print(f"Offline mode: {'ON' if off else 'OFF'}")
    print(f"Live LLM calls: {'ENABLED' if live_calls_enabled() else 'disabled'}")

    all_ok = all(ok for _, ok, _ in checks)
    if all_ok and off:
        print("Result: DESi is ready for offline use.")
    elif all_ok:
        print("Result: DESi is ready (live LLM calls configured).")
    else:
        print("Result: setup incomplete - see FAIL lines above.")
    return 0 if all_ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="desi",
        description=(
            "DESi: deterministic, replay-governed epistemic "
            "governance (experimental, v0.1.0a0)."
        ),
    )
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("replay", help="replay-stability + determinism check")
    sub.add_parser("audit", help="documentation overreach audit")
    sub.add_parser("benchmark", help="external benchmark verdict summary")
    sub.add_parser("review", help="role-based skeptical reviewer summary")
    sub.add_parser("config", help="show providers + offline/live mode")
    sub.add_parser("doctor", help="environment readiness check")
    return p


_DISPATCH = {
    "replay": _cmd_replay,
    "audit": _cmd_audit,
    "benchmark": _cmd_benchmark,
    "review": _cmd_review,
    "config": _cmd_config,
    "doctor": _cmd_doctor,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return _DISPATCH[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
