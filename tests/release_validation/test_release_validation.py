"""Final release-validation audit tests.

Verifies the audit is hard and honest: it returns MAIN_BRANCH_NOT_READY
with the real remaining blockers, confirms the two safe fixes were
applied, and never claims DESi approved itself.
"""
from __future__ import annotations

import pathlib

from desi.release_validation import (
    VERDICT_NOT_READY, all_documents, blockers, phase1_clean_room,
    phase2_replay_integrity, phase4_examples, phase5_ci_integrity,
    resolved_during_audit, reviewer_attack_surface,
    undocumented_dependencies, verdict,
)

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_ART = _ROOT / "artifacts" / "release_validation"


# --- verdict is a hard NOT_READY ----------------
def test_verdict_is_not_ready() -> None:
    assert verdict() == VERDICT_NOT_READY
    assert len(blockers()) >= 1


def test_blockers_include_system_paper_and_divergence() -> None:
    bl = " | ".join(blockers())
    assert "System Paper v1.1" in bl
    assert "diverges" in bl


# --- safe fixes applied during the audit --------
def test_sympy_dependency_now_documented() -> None:
    assert undocumented_dependencies() == ()


def test_resolved_items_recorded() -> None:
    res = " ".join(resolved_during_audit()).lower()
    assert "sympy" in res
    assert "stale" in res


# --- phases that genuinely pass -----------------
def test_clean_room_imports_ok() -> None:
    p = phase1_clean_room()
    assert p["facade_imports_ok"] is True
    assert p["cli_complete"] is True


def test_replay_no_drift() -> None:
    p = phase2_replay_integrity()
    assert p["replay_drift"] == 0
    assert p["replay_stable"] is True
    assert p["uuid_artifacts_count"] == 0


def test_examples_present_and_clean() -> None:
    p = phase4_examples()
    assert p["all_present"] is True
    assert len(p["examples"]) == 4


def test_ci_report_only() -> None:
    p = phase5_ci_integrity()
    assert p["report_only"] is True
    assert p["no_auto_fix"] is True


# --- reviewer attack surface --------------------
def test_reviewer_attack_surface_ten_questions() -> None:
    qa = reviewer_attack_surface()
    assert len(qa) == 10
    for q, a in qa:
        assert q.strip() and a.strip()


# --- the seven artifacts ------------------------
def test_seven_artifacts_written() -> None:
    expected = {
        "clean_room_install.md", "replay_integrity.md",
        "readme_consistency.md", "example_execution.md",
        "ci_integrity.md", "reviewer_attack_surface.md",
        "main_branch_verdict.md",
    }
    for name in expected:
        assert (_ART / name).exists(), name


def test_artifacts_match_live_build() -> None:
    for name, text in all_documents().items():
        assert (_ART / name).read_text(encoding="utf-8") == text


def test_verdict_artifact_says_not_ready() -> None:
    doc = (_ART / "main_branch_verdict.md").read_text(encoding="utf-8")
    assert "MAIN_BRANCH_NOT_READY" in doc
    assert "did not approve itself" in doc
    assert "Human approval remains required" in doc


def test_no_almost_ready_release() -> None:
    # the actual verdict heading must be NOT_READY, never the
    # pass-verdict heading (referencing the target state in prose is
    # fine).
    doc = (_ART / "main_branch_verdict.md").read_text(encoding="utf-8")
    assert "## `MAIN_BRANCH_NOT_READY`" in doc
    assert "## `MAIN_BRANCH_READY`" not in doc
