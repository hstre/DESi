"""Tests for the deterministic decision/tradeoff recorder (offline)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "utility_evolution" / "decision_record"))

import decide as D  # noqa: E402

_OPTIONS = ["A", "B", "C"]
_CRITERIA = [{"name": "speed", "weight": 1.0, "higher_is_better": True},
             {"name": "cost", "weight": 1.0, "higher_is_better": False}]
_SCORES = {"A": {"speed": 0.9, "cost": 0.2}, "B": {"speed": 0.5, "cost": 0.1},
           "C": {"speed": 0.4, "cost": 0.9}}


def test_decide_is_replay_deterministic():
    a = D.decide(_OPTIONS, _CRITERIA, _SCORES)
    b = D.decide(_OPTIONS, _CRITERIA, _SCORES)
    assert a["replay_hash"] == b["replay_hash"]


def test_winner_is_top_weighted():
    rec = D.decide(_OPTIONS, _CRITERIA, _SCORES)
    # A: (0.9 + (1-0.2))/2 = 0.85 ; B: (0.5+0.9)/2=0.70 ; C: (0.4+0.1)/2=0.25
    assert rec["winner"] == "A"
    assert rec["ranking"][0]["score"] >= rec["ranking"][1]["score"]


def test_higher_is_better_false_inverts():
    rec = D.decide(["X", "Y"], [{"name": "cost", "weight": 1.0, "higher_is_better": False}],
                   {"X": {"cost": 0.1}, "Y": {"cost": 0.9}})
    assert rec["winner"] == "X"   # lower cost wins


def test_tradeoffs_list_where_runnerup_beats_winner():
    rec = D.decide(_OPTIONS, _CRITERIA, _SCORES)
    # runner-up B beats winner A on cost (0.1 < 0.2, lower better)
    assert any(t["criterion"] == "cost" for t in rec["tradeoffs"])


def test_format_record_renders():
    rec = D.decide(_OPTIONS, _CRITERIA, _SCORES)
    out = D.format_record(rec)
    assert "Recommended: A" in out and "replay_hash" in out
