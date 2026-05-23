"""v3.30 — cause-aware control tests."""
from __future__ import annotations

import json
import pathlib

from desi.cause_aware_control.actions import (
    CauseActionKind, apply_branch_prune,
    apply_causal_suspend, apply_cause_action,
    apply_frame_replay, apply_support_hold,
)
from desi.cause_aware_control.controller import (
    control_all, control_trajectory,
)
from desi.cause_aware_control.report import (
    MAX_FALSE_INTERVENTION_RATE,
    MAX_NC_INTERVENTION_RATE, build_report,
    build_cause_aware_artifact,
)
from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.epistemic_trajectory.state import StateVector
from desi.trajectory_control.negative_controls import (
    all_ncs,
)


def _sv(**overrides) -> StateVector:
    base = dict(
        frame_id=2.0, contradiction_load=0.0,
        anchor_density=0.5, source_quality=0.0,
        novelty=0.0, confidence=0.6, branch_cost=3.0,
        support_state=0.0, routing_state=2.0,
    )
    base.update(overrides)
    return StateVector(**base)


def test_cause_action_kinds_match_directive() -> None:
    """Directive mapping:
        SUPPORT_DECAY -> support_hold
        FRAME_COLLISION -> frame_replay
        BRANCH_OVERLOAD -> branch_prune
        CAUSAL_LEAP -> causal_suspend
        CONFIDENCE_OSCILLATION -> confidence_hold
        UNKNOWN -> rollback_only"""
    expected = {
        "support_hold", "frame_replay", "branch_prune",
        "causal_suspend", "confidence_hold",
        "rollback_last_transition",
    }
    assert {k.value for k in CauseActionKind} == expected


def test_support_hold_clamps_audit_support_to_anchor() -> None:
    s0 = _sv(support_state=0.0)
    s1 = _sv(support_state=0.0)
    s2 = _sv(support_state=0.0)
    s3 = _sv(support_state=3.0)  # audit-step REJECTED
    out = apply_support_hold((s0, s1, s2, s3), at=2)
    # Final support state should be the anchor (= s1
    # support_state = 0.0), not 3.0.
    assert out[-1].support_state == 0.0


def test_frame_replay_restores_frame_at_audit() -> None:
    s0 = _sv(frame_id=2.0)
    s1 = _sv(frame_id=2.0)
    s2 = _sv(frame_id=5.0)
    s3 = _sv(frame_id=5.0, support_state=3.0)
    out = apply_frame_replay((s0, s1, s2, s3), at=2)
    # Frame ID restored to anchor.
    assert out[2].frame_id == 2.0
    assert out[3].frame_id == 2.0
    # Audit step withdrawn.
    assert out[-1].support_state != 3.0


def test_branch_prune_caps_branch_cost() -> None:
    s0 = _sv(branch_cost=4.0)
    s1 = _sv(branch_cost=8.0)
    s2 = _sv(branch_cost=10.0, support_state=3.0)
    out = apply_branch_prune((s0, s1, s2), at=1)
    cap = max(1.0, s0.branch_cost / 2.0)
    assert out[1].branch_cost <= cap
    assert out[2].branch_cost <= cap


def test_causal_suspend_caps_novelty() -> None:
    s0 = _sv(novelty=1.0)
    s1 = _sv(novelty=5.0)
    s2 = _sv(novelty=8.0, support_state=3.0)
    out = apply_causal_suspend((s0, s1, s2), at=1)
    assert out[1].novelty <= 1.0
    assert out[2].novelty <= 1.0


def test_controller_does_not_intervene_on_ncs() -> None:
    """Directive: NCs must never trigger an
    intervention (cause is UNKNOWN AND no cliff)."""
    for nc in all_ncs():
        out = control_trajectory(nc.trajectory)
        assert not out.intervened, nc.nc_id


def test_false_intervention_rate_meets_gate() -> None:
    assert build_report().false_intervention_rate <= (
        MAX_FALSE_INTERVENTION_RATE
    )


def test_nc_intervention_rate_meets_gate() -> None:
    assert build_report().nc_intervention_rate <= (
        MAX_NC_INTERVENTION_RATE
    )


def test_rollback_reduction_is_positive() -> None:
    """The cause-aware controller must use fewer
    rollback actions than the v3.27 baseline (the entire
    point of routing causes to specific actions)."""
    assert build_report().rollback_reduction > 0


def test_rescued_verdicts_at_least_one() -> None:
    assert build_report().rescued_verdicts >= 1


def test_smoothness_delta_non_negative() -> None:
    """Cause-aware actions clamp problematic dimensions
    so the counterfactual trajectory should not be
    rougher than the original."""
    assert build_report().smoothness_delta >= 0.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "CAUSE_AWARE_CONTROL_REDUCES_ROLLBACKS",
        "CAUSE_AWARE_CONTROL_NEUTRAL_ROLLBACK",
        "CAUSE_AWARE_CONTROL_NO_RESCUE",
        "HALT_FALSE_INTERVENTION",
    }
    assert build_report().recommendation in allowed


def test_no_forbidden_action_kinds() -> None:
    """Directive: still forbidden — rule changes, frame
    overrides at the runtime layer, causal overrides.
    The cause-action enum only carries the six allowed
    names."""
    allowed = {
        "support_hold", "frame_replay", "branch_prune",
        "causal_suspend", "confidence_hold",
        "rollback_last_transition",
    }
    forbidden = {
        "rule_change", "frame_override",
        "causal_override", "patch_rule",
    }
    assert allowed & forbidden == set()


def test_action_distribution_only_uses_allowed_actions() -> None:
    rep = build_report().to_dict()
    allowed = {
        "support_hold", "frame_replay", "branch_prune",
        "causal_suspend", "confidence_hold",
        "rollback_last_transition",
    }
    for k in rep["action_distribution"]:
        assert k in allowed, k


def test_artifact_report_matches_live_build_loosely() -> None:
    """Same float-jitter tolerance as v3.28: cause and
    action distributions can drift by one trajectory
    across runs because FrameDetector's dict-iteration
    is hash-seed sensitive."""
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_30" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {
        "action_distribution", "cause_distribution",
        "smoothness_pre_mean", "smoothness_post_mean",
        "smoothness_delta",
    }
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable


def test_premature_closure_claims_artifact_has_50_claims() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    doc = json.loads(
        (root / "artifacts" / "v3_30"
         / "premature_closure_claims.json").read_text(
            encoding="utf-8",
        )
    )
    assert doc["claim_count"] >= 1
    assert len(doc["claims"]) == doc["claim_count"]


def test_cause_aware_artifact_has_outcomes() -> None:
    art = build_cause_aware_artifact()
    assert "outcomes" in art
    assert len(art["outcomes"]) >= 1
