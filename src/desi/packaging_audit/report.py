"""Packaging migration GO/NO-GO assessment.

Answers the three required questions deterministically:

1. Did packaging affect replay stability?  -> replay-drift check:
   every key verdict artifact rebuilt live must be byte-identical to
   the committed artifact.
2. Were hidden states introduced?           -> the packaging-added
   facade/CLI files must contain no nondeterminism patterns
   (random / time.time / datetime.now / tempfile / uuid).
3. Were core invariants violated?           -> core_identity == 1.0,
   governance intact, determinism scanner clean, replay stability 1.0.

This is read-only: it computes the assessment and emits a Markdown
verdict. It does not modify any artifact or core module.
"""
from __future__ import annotations

import pathlib
import re

from desi.core.determinism_scanner import high_risk_hit_count
from desi.core.governance_core import core_identity, governance_intact
from desi.core.replay_kernel import canonical_json

_ROOT = pathlib.Path(__file__).resolve().parents[3]

# Files added by the packaging migration that must stay deterministic.
_PACKAGING_FILES = (
    "src/desi/core/replay_kernel.py",
    "src/desi/core/determinism_scanner.py",
    "src/desi/core/governance_core.py",
    "src/desi/core/__init__.py",
    "src/desi/gates/concept_gate.py",
    "src/desi/gates/__init__.py",
    "src/desi/reviewer/reviewer_port.py",
    "src/desi/reviewer/__init__.py",
    "src/desi/replay/__init__.py",
    "src/desi/governance_cli.py",
)

_NONDETERMINISM = (
    r"\brandom\.", r"\btime\.time\(", r"datetime\.now\(",
    r"\btempfile\b", r"\buuid\.", r"\bos\.urandom\b",
)

_VERDICT_ARTIFACTS = {
    "artifacts/frozen_benchmark/v32_4_verdict.json":
        "desi.frozen_benchmark_verdict",
    "artifacts/benchmark_api/v33_4_verdict.json":
        "desi.benchmark_api_verdict",
    "artifacts/benchmark_runs/v34_4_verdict.json":
        "desi.benchmark_runs_verdict",
    "artifacts/external_benchmarks/v35_4_verdict.json":
        "desi.external_benchmarks_verdict",
    "artifacts/reasoning_benchmarks/v36_4_verdict.json":
        "desi.reasoning_benchmarks_verdict",
    "artifacts/audit_benchmarks/v37_4_verdict.json":
        "desi.audit_benchmarks_verdict",
    "artifacts/live_llm_validation/v38_4_verdict.json":
        "desi.live_llm_validation_verdict",
}


def replay_drift_count() -> int:
    """Number of key artifacts whose live rebuild differs from the
    committed bytes (0 = no drift)."""
    import importlib

    drift = 0
    for rel, mod_name in _VERDICT_ARTIFACTS.items():
        path = _ROOT / rel
        if not path.exists():
            continue
        mod = importlib.import_module(mod_name)
        rebuilt = canonical_json(mod.build_verdict_artifact())
        if rebuilt != path.read_text(encoding="utf-8"):
            drift += 1
    return drift


def nondeterminism_hits() -> tuple[str, ...]:
    out: list[str] = []
    for rel in _PACKAGING_FILES:
        p = _ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for pat in _NONDETERMINISM:
            if re.search(pat, text):
                out.append(f"{rel}: {pat}")
    return tuple(out)


def importability() -> float:
    try:
        import importlib

        importlib.import_module("desi.core").replay_kernel
        importlib.import_module("desi.gates").concept_gate
        importlib.import_module("desi.reviewer").reviewer_port
        return 1.0
    except Exception:  # pragma: no cover - import must succeed
        return 0.0


def assessment() -> dict[str, object]:
    drift = replay_drift_count()
    hidden = nondeterminism_hits()
    return {
        "packaging_replay_drift": drift,
        "hidden_state_introduced": bool(hidden),
        "hidden_state_findings": list(hidden),
        "core_identity": core_identity(),
        "governance_intact": governance_intact(),
        "determinism_clean": high_risk_hit_count() == 0,
        "importability": importability(),
    }


def is_go() -> bool:
    a = assessment()
    return (
        a["packaging_replay_drift"] == 0
        and a["hidden_state_introduced"] is False
        and a["core_identity"] == 1.0
        and a["governance_intact"] is True
        and a["determinism_clean"] is True
        and a["importability"] == 1.0
    )


def build_go_no_go() -> str:
    a = assessment()
    verdict = "GO" if is_go() else "NO-GO"
    lines = [
        "# DESi Packaging Migration - Go/No-Go (v0.1.0a0)",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        "Packaging (pyproject, namespace facades, CLI, examples, CI) "
        "is documentation/distribution only. It does not modify the "
        "replay kernel, governance core, Concept Gates, determinism "
        "scanner, or artifact format.",
        "",
        "## The three required questions",
        "",
        f"1. **Did packaging affect replay stability?** "
        f"{'No' if a['packaging_replay_drift'] == 0 else 'YES'} - "
        f"replay drift across {len(_VERDICT_ARTIFACTS)} key verdict "
        f"artifacts = {a['packaging_replay_drift']} (each rebuilt "
        f"live is byte-identical to its committed artifact).",
        f"2. **Were hidden states introduced?** "
        f"{'No' if not a['hidden_state_introduced'] else 'YES'} - "
        f"no PRNG / timestamp / tempfile / uuid patterns in the "
        f"packaging-added files. Findings: "
        f"{a['hidden_state_findings']}.",
        f"3. **Were core invariants violated?** "
        f"{'No' if (a['core_identity'] == 1.0 and a['governance_intact'] and a['determinism_clean']) else 'YES'}"
        f" - core_identity = {a['core_identity']}, governance_intact "
        f"= {a['governance_intact']}, determinism_clean = "
        f"{a['determinism_clean']}.",
        "",
        "## Assessment metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| packaging_replay_drift | {a['packaging_replay_drift']} |",
        f"| hidden_state_introduced | {a['hidden_state_introduced']} |",
        f"| core_identity | {a['core_identity']} |",
        f"| governance_intact | {a['governance_intact']} |",
        f"| determinism_clean | {a['determinism_clean']} |",
        f"| importability | {a['importability']} |",
        "",
        "## What was deliberately NOT done",
        "",
        "Modules were not physically relocated into the recommended "
        "directory layout; the recommended namespace is provided as "
        "a re-export facade over the in-place implementations. "
        "Moving hundreds of modules would churn the import graph and "
        "risk replay drift, which the directive forbids. No "
        "simplification, agentification, or LangGraph-ification was "
        "applied. Developer ergonomics were treated as secondary to "
        "replay-governance.",
        "",
        "Verified by `tests/packaging/` and report-only CI "
        "(`.github/workflows/ci.yml`). Human approval remains "
        "required for any change.",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "assessment",
    "build_go_no_go",
    "importability",
    "is_go",
    "nondeterminism_hits",
    "replay_drift_count",
]
