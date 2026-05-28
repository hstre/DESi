"""Targeted tests for the DESi compression-ablation audit (offline, deterministic, read-only)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

import run_compression_ablation as abl  # noqa: E402
import compression_loss_audit as cla  # noqa: E402

_SUMMARY = {
    "turns": 11, "constraint_half_life_mean": 0.9, "max_constraint_decay": 0.2,
    "unrecovered_constraints": 1, "rhetorical_recovery_count": 3,
    "operational_recovery_count": 1, "failed_recovery_count": 1,
    "recovery_quality_proxy": 0.2, "branch_entropy_proxy": 0.8,
    "branch_collapse_events": 1, "cumulative_drift_energy": 3.4,
    "composite_drift_v1": 0.21,
    "drift_event_ledger": [{"turn": 1, "events": ["new_constraint_loss", "banned_move_incursion"]},
                           {"turn": 3, "events": ["constraint_recovery"]}],
}
_V11 = {"v11_irreversible_lock_in_proxy_v11": 0.15, "v11_composite": 0.23}
_LONG = ("Use only billing-panel data and report calibrated precision across distinct cohorts "
         "while preserving the original constraints and avoiding the banned shortcut moves. " * 30)
_ITEM = {"messages": [
    {"role": "system", "content": "Objective: a controlled longitudinal study of community solar adoption."},
    {"role": "user", "content": "thanks!"},
    {"role": "assistant", "content": _LONG},
    {"role": "user", "content": "ok"},
    {"role": "assistant", "content": "Switching to an unrelated marketing narrative about brand sentiment instead."},
]}


def test_is_filler_short_and_ack_only():
    assert abl.is_filler("ok")
    assert abl.is_filler("thanks!")
    assert abl.is_filler("sure, got it")
    assert not abl.is_filler("Use only billing-panel data and report calibrated precision across cohorts.")


def test_carries_is_monotone_nested():
    # C subset D subset E subset F (each strip removes, never adds)
    assert abl.CARRIES["C"] < abl.CARRIES["D"] < abl.CARRIES["E"] < abl.CARRIES["F"]
    assert abl.CARRIES["A"] == abl.CARRIES["B"] == abl.CARRIES["F"]
    # the exact families peeled at each structured step
    assert abl.CARRIES["F"] - abl.CARRIES["E"] == {"lock_in"}
    assert abl.CARRIES["E"] - abl.CARRIES["D"] == {"recovery", "event"}
    assert abl.CARRIES["D"] - abl.CARRIES["C"] == {"branch"}


def test_state_token_monotonicity():
    tC = abl.token_count(abl.variant_state_text(_ITEM, _SUMMARY, _V11, "C"))
    tD = abl.token_count(abl.variant_state_text(_ITEM, _SUMMARY, _V11, "D"))
    tE = abl.token_count(abl.variant_state_text(_ITEM, _SUMMARY, _V11, "E"))
    tF = abl.token_count(abl.variant_state_text(_ITEM, _SUMMARY, _V11, "F"))
    tA = abl.token_count(abl.variant_state_text(_ITEM, _SUMMARY, _V11, "A"))
    assert 0 < tC < tD < tE <= tF < tA   # more fields -> more tokens; raw transcript largest


def test_epistemic_retained_monotone_and_endpoints():
    w = {"constraint": 0.2, "branch": 0.2, "recovery": 0.2, "event": 0.4, "lock_in": 0.05}
    r = {lv: abl.epistemic_retained(lv, w) for lv in abl.VARIANTS}
    assert r["A"] == r["B"] == r["F"] == 1.0          # text + full state preserve everything
    assert r["C"] < r["D"] < r["E"] < r["F"]          # each added family raises retention
    assert 0.0 < r["C"] < 1.0


def test_pareto_front_includes_full_state_and_excludes_raw():
    # F dominates A/B (same retention, far higher compression); C/D/E/F form the trade-off front
    pts = {"A": (0.0, 1.0), "B": (0.0002, 1.0), "C": (0.995, 0.22),
           "D": (0.993, 0.43), "E": (0.971, 0.99), "F": (0.965, 1.0)}
    front = abl._pareto_front(pts)
    assert "F" in front
    assert "A" not in front and "B" not in front
    assert {"C", "D", "E"} <= front


def test_minmax_bounds():
    out = abl._minmax([3.0, 1.0, 5.0, 1.0])
    assert min(out) == 0.0 and max(out) == 1.0
    assert abl._minmax([2.0, 2.0]) == [0.0, 0.0]   # constant -> all zero, no divide-by-zero


def _synth_rows(n=8):
    rows = []
    for i in range(n):
        f = i / (n - 1)
        rows.append({
            "run_id": f"r{i}", "drift_severity": i % 4,
            "constraint_adherence": 4 - (i % 4), "alternative_coverage": i % 5,
            "recoverability": 4 - (i % 3), "lock_in_binary": 1 if i % 4 == 3 else 0,
            "tokens": {"A": 1000 + i, "B": 998 + i, "C": 20, "D": 30, "E": 200, "F": 260},
            "raw_drift": round(0.2 + 0.5 * f, 3),
            "constraint_half_life_mean": round(1.0 - 0.5 * f, 3),
            "branch_entropy_proxy": round(0.9 - 0.4 * f, 3),
            "recovery_quality_proxy": round(0.1 + 0.7 * f, 3),
            "total_events": i, "lock_in_proxy": round(0.05 * (i % 4), 3),
            "max_constraint_decay": round(0.3 * f, 3), "unrecovered_constraints": i % 3,
            "branch_collapse_events": i % 4, "failed_recovery_count": i % 2,
            "cumulative_drift_energy": round(2.0 + f, 3),
        })
    return rows


def test_loss_attribution_signal_to_step_mapping():
    rows = _synth_rows()
    _agg, steps = cla.attribute(rows)
    by_step = {s["step"]: s for s in steps}
    assert by_step["F->E"]["signals_lost"] == ["lock_in"]
    assert by_step["E->D"]["signals_lost"] == ["event", "recovery"]
    assert by_step["D->C"]["signals_lost"] == ["branch"]
    # the big text->state jump loses nothing and saves the most tokens
    assert by_step["B->F"]["signals_lost"] == [] and by_step["B->F"]["epistemic_loss"] == 0.0
    assert by_step["A->B"]["epistemic_loss"] == 0.0
    assert by_step["B->F"]["extra_compression"] == max(s["extra_compression"] for s in steps)


def test_loss_attribution_flags_pure_loss_steps():
    rows = _synth_rows()
    _agg, steps = cla.attribute(rows)
    by_step = {s["step"]: s for s in steps}
    # stripping inside the state saves ~0 tokens but costs signal -> flagged
    assert by_step["E->D"]["flag"] and by_step["D->C"]["flag"]
    # the free / valuable steps are not flagged
    assert not by_step["A->B"]["flag"] and not by_step["B->F"]["flag"]
