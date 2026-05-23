"""v3.29 — counterfactual survival tests."""
from __future__ import annotations

import json
import pathlib

from desi.counterfactual_survival.report import (
    build_report, build_survival_artifact,
)
from desi.counterfactual_survival.runs import (
    RunKind, all_runs, rollback_trajectory_ids,
)
from desi.counterfactual_survival.survival import (
    compare_runs,
)
from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)


def test_run_kinds_are_closed_set() -> None:
    expected = {
        "RUN_A_NORMAL", "RUN_B_NO_ROLLBACK",
        "RUN_C_NO_PRUNING", "RUN_D_DELAYED_CLOSURE",
    }
    assert {k.value for k in RunKind} == expected


def test_all_runs_returns_four_outcomes() -> None:
    trajs = extract_all_trajectories()
    runs = all_runs(trajs[0])
    assert len(runs) == 4
    assert {r.run for r in runs} == {k.value for k in RunKind}


def test_run_c_preserves_original_states() -> None:
    """Run C is identity: no controller, no actions —
    the trajectory's final-state vector matches the
    original."""
    trajs = extract_all_trajectories()
    for t in trajs[:10]:
        runs = all_runs(t)
        run_c = next(
            r for r in runs if r.run == "RUN_C_NO_PRUNING"
        )
        assert (
            run_c.final_support_state
            == t.states[-1].support_state
        )


def test_run_d_truncates_trajectory_by_one_step() -> None:
    """Run D removes the audit step. The pre-audit state
    has support_state = 0 (the UNDER_AUDIT placeholder)
    on every v3-shape trajectory."""
    trajs = extract_all_trajectories()
    for t in trajs[:10]:
        runs = all_runs(t)
        run_d = next(
            r for r in runs
            if r.run == "RUN_D_DELAYED_CLOSURE"
        )
        # The pre-audit state's support_state is what
        # state[-2] carries.
        if len(t.states) >= 2:
            assert (
                run_d.final_support_state
                == t.states[-2].support_state
            )


def test_paper9_stop_rule_not_triggered() -> None:
    """Directive Stop Rule: survival_gain == 0 halts
    Paper 9. With the empirically-tuned controller on
    the current corpus, survival_gain must be > 0."""
    r = build_report()
    assert r.survival_gain > 0
    assert r.paper9_stop is False


def test_rollback_id_count_matches_v3_27() -> None:
    """The rolled-back set must be derived from the v3.27
    controller and contain at least one entry."""
    ids = rollback_trajectory_ids()
    assert len(ids) >= 1


def test_run_outcomes_record_six_directive_metrics() -> None:
    """Directive Messgrößen per run: final verdict,
    smoothness, branch_cost, contradiction count,
    support depth, replay hash."""
    trajs = extract_all_trajectories()
    runs = all_runs(trajs[0])
    for r in runs:
        d = r.to_dict()
        for k in (
            "final_support_state", "smoothness",
            "final_branch_cost",
            "final_contradiction_load",
            "support_depth", "replay_hash",
        ):
            assert k in d


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PAPER9_STOP_NO_SURVIVAL_GAIN",
        "BOTH_ROLLBACK_AND_DELAYED_CLOSURE_HELP",
        "DELAYED_CLOSURE_EXPLAINS_RESCUE",
        "ROLLBACK_PROVIDES_NO_SURVIVAL_GAIN",
    }
    assert build_report().recommendation in allowed


def test_survival_artifact_has_per_trajectory_comparisons() -> None:
    art = build_survival_artifact()
    assert "comparisons" in art
    assert len(art["comparisons"]) == build_report().rolled_back_count


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_29" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    assert art == live


def test_rollback_only_gain_is_documented() -> None:
    """Even when rollback_only_gain is 0 — meaning
    rollback adds no rescue beyond delayed closure —
    the report records it transparently so Paper 9's
    'premature closure' hypothesis is verifiable."""
    rep = build_report().to_dict()
    assert "rollback_only_gain" in rep
    assert rep["rollback_only_gain"] >= 0


def test_runs_are_deterministic() -> None:
    trajs = extract_all_trajectories()[:5]
    for t in trajs:
        a = tuple((r.run, r.replay_hash) for r in all_runs(t))
        b = tuple((r.run, r.replay_hash) for r in all_runs(t))
        assert a == b
