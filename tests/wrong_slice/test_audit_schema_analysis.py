"""Tests for the wrong-slice audit sink, result schema, and paired analysis.

These exercise the *logic* on tiny hand-built fixtures. The fixtures are unit
inputs, NOT experimental results — no run data is committed anywhere.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "experiments" / "wrong_slice"))

from analysis import mcnemar_exact_p, paired_contrast, run_paired_analysis  # noqa: E402
from audit import admit_or_audit  # noqa: E402
from result_schema import ARMS, RunResult, validate_record  # noqa: E402
from slice_matcher import Claim, Slice  # noqa: E402


def _claim(text: str, pid: str) -> Claim:
    return Claim(text, {"validity": "v", "role": "r"}, {"src": "d", "pass_id": pid})


def _correct() -> Slice:
    return Slice([_claim("a b c", "p1"), _claim("d e f", "p1")], pass_id="p1")


def _matched_wrong() -> Slice:
    return Slice([_claim("g h i", "p2"), _claim("j k l", "p2")], pass_id="p2")


# --- audit -----------------------------------------------------------------

def test_audit_records_reject_and_admit(tmp_path):
    sink = tmp_path / "audit.jsonl"
    # admit: matched
    ok, _ = admit_or_audit(_correct(), _matched_wrong(), sink)
    assert ok
    # reject: extra claim -> claim_count fails
    bad = _matched_wrong()
    bad.claims.append(_claim("m n o", "p2"))
    ok2, rep = admit_or_audit(_correct(), bad, sink)
    assert not ok2
    lines = [json.loads(x) for x in sink.read_text().splitlines()]
    assert len(lines) == 2
    decisions = [e["decision"] for e in lines]
    assert decisions == ["admitted", "rejected"]
    assert "claim_count" in lines[1]["failed_criteria"]


def test_audit_only_rejected_when_flag_off(tmp_path):
    sink = tmp_path / "audit.jsonl"
    admit_or_audit(_correct(), _matched_wrong(), sink, audit_admitted=False)
    assert not sink.exists() or sink.read_text() == ""


# --- result schema ---------------------------------------------------------

def _run(arm: str, admissible: bool, case="c1", rep=0, seed=1, matcher_ok=None) -> RunResult:
    comp = dict(
        no_loop=admissible,
        task_completed=admissible,
        no_severe_role_adoption=admissible,
        no_control_failure=admissible,
    )
    return RunResult(
        experiment_id="exp1", prereg_hash="deadbeef", case_id=case, arm=arm,
        repetition=rep, seed=seed, provider="groq", model_id="llama-3.1-8b",
        decoding={"temperature": 0.0}, slice_hash="" if arm == "raw" else "h",
        matcher_ok=matcher_ok, **comp,
    )


def test_admissible_property():
    assert _run("correct", True).admissible
    r = _run("correct", True)
    r.no_loop = False
    assert not r.admissible


def test_roundtrip_record():
    r = _run("wrong_permuted", True, matcher_ok=True)
    rec = r.to_record()
    assert rec["admissible"] is True
    back = RunResult.from_record(rec)
    assert back.arm == "wrong_permuted"
    assert back.admissible is True


def test_validate_flags_bad_arm_and_matcher():
    rec = _run("correct", True).to_record()
    rec["arm"] = "bogus"
    assert any("arm not in" in p for p in validate_record(rec))
    # wrong arm without matcher_ok=True must be flagged
    rec2 = _run("wrong_permuted", True, matcher_ok=None).to_record()
    assert any("requires matcher_ok=True" in p for p in validate_record(rec2))


def test_validate_raw_needs_empty_slice_hash():
    rec = _run("raw", True).to_record()
    rec["slice_hash"] = "x"
    assert any("raw arm must have empty slice_hash" in p for p in validate_record(rec))


def test_arms_constant():
    assert ARMS == ("raw", "correct", "wrong_permuted", "wrong_plausible")


# --- analysis --------------------------------------------------------------

def test_mcnemar_helper():
    assert mcnemar_exact_p(0, 0) == 1.0
    assert mcnemar_exact_p(5, 5) == 1.0
    assert mcnemar_exact_p(12, 0) < 0.01


def test_empty_is_insufficient_not_fabricated():
    out = run_paired_analysis([], delta=0.1)
    assert out["verdict"] == "insufficient_data"


def test_paired_contrast_counts_discordances():
    # 4 paired (case,rep,seed) cells; correct always admissible, wrong never
    results = []
    for i in range(4):
        results.append(_run("correct", True, case="c", rep=i, seed=i))
        results.append(_run("wrong_permuted", False, case="c", rep=i, seed=i, matcher_ok=True))
    ct = paired_contrast(results, "correct", "wrong_permuted")
    assert ct["n_pairs"] == 4
    assert ct["incidence_a"] == 0.0     # correct never degenerates
    assert ct["incidence_b"] == 1.0     # wrong always degenerates
    # correct (arm_a) is better in every pair; wrong (arm_b) never is
    assert ct["discordant_a_better"] == 4
    assert ct["discordant_b_better"] == 0


def test_decision_H1_when_correct_beats_wrong():
    results = []
    for i in range(10):
        results.append(_run("correct", True, case="c", rep=i, seed=i))
        results.append(_run("wrong_permuted", False, case="c", rep=i, seed=i, matcher_ok=True))
    out = run_paired_analysis(results, delta=0.1)
    assert out["decisions"]["wrong_permuted"]["verdict"] == "H1_selection_real"


def test_decision_H0_shrink_when_equal():
    # correct and wrong identical outcomes -> no difference -> H0 shrink
    results = []
    for i in range(8):
        results.append(_run("correct", True, case="c", rep=i, seed=i))
        results.append(_run("wrong_permuted", True, case="c", rep=i, seed=i, matcher_ok=True))
    out = run_paired_analysis(results, delta=0.1)
    assert out["decisions"]["wrong_permuted"]["verdict"] == "H0_shrink_to_context_selection"


def test_integration_end_to_end(tmp_path):
    import integration

    correct = _correct()
    cand = _matched_wrong()
    sink = tmp_path / "audit.jsonl"
    ok, _ = integration.admit_wrong_slice(correct, cand, sink)
    assert ok
    assert len(integration.prereg_hash()) == 64  # sha-256 hex of frozen prereg

    results = []
    for i in range(6):
        results.append(integration.record(
            experiment_id="e", case_id="c", arm="correct", repetition=i, seed=i,
            provider="groq", model_id="llama-3.1-8b", decoding={"temperature": 0.0},
            fed_slice=correct, matcher_ok=None,
            no_loop=True, task_completed=True,
            no_severe_role_adoption=True, no_control_failure=True))
        results.append(integration.record(
            experiment_id="e", case_id="c", arm="wrong_permuted", repetition=i, seed=i,
            provider="groq", model_id="llama-3.1-8b", decoding={"temperature": 0.0},
            fed_slice=cand, matcher_ok=True,
            no_loop=False, task_completed=False,
            no_severe_role_adoption=True, no_control_failure=True))
    out = integration.analyse(results, delta=0.1)
    assert out["decisions"]["wrong_permuted"]["verdict"] == "H1_selection_real"


def test_integration_record_rejects_invalid():
    import integration
    # wrong arm with matcher_ok=None must be rejected by the schema validator
    try:
        integration.record(
            experiment_id="e", case_id="c", arm="wrong_permuted", repetition=0, seed=0,
            provider="groq", model_id="m", decoding={}, fed_slice=_matched_wrong(),
            matcher_ok=None, no_loop=True, task_completed=True,
            no_severe_role_adoption=True, no_control_failure=True)
    except ValueError as e:
        assert "matcher_ok=True" in str(e)
    else:
        raise AssertionError("expected ValueError for invalid record")


def test_decision_H2_when_wrong_worse():
    # wrong degenerates, correct does not, but we ask: is wrong worse than correct?
    # H2 is "matched wrong WORSE than correct" -> diff (wrong-correct) negative means
    # correct better; H2 triggers when correct is worse. Build correct worse:
    results = []
    for i in range(10):
        results.append(_run("correct", False, case="c", rep=i, seed=i))
        results.append(_run("wrong_permuted", True, case="c", rep=i, seed=i, matcher_ok=True))
    out = run_paired_analysis(results, delta=0.1)
    assert out["decisions"]["wrong_permuted"]["verdict"] == "H2_wrong_structure_harmful"
