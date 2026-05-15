"""Tests for v2.8 phase runners (Aufgabe 3)."""
from __future__ import annotations

import pathlib

import pytest

from desi.rule_patch_protocol import (
    GuardDescriptor,
    PatchCandidate,
    PatchPhase,
    causal_chain_v2_7_candidate,
    compute_benchmark_hashes,
    fake_rule_without_guards_candidate,
    run_discovery,
    run_guard_synthesis,
    run_implementation,
    run_regression,
    run_replay_verification,
    run_risk_probe,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_ARTIFACT_ROOT = _REPO_ROOT / "artifacts"


# ---------------------------------------------------------------------------
# DISCOVERY
# ---------------------------------------------------------------------------


def test_discovery_passes_when_artefacts_present() -> None:
    c = causal_chain_v2_7_candidate()
    out = run_discovery(c, artifact_root=_ARTIFACT_ROOT)
    assert out.passed is True
    assert out.phase is PatchPhase.DISCOVERY
    assert "artefact_hashes" in out.data
    assert set(out.data["artefact_hashes"].keys()) == set(c.required_artifacts)


def test_discovery_fails_when_artefact_missing(tmp_path: pathlib.Path) -> None:
    c = PatchCandidate(
        name="x", target_rule="x", source_branch="b",
        required_artifacts=("does_not_exist.json",),
    )
    out = run_discovery(c, artifact_root=tmp_path)
    assert out.passed is False
    assert "missing" in out.reason


# ---------------------------------------------------------------------------
# RISK_PROBE
# ---------------------------------------------------------------------------


def test_risk_probe_passes_on_real_v26_artefact() -> None:
    c = causal_chain_v2_7_candidate()
    out = run_risk_probe(c, artifact_root=_ARTIFACT_ROOT)
    assert out.passed is True
    assert out.data.get("safe_to_implement") is True


def test_risk_probe_fails_when_v26_missing(tmp_path: pathlib.Path) -> None:
    c = causal_chain_v2_7_candidate()
    out = run_risk_probe(c, artifact_root=tmp_path)
    assert out.passed is False
    assert "missing" in out.reason


# ---------------------------------------------------------------------------
# GUARD_SYNTHESIS
# ---------------------------------------------------------------------------


def test_guard_synthesis_passes_on_v27_candidate() -> None:
    out = run_guard_synthesis(causal_chain_v2_7_candidate())
    assert out.passed is True
    assert out.data["guard_names"]


def test_guard_synthesis_fails_on_empty_guards() -> None:
    out = run_guard_synthesis(fake_rule_without_guards_candidate())
    assert out.passed is False
    assert out.reason.startswith("missing_guards")


def test_guard_synthesis_rejects_case_id_observable() -> None:
    c = PatchCandidate(
        name="bad", target_rule="bad", source_branch="b",
        guards=(
            GuardDescriptor("g1", "case_id_check", "x"),
            GuardDescriptor("g2", "premise_kind", "x"),
        ),
    )
    out = run_guard_synthesis(c)
    assert out.passed is False
    assert "case_id" in out.reason


def test_guard_synthesis_rejects_allowlist_observable() -> None:
    c = PatchCandidate(
        name="bad", target_rule="bad", source_branch="b",
        guards=(
            GuardDescriptor("g1", "allowlist_check", "x"),
            GuardDescriptor("g2", "premise_kind", "x"),
        ),
    )
    out = run_guard_synthesis(c)
    assert out.passed is False
    assert "allowlist" in out.reason


def test_guard_synthesis_rejects_unknown_observable() -> None:
    c = PatchCandidate(
        name="bad", target_rule="bad", source_branch="b",
        guards=(
            GuardDescriptor("g1", "horoscope", "x"),
            GuardDescriptor("g2", "premise_kind", "x"),
        ),
    )
    out = run_guard_synthesis(c)
    assert out.passed is False
    assert "ALLOWED_OBSERVABLES" in out.reason


# ---------------------------------------------------------------------------
# IMPLEMENTATION
# ---------------------------------------------------------------------------


def test_implementation_passes_on_real_v27_files() -> None:
    out = run_implementation(
        causal_chain_v2_7_candidate(), repo_root=_REPO_ROOT,
    )
    assert out.passed is True


def test_implementation_fails_on_unknown_file() -> None:
    c = PatchCandidate(
        name="x", target_rule="x", source_branch="b",
        touched_files=("src/desi/forbidden/file.py",),
    )
    out = run_implementation(c, repo_root=_REPO_ROOT)
    assert out.passed is False


# ---------------------------------------------------------------------------
# REGRESSION
# ---------------------------------------------------------------------------


def test_regression_baseline_captures_six_hashes() -> None:
    out = run_regression(causal_chain_v2_7_candidate())
    assert out.passed is True
    hashes = out.data["hashes"]
    for key in (
        "v1_5_main", "v1_9_tool", "v2_3_multistep",
        "v2_4_bridge_audit", "v2_5_rule_audit", "v2_6_causal_probe",
    ):
        assert key in hashes


def test_regression_against_matching_expected_passes() -> None:
    baseline = compute_benchmark_hashes()
    out = run_regression(
        causal_chain_v2_7_candidate(),
        expected_hashes=baseline,
    )
    assert out.passed is True


def test_regression_against_wrong_expected_fails() -> None:
    bad = {
        "v1_5_main": "deadbeefdeadbeef",
        "v1_9_tool": "deadbeefdeadbeef",
        "v2_3_multistep": "deadbeefdeadbeef",
        "v2_4_bridge_audit": "deadbeefdeadbeef",
        "v2_5_rule_audit": "deadbeefdeadbeef",
        "v2_6_causal_probe": "deadbeefdeadbeef",
    }
    out = run_regression(
        causal_chain_v2_7_candidate(),
        expected_hashes=bad,
    )
    assert out.passed is False
    assert "v1_5_main" in out.reason


# ---------------------------------------------------------------------------
# REPLAY_VERIFICATION
# ---------------------------------------------------------------------------


def test_replay_verification_passes() -> None:
    out = run_replay_verification(causal_chain_v2_7_candidate())
    assert out.passed is True
