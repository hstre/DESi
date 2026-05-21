"""v28.2 - Branch Generation & Patch Sandbox tests."""
from __future__ import annotations

import json
import pathlib

from desi.self_improvement import is_forbidden_target
from desi.self_improvement_branches import (
    all_valid, any_bypassed, branch_isolation, branches,
    build_branches_artifact, build_report,
    governance_preservation, merges_to_main, patches,
    regression_integrity, rejected_patch_attempts,
    replay_stability, unsafe_patch_attempt_count,
    unsafe_patch_rejection, validations,
)
from desi.self_improvement_branches.report import (
    REPORT_VERDICTS, VERDICT_CONTROLLED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "self_improvement"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- branch isolation (must be exactly 1.0) -----
def test_branch_isolation_full() -> None:
    assert branch_isolation() == 1.0


def test_no_branch_targets_main_or_auto_merges() -> None:
    assert merges_to_main() == ()
    for b in branches():
        assert b.is_isolated()
        assert b.name.startswith("proposal/")
        assert b.base == "sandbox"
        assert b.auto_merge is False
        assert b.targets_main is False
        assert b.name != "main"
        assert b.human_approval_required is True


# --- regression integrity -----------------------
def test_regression_integrity_full() -> None:
    assert regression_integrity() == 1.0
    assert any_bypassed() is False


# --- unsafe patch rejection ---------------------
def test_unsafe_patch_rejection_full() -> None:
    assert unsafe_patch_rejection() == 1.0
    assert unsafe_patch_attempt_count() >= 1
    assert len(rejected_patch_attempts()) == (
        unsafe_patch_attempt_count()
    )


def test_only_safe_patches_generated() -> None:
    for p in patches():
        assert p.is_safe
        assert not is_forbidden_target(p.target_area)


# --- governance preservation --------------------
def test_governance_preservation_full() -> None:
    assert governance_preservation() == 1.0


def test_all_branches_validate() -> None:
    assert all_valid() is True
    for v in validations():
        assert v.is_valid()
        assert v.replay_preserved
        assert v.governance_preserved
        assert v.regression_enforced


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        branch_isolation(), regression_integrity(),
        unsafe_patch_rejection(), governance_preservation(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_controlled() -> None:
    assert build_report().recommendation == VERDICT_CONTROLLED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v28_2_branches.json")
    assert art["schema_version"] == "v28_2_branch_sandbox"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v28_2_branches.json")
    disc = art["disclaimer"].lower()
    assert "never applied diffs" in disc
    assert "no branch targets main" in disc
    assert "human approval is mandatory" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v28_2_branches.json")
    required = {
        "branch_isolation", "regression_integrity",
        "unsafe_patch_rejection", "governance_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_no_merges_to_main() -> None:
    art = _load("v28_2_branches.json")
    assert art["merges_to_main"] == []
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v28_2_branches.json")
    live = build_branches_artifact()
    assert art == live
