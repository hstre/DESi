"""Replay-drift regression for the packaging migration.

Proves that adding packaging (pyproject, namespace facades, CLI,
examples, CI) introduced NO replay drift: every key verdict artifact,
rebuilt live, is byte-identical to the committed artifact, the
determinism scanner stays clean, and core identity / replay stability
remain 1.0.
"""
from __future__ import annotations

import pathlib

from desi.core.replay_kernel import canonical_json
from desi.core.determinism_scanner import high_risk_hit_count
from desi.core.governance_core import core_identity, governance_intact

_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _verdict_builders():
    from desi.frozen_benchmark_verdict import (
        build_verdict_artifact as v32,
    )
    from desi.benchmark_api_verdict import (
        build_verdict_artifact as v33,
    )
    from desi.benchmark_runs_verdict import (
        build_verdict_artifact as v34,
    )
    from desi.external_benchmarks_verdict import (
        build_verdict_artifact as v35,
    )
    from desi.reasoning_benchmarks_verdict import (
        build_verdict_artifact as v36,
    )
    from desi.audit_benchmarks_verdict import (
        build_verdict_artifact as v37,
    )
    from desi.live_llm_validation_verdict import (
        build_verdict_artifact as v38,
    )
    return {
        "artifacts/frozen_benchmark/v32_4_verdict.json": v32,
        "artifacts/benchmark_api/v33_4_verdict.json": v33,
        "artifacts/benchmark_runs/v34_4_verdict.json": v34,
        "artifacts/external_benchmarks/v35_4_verdict.json": v35,
        "artifacts/reasoning_benchmarks/v36_4_verdict.json": v36,
        "artifacts/audit_benchmarks/v37_4_verdict.json": v37,
        "artifacts/live_llm_validation/v38_4_verdict.json": v38,
    }


def test_no_artifact_drift_after_packaging() -> None:
    for rel, builder in _verdict_builders().items():
        committed = (_ROOT / rel).read_text(encoding="utf-8")
        rebuilt = canonical_json(builder())
        assert rebuilt == committed, f"replay drift in {rel}"


def test_determinism_scanner_clean() -> None:
    assert high_risk_hit_count() == 0


def test_core_identity_intact() -> None:
    assert core_identity() == 1.0
    assert governance_intact() is True


def test_replay_stability_across_phases() -> None:
    from desi.external_benchmarks_verdict import (
        replay_stability as r35,
    )
    from desi.live_llm_validation_verdict import (
        replay_stability as r38,
    )
    assert r35() == 1.0
    assert r38() == 1.0


def test_canonical_json_matches_repo_format() -> None:
    # the facade serialization equals the format committed artifacts
    # were written with (indent=2, sort_keys=True, trailing newline)
    obj = {"b": 2, "a": 1}
    assert canonical_json(obj) == '{\n  "a": 1,\n  "b": 2\n}\n'
