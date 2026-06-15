"""Offline tests for the wrong-slice new-run pipeline.

Covers everything that does NOT need a model: case loading, the transparent
detectors, slice construction from frozen claims (matcher-gated), and freeze
determinism. Claim fixtures are built in-memory here — no run data is committed.
Stage A (extract) and Step 5 (run_arms) need a live key and are exercised only
in the Actions workflow.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
WS = HERE.parent.parent.parent / "experiments" / "wrong_slice"
sys.path.insert(0, str(WS))

import detectors  # noqa: E402
from case_schema import load_cases  # noqa: E402
from slice_builder import build_arms  # noqa: E402
from slice_matcher import match  # noqa: E402


# --- cases -----------------------------------------------------------------

def test_cases_load_and_validate():
    cases = load_cases()
    assert {"c1_pe_workup", "c2_sepsis_workup", "c3_incident_response"} <= set(cases)
    for c in cases.values():
        assert c.permuted_donor in cases
        assert c.plausible_donor in cases
        assert c.permuted_donor != c.case_id


# --- detectors -------------------------------------------------------------

def test_no_loop_flags_repetition():
    assert detectors.no_loop("Distinct one. Distinct two. Distinct three.")
    looped = "The pool is saturated. " * 4
    assert not detectors.no_loop(looped)


def test_task_completed_and_control_failure():
    assert detectors.task_completed("... NEXT STEP: order CTPA", ["NEXT STEP:"])
    assert not detectors.task_completed("no marker here", ["NEXT STEP:"])
    assert detectors.no_control_failure("safe answer", ["discharge the patient"])
    assert not detectors.no_control_failure("we should discharge the patient", ["discharge the patient"])


def test_role_adoption_detector():
    assert detectors.no_severe_role_adoption("clinical answer", ["as the relative"])
    assert not detectors.no_severe_role_adoption("ok, as the relative I demand...", ["as the relative"])


def test_score_returns_four_components():
    s = detectors.score("x.", "NEXT STEP: y", success_markers=["NEXT STEP:"],
                        forbidden_persona_markers=["as the relative"],
                        control_violation_markers=["discharge"])
    assert set(s) == {"no_loop", "task_completed", "no_severe_role_adoption", "no_control_failure"}
    assert all(s.values())


# --- slice construction from frozen claims ---------------------------------

def _write_frozen(dirp: Path, case_id: str, claims: list[dict]) -> None:
    payload = {"case_id": case_id, "claims": claims}
    (dirp / f"{case_id}.claims.json").write_text(json.dumps(payload), encoding="utf-8")


def _claims(words: list[str], status="supported", modality="evidence") -> list[dict]:
    return [{"subject": w, "predicate": "is", "object": "noted",
             "status": status, "modality": modality,
             "generated_by": "llm_semantic_projection", "evidence_refs": []}
            for w in words]


def test_build_arms_matched_and_audited(tmp_path):
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    audit = tmp_path / "audit.jsonl"
    # correct + two donors with enough claims to find a matched 3-subset
    _write_frozen(frozen, "cA", _claims(["alpha", "beta", "gamma"]))
    _write_frozen(frozen, "cB", _claims(["delta", "epsilon", "zeta", "eta", "theta"]))
    _write_frozen(frozen, "cC", _claims(["iota", "kappa", "lambda", "mu", "nu"]))
    arms = build_arms("cA", "assessment", "cB", "cC",
                      frozen_dir=frozen, audit_sink=audit)
    assert set(arms) == {"correct", "wrong_permuted", "wrong_plausible"}
    # wrong arms must each pass the matcher against correct
    correct = arms["correct"].slice
    for arm in ("wrong_permuted", "wrong_plausible"):
        assert arms[arm].matcher_ok is True
        assert match(correct, arms[arm].slice, token_tolerance=12).ok
        # and actually differ from correct
        assert arms[arm].slice_hash != arms["correct"].slice_hash
    # the audit recorded the admit decisions
    assert audit.exists() and audit.read_text().strip()


def test_build_arms_raises_when_donor_too_small(tmp_path):
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    audit = tmp_path / "audit.jsonl"
    _write_frozen(frozen, "cA", _claims(["alpha", "beta", "gamma"]))
    _write_frozen(frozen, "cB", _claims(["delta"]))  # too few to match 3
    with pytest.raises(ValueError):
        build_arms("cA", "assessment", "cB", "cB", frozen_dir=frozen, audit_sink=audit)
    # the failure was audited, not silent
    assert audit.exists() and "rejected" in audit.read_text()


def test_freeze_is_deterministic(tmp_path):
    # build a tiny frozen set and confirm two manifest builds are byte-identical
    import freeze as freeze_mod
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    # real donor graph requires equal counts; each claim renders to 3 tokens
    _write_frozen(frozen, "c1_pe_workup", _claims(["a1", "a2", "a3", "a4", "a5"]))
    _write_frozen(frozen, "c2_sepsis_workup", _claims(["b1", "b2", "b3", "b4", "b5"]))
    _write_frozen(frozen, "c3_incident_response", _claims(["c1", "c2", "c3", "c4", "c5"]))
    sink = frozen / "audit.jsonl"
    m1 = freeze_mod.build_manifest(frozen_dir=frozen, audit_sink=sink)
    m2 = freeze_mod.build_manifest(frozen_dir=frozen, audit_sink=sink)
    assert m1["manifest_hash"] == m2["manifest_hash"]
    assert set(m1["cases"]) == {"c1_pe_workup", "c2_sepsis_workup", "c3_incident_response"}
    for e in m1["cases"].values():
        assert set(e["arms"]) == {"raw", "correct", "wrong_permuted", "wrong_plausible"}
