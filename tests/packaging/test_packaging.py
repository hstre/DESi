"""Packaging tests: importability, facades, CLI, pyproject.

Verifies the recommended public import paths resolve, the facades
re-export the REAL in-place implementations (no divergence, nothing
faked), the CLI subcommands run, and pyproject is well-formed.
"""
from __future__ import annotations

import pathlib
import tomllib

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[2]


# --- required public imports (directive D) ------
def test_core_imports() -> None:
    from desi.core import (
        determinism_scanner, governance_core, replay_kernel,
    )
    assert replay_kernel.replay_hash({"a": 1})
    assert determinism_scanner.determinism_clean() is True
    assert governance_core.core_identity() == 1.0


def test_gates_import() -> None:
    from desi.gates import concept_gate
    assert "external_benchmarks" in concept_gate.registered_phases()


def test_reviewer_import() -> None:
    from desi.reviewer import reviewer_port
    assert "desi.scientific_reviewers" in reviewer_port.IMPLEMENTED_BY


def test_replay_import() -> None:
    from desi.replay import (  # noqa: F401
        DeterministicCache, replay_stability,
    )


# --- facades re-export REAL objects (no fakes) --
def test_replay_kernel_reexports_real_hash() -> None:
    from desi.core.replay_kernel import content_hash
    from desi.external_benchmarks.dataset_hashing import (
        content_hash as real,
    )
    assert content_hash is real


def test_determinism_scanner_reexports_real() -> None:
    from desi.core.determinism_scanner import high_risk_hit_count
    from desi.determinism_root_cause.containers import (
        high_risk_hit_count as real,
    )
    assert high_risk_hit_count is real


def test_governance_core_reexports_real() -> None:
    from desi.core.governance_core import PROTECTED_CORE, core_identity
    from desi.peripheral_mutation import (
        PROTECTED_CORE as real_pc, core_identity as real_ci,
    )
    assert PROTECTED_CORE is real_pc
    assert core_identity is real_ci


def test_reviewer_port_maps_to_real_subsystems() -> None:
    from desi.reviewer.reviewer_port import build_claim_audit_artifact
    from desi.readme_self_review import (
        build_claim_audit_artifact as real,
    )
    assert build_claim_audit_artifact is real


# --- CLI ----------------------------------------
@pytest.mark.parametrize("cmd", ["replay", "benchmark", "review"])
def test_cli_subcommands_run(cmd: str) -> None:
    from desi.governance_cli import main
    assert main([cmd]) == 0


def test_cli_replay_reports_stable() -> None:
    from desi.governance_cli import main
    # replay subcommand returns 0 only when stable + clean + core 1.0
    assert main(["replay"]) == 0


def test_cli_parser_has_core_subcommands() -> None:
    from desi.governance_cli import _DISPATCH
    # the four core subcommands plus the dummy-install helpers
    assert {"replay", "audit", "benchmark", "review"}.issubset(
        set(_DISPATCH))
    assert {"config", "doctor"}.issubset(set(_DISPATCH))


# --- pyproject ----------------------------------
def test_pyproject_valid_and_alpha() -> None:
    data = tomllib.loads(
        (_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
    )
    proj = data["project"]
    assert proj["name"] == "desi-governance"
    assert proj["version"] == "0.1.0a0"  # alpha, not v1.0
    assert proj["requires-python"] == ">=3.11"
    assert "desi" in data["project"]["scripts"]


def test_pyproject_no_heavy_frameworks() -> None:
    data = tomllib.loads(
        (_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
    )
    deps = " ".join(data["project"]["dependencies"]).lower()
    for heavy in ("langgraph", "langchain", "autogen", "crewai",
                  "torch", "tensorflow"):
        assert heavy not in deps


def test_license_and_manifest_present() -> None:
    assert (_ROOT / "LICENSE").exists()
    assert (_ROOT / "MANIFEST.in").exists()
    assert (_ROOT / "CHANGELOG.md").exists()


def test_examples_present() -> None:
    for name in (
        "replay_example.py", "concept_gate_example.py",
        "reviewer_port_example.py", "live_llm_example.py",
    ):
        assert (_ROOT / "examples" / name).exists()


def test_ci_workflow_is_report_only() -> None:
    ci = (_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8",
    )
    assert "NEVER auto-fixes" in ci
    # no auto-commit / push / format-write steps
    assert "git commit" not in ci
    assert "git push" not in ci
