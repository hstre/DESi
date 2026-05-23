"""DESi governance CLI (`desi`).

Minimal, real subcommands over the in-place implementations - no fake
output, no marketing. Each subcommand invokes genuine functions and
prints a deterministic summary.

    desi replay      - replay-stability + determinism check
    desi audit       - documentation overreach audit (README self-review)
    desi benchmark   - external benchmark verdict summary
    desi review      - role-based skeptical reviewer summary

This CLI does not mutate state, does not write artifacts, and never
auto-fixes. It reports.
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
    return p


_DISPATCH = {
    "replay": _cmd_replay,
    "audit": _cmd_audit,
    "benchmark": _cmd_benchmark,
    "review": _cmd_review,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return _DISPATCH[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
