"""v3.27 — rollback tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.epistemic_trajectory.state import StateVector
from desi.trajectory_control.negative_controls import (
    all_ncs,
)
from desi.trajectory_control.replay_control import (
    control_all_with_rollback, control_with_rollback,
    replay_stability,
)
from desi.trajectory_control.report_v3_27 import (
    MAX_NC_ROLLBACK_RATE, MAX_OVERCONTROL_RATE,
    MIN_REPLAY_STABILITY, build_report,
)
from desi.trajectory_control.rollback import (
    RollbackKind, apply_rollback_last_transition,
)
from desi.trajectory_control.trace import (
    TraceEntry, TraceLog,
)


def _sv(**overrides):
    base = dict(
        frame_id=2.0, contradiction_load=0.0,
        anchor_density=0.5, source_quality=0.0,
        novelty=0.0, confidence=0.6, branch_cost=3.0,
        support_state=0.0, routing_state=2.0,
    )
    base.update(overrides)
    return StateVector(**base)


def test_rollback_kind_value_matches_directive() -> None:
    assert (
        RollbackKind.ROLLBACK_LAST_TRANSITION.value
        == "rollback_last_transition"
    )


def test_apply_rollback_replaces_tail_with_anchor() -> None:
    s0 = _sv(novelty=0.0)
    s1 = _sv(novelty=1.0)
    s2 = _sv(novelty=2.0, support_state=3.0)
    out = apply_rollback_last_transition((s0, s1, s2), at=2)
    assert out[0] == s0
    assert out[1] == s1
    # The tail is replaced by states[at-1] = s1
    assert out[2] == s1


def test_rollback_at_zero_is_noop() -> None:
    s0 = _sv()
    out = apply_rollback_last_transition((s0,), at=0)
    assert out == (s0,)


def test_replay_stability_is_one() -> None:
    """Controller must be deterministic across replays."""
    assert replay_stability() >= MIN_REPLAY_STABILITY


def test_trace_log_signatures_stable_across_replays() -> None:
    trajs = extract_all_trajectories()[:20]
    first = control_all_with_rollback(trajs)
    second = control_all_with_rollback(trajs)
    for a, b in zip(first, second):
        assert a.trace.signature() == b.trace.signature(), (
            a.trajectory_id
        )


def test_controller_does_not_rollback_on_ncs() -> None:
    """Directive Stop Rule: false_intervention_rate > 0.2
    halts. Rollback is a stronger action than the v3.26
    set; it must not fire on any NC."""
    for nc in all_ncs():
        out = control_with_rollback(nc.trajectory)
        assert not out.rolled_back, nc.nc_id


def test_overcontrol_rate_meets_gate() -> None:
    assert build_report().overcontrol_rate <= (
        MAX_OVERCONTROL_RATE
    )


def test_nc_rollback_rate_meets_gate() -> None:
    assert build_report().nc_rollback_rate <= (
        MAX_NC_ROLLBACK_RATE
    )


def test_rescued_verdicts_reported() -> None:
    rep = build_report().to_dict()
    for key in (
        "rescued_verdicts", "overcontrol_cases",
        "replay_stability",
    ):
        assert key in rep, key


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ROLLBACK_RESCUES_VERDICTS",
        "ROLLBACK_NEUTRAL", "HALT_ROLLBACK",
    }
    assert build_report().recommendation in allowed


def test_rollback_can_actually_rescue_a_verdict() -> None:
    """Empirical floor: at least one rescue on the real
    trajectory corpus."""
    rep = build_report()
    assert rep.rescued_verdicts >= 1


def test_no_overcontrol_in_current_report() -> None:
    """The risk-score floor for rollback at the final
    transition must be tight enough to keep overcontrol
    at zero on the current corpus."""
    assert build_report().overcontrol_cases == 0


def test_artifact_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_27" / "report.json")
        .read_text(encoding="utf-8"),
    )
    live = build_report().to_dict()
    # Numerical fields can drift by tiny amounts due to
    # upstream hash-seed effects; integers + 1.0 floats
    # are exact, mean-style floats use 6 decimals here.
    volatile = set()  # nothing volatile in v3.27 report
    for k in art:
        if k in volatile:
            assert abs(art[k] - live[k]) <= 1.0
        else:
            assert art[k] == live[k], (k, art[k], live[k])


def test_trace_log_per_state_has_an_action_field() -> None:
    out = control_with_rollback(
        extract_all_trajectories()[0],
    )
    for entry in out.trace.entries:
        assert entry.action in (
            "no_action", "branch_freeze",
            "forced_replay", "confidence_hold",
            "rollback_last_transition",
        ), entry.action


def test_replay_control_module_uses_only_existing_actions() -> None:
    """v3.27's new action must come from the
    rollback.RollbackKind enum; the v3.26 actions remain
    available via ActionKind."""
    from desi.trajectory_control import (
        ActionKind, RollbackKind,
    )
    assert RollbackKind.ROLLBACK_LAST_TRANSITION.value not in {
        a.value for a in ActionKind
    }


def test_no_forbidden_runtime_modules_imported() -> None:
    """Directive's recurring constraint: no rule changes,
    no frame overrides, no causal overrides. The
    trajectory_control package must not import from the
    runtime rule / frame / causal modules in a way that
    would mutate runtime state."""
    forbidden = ("rule_patch_protocol",)
    import desi.trajectory_control.actions as a
    import desi.trajectory_control.controller as c
    import desi.trajectory_control.observer as o
    import desi.trajectory_control.policies as p
    import desi.trajectory_control.replay_control as r
    import desi.trajectory_control.report_v3_27 as rep
    import desi.trajectory_control.rollback as rb
    import desi.trajectory_control.trace as t
    for mod in (a, c, o, p, r, rep, rb, t):
        src = pathlib.Path(mod.__file__).read_text()
        for f in forbidden:
            assert f"import {f}" not in src, (mod.__name__, f)
