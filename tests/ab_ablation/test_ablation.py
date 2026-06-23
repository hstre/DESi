"""Regression tests for the falsification-oriented A/B/C/D ablation extension.

Pins the four guarantees the brief requires:
  1. the wrong-slice condition really receives another case's slice (and almost none of the true
     info), while the normal-DESi slice carries the true info;
  2. the status-stripped condition contains the claim TEXT but none of the governance metadata
     (category keys, typed ids, evidence/claim_ids fields);
  3. the degeneration metrics count known loop / contradiction / invalid-reuse / bad-framing /
     coherence-without-continuity examples the way their definitions say;
  4. the benchmark output contains all four conditions, end to end.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "ab_evidence"))

from ablation_conditions import WRONG_SLICE_DONOR, build_condition, status_strip  # noqa: E402
from ablation_run import CONDITIONS, _info_recall, _slice_bodies, _true_bodies, run  # noqa: E402
from build_state import load_ground_truth, state_for_variant_B  # noqa: E402
from degeneration import (  # noqa: E402
    bad_framing_nonrecovery,
    coherence_without_continuity,
    contradiction_persistence,
    invalid_claim_reuse,
    loop_trap,
)

CASE = "case1_architecture"


# --- 1. wrong-slice really receives the wrong slice ---------------------------------------------
def test_wrong_slice_receives_another_cases_slice():
    donor = WRONG_SLICE_DONOR[CASE]
    c = build_condition(CASE, "C_wrong_slice")
    assert c["slice_source"] == donor and donor != CASE
    # the injected slice carries (almost) NONE of this case's true ground truth ...
    assert _info_recall(_slice_bodies(CASE, "C_wrong_slice"), _true_bodies(CASE)) <= 0.1
    # ... whereas the normal-DESi slice carries (almost) all of it
    assert _info_recall(_slice_bodies(CASE, "B_normal_desi"), _true_bodies(CASE)) >= 0.9
    # and it is the DONOR's information that was injected
    assert _info_recall(_slice_bodies(CASE, "C_wrong_slice"), _true_bodies(donor)) >= 0.9


# --- 2. status-stripped keeps claim text, drops governance metadata -----------------------------
def test_status_stripped_keeps_text_drops_governance():
    d = build_condition(CASE, "D_status_stripped")
    user = d["messages"][0]["content"]
    gt = load_ground_truth(CASE)
    every = (gt["active_claims"] + gt["active_constraints"] + gt["decisions"]
             + gt["open_conflicts"] + gt["open_questions"])
    # claim TEXT is preserved verbatim ...
    for e in every:
        assert e["what"] in user
    # ... but the governance metadata (as it appears in the JSON state) is gone
    for token in ('"active_claims"', '"active_constraints"', '"decisions"', '"open_conflicts"',
                  '"open_questions"', '"what"', '"id"', '"evidence"', '"claim_ids"'):
        assert token not in user
    for e in every:
        assert f'"{e["id"]}"' not in user          # typed ids (C1/R1/D1/K1/Q1) are not present
    # sanity: the normal-DESi slice DOES carry that governance metadata
    b_user = build_condition(CASE, "B_normal_desi")["messages"][0]["content"]
    assert '"what"' in b_user and '"active_claims"' in b_user
    # status_strip preserves order + count of bodies
    assert status_strip(state_for_variant_B(CASE)) == [e["what"] for e in every]


# --- 3. degeneration metrics count known examples -----------------------------------------------
def test_loop_trap_detects_repetition_not_variety():
    looping = "\n".join(["- the cache must be invalidated on every write"] * 4)
    varied = ("- use schema per tenant in a shared database\n"
              "- legal must weigh in on the deletion policy\n"
              "- invalidate the cache on write")
    assert loop_trap(looping)["loop_trapped"] is True
    assert loop_trap(varied)["loop_trapped"] is False


def test_invalid_reuse_and_bad_framing_nonrecovery():
    wrong = ["per-tenant database is operationally too heavy at our scale"]
    true = ["use schema-per-tenant in a shared database (not per-tenant DB)"]
    parrots_wrong = "- per-tenant database is operationally too heavy at our scale"
    assert invalid_claim_reuse(parrots_wrong, wrong)["reused"] >= 1
    assert bad_framing_nonrecovery(parrots_wrong, wrong, true)["nonrecovered"] is True
    recovered = "- use schema-per-tenant in a shared database, not a per-tenant DB"
    assert bad_framing_nonrecovery(recovered, wrong, true)["nonrecovered"] is False


def test_contradiction_persistence_and_coherence_without_continuity():
    conflicts = [{"id": "K1", "what": ("tenant-deletion: GDPR hard delete within 30 days vs "
                                       "operations prefers soft delete")}]
    settled = "- tenant deletion uses GDPR hard delete within 30 days"   # one side, no open cue
    assert contradiction_persistence(settled, conflicts)["persistence_count"] == 1
    surfaced = ("- open conflict: GDPR hard delete within 30 days vs operations soft delete")
    assert contradiction_persistence(surfaced, conflicts)["persistence_count"] == 0
    fluent = "\n".join(
        f"- this is a perfectly well formed sentence number {i} that nonetheless says nothing"
        for i in range(6))
    assert coherence_without_continuity(fluent, true_recall=0.1)["coherence_without_continuity"]
    assert not coherence_without_continuity(fluent, true_recall=0.9)["coherence_without_continuity"]


# --- 4. benchmark output includes all four conditions -------------------------------------------
def test_run_output_includes_all_four_conditions():
    def stub(system, messages):
        return {"text": "- none"}

    out = run((CASE,), responder=stub, tag="selftest")
    assert out["backend_status"] == "STUB_TEST"
    conds = out["cases"][0]["conditions"]
    assert set(conds) == set(CONDITIONS)
    for c in CONDITIONS:
        assert "evaluation" in conds[c] and "degeneration" in conds[c]
