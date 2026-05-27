"""Targeted tests for the DESi context-compression demo (offline, deterministic)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

import context_compression_demo as ccd  # noqa: E402

_V1_SUMMARY = {
    "turns": 11, "constraint_half_life_mean": 0.9, "max_constraint_decay": 0.2,
    "unrecovered_constraints": 1, "rhetorical_recovery_count": 3,
    "operational_recovery_count": 1, "failed_recovery_count": 1,
    "recovery_quality_proxy": 0.2, "branch_entropy_proxy": 0.8,
    "branch_collapse_events": 1, "cumulative_drift_energy": 3.4,
    "composite_drift_v1": 0.21,
    "drift_event_ledger": [{"turn": 1, "events": ["new_constraint_loss", "banned_move_incursion"]},
                           {"turn": 3, "events": ["constraint_recovery"]}],
}


def test_token_count_positive_and_deterministic():
    t1 = ccd.token_count("a controlled longitudinal study of community solar enrollment")
    t2 = ccd.token_count("a controlled longitudinal study of community solar enrollment")
    assert t1 == t2 and t1 > 0
    assert ccd.token_count("") == 0


def test_state_summary_far_smaller_than_transcript():
    long_transcript = ("The proposed research design involves a detailed multi-turn analysis. " * 400)
    state = ccd.build_desi_state(_V1_SUMMARY, 0.15, 0.23)
    assert ccd.token_count(state) < ccd.token_count(long_transcript)
    # the compact state carries the key drift signals as text
    for marker in ("constraint_preservation", "recovery", "lock_in", "branch_entropy", "composite", "events"):
        assert marker in state


def test_compression_ratio_high_for_long_transcript():
    raw = ccd.token_count("Detailed research-design discussion across many turns. " * 500)
    desi = ccd.token_count(ccd.build_desi_state(_V1_SUMMARY, 0.15, 0.23))
    ratio = 1.0 - desi / raw
    assert ratio > 0.7          # long transcript -> >70% savings


def test_raw_drift_proxy_range():
    item_stable = {"messages": [{"role": "system", "content": "s"},
                                {"role": "assistant", "content": "use only billing panel data and report precision"},
                                {"role": "assistant", "content": "use only billing panel data and report precision"}]}
    item_drift = {"messages": [{"role": "assistant", "content": "rigorous billing panel data analysis"},
                               {"role": "assistant", "content": "an unrelated marketing narrative about something else entirely"}]}
    d_stable = ccd.raw_drift_proxy(item_stable)
    d_drift = ccd.raw_drift_proxy(item_drift)
    assert 0.0 <= d_stable <= 1.0 and 0.0 <= d_drift <= 1.0
    assert d_drift > d_stable
    # single-turn -> no drift signal
    assert ccd.raw_drift_proxy({"messages": [{"role": "assistant", "content": "x"}]}) == 0.0


def test_state_includes_event_ledger():
    state = ccd.build_desi_state(_V1_SUMMARY, 0.15, 0.23)
    assert "1:new_constraint_loss" in state and "3:constraint_recovery" in state
