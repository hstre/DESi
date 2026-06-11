"""Pins the confidence-discrimination metric: the precondition for escalation.

The pipeline escalates on low/unknown confidence. That gate only earns its cost
if those buckets are genuinely less accurate, so ``discrimination`` (in
ab_evidence/confidence_calibration.py) must report a positive separation when
the heuristic actually tracks correctness — and must NOT be fooled into claiming
signal when it doesn't.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "ab_evidence"))

from confidence_calibration import discrimination  # noqa: E402


def test_perfect_heuristic_has_full_separation():
    # every 'low' answer wrong, every 'high' answer correct
    d = discrimination({"high": [1.0, 1.0, 1.0], "low": [0.0, 0.0]})
    assert d["p_correct_keep"] == 1.0
    assert d["p_correct_escalate"] == 0.0
    assert d["separation"] == 1.0
    assert d["trigger_rate"] == round(2 / 5, 4)
    assert d["confusion"] == {
        "escalate_and_wrong": 2, "escalate_and_correct": 0,
        "keep_and_wrong": 0, "keep_and_correct": 3,
    }


def test_useless_heuristic_has_zero_separation():
    # same accuracy in both groups -> escalation fires on noise
    d = discrimination({"high": [1.0, 0.0], "low": [1.0, 0.0]})
    assert d["separation"] == 0.0


def test_inverted_heuristic_is_negative():
    # 'low' answers are actually the *correct* ones -> gate is inverted
    d = discrimination({"high": [0.0, 0.0], "low": [1.0, 1.0]})
    assert d["separation"] == -1.0


def test_unknown_counts_as_escalate_bucket():
    # the pipeline escalates on ("low", "unknown"); both must land in escalate
    d = discrimination({"high": [1.0], "unknown": [0.0], "low": [0.0]})
    assert d["n_escalate"] == 2 and d["n_keep"] == 1
    assert d["p_correct_escalate"] == 0.0


def test_medium_counts_as_keep_bucket():
    d = discrimination({"medium": [1.0, 1.0], "low": [0.0]})
    assert d["n_keep"] == 2 and d["n_escalate"] == 1


def test_empty_groups_yield_none_not_crash():
    d = discrimination({"high": [1.0]})           # no escalate runs at all
    assert d["p_correct_escalate"] is None
    assert d["separation"] is None
    assert d["trigger_rate"] == 0.0
    d2 = discrimination({})                        # nothing at all
    assert d2["n_total"] == 0 and d2["trigger_rate"] == 0.0


def test_partial_credit_scores_are_averaged_for_p_correct():
    # p_correct is a mean of scores; confusion uses the >=1.0 correctness cut
    d = discrimination({"high": [0.5, 1.0], "low": [0.5]})
    assert d["p_correct_keep"] == 0.75
    assert d["confusion"]["keep_and_correct"] == 1   # only the 1.0
    assert d["confusion"]["keep_and_wrong"] == 1     # the 0.5 is "not correct"
