"""v5.0 - sandbox-runtime tests."""
from __future__ import annotations

import json
import pathlib

from desi.adolescence.report import (
    build_report,
    build_sandbox_runtime_artifact,
    rollback_success, seed_invariance,
    session_replay_rate, snapshot_integrity,
)
from desi.adolescence.runtime import (
    default_session_configs, replay_session,
    rollback_to, run_session,
)
from desi.adolescence.sandbox import (
    apply_action, initial_state, payload_for,
    pick_action, state_hash,
)
from desi.adolescence.session import (
    ACTIONS, SandboxAction, SessionConfig,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "v5_0"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_actions_is_closed_set() -> None:
    assert ACTIONS == tuple(
        a.value for a in SandboxAction
    )
    assert len(ACTIONS) == 4


def test_initial_state_is_empty() -> None:
    s = initial_state()
    assert s.step == 0
    assert s.observations == ()
    assert s.hypotheses == ()
    assert s.checkpoints == ()


def test_apply_action_is_pure() -> None:
    s0 = initial_state()
    s1 = apply_action(
        s0, SandboxAction.OBSERVE, "x",
    )
    s2 = apply_action(
        s0, SandboxAction.OBSERVE, "x",
    )
    assert s1 == s2
    assert s0 == initial_state()


def test_state_hash_is_deterministic() -> None:
    s = apply_action(
        initial_state(),
        SandboxAction.HYPOTHESIZE, "h",
    )
    assert state_hash(s) == state_hash(s)


def test_pick_action_is_deterministic() -> None:
    a = pick_action("sess_01", 1, 3, 5)
    b = pick_action("sess_01", 1, 3, 5)
    assert a == b


def test_pick_action_forces_checkpoint() -> None:
    """Every checkpoint_every-th step must be a
    CHECKPOINT, so rollback has anchors."""
    a = pick_action("sess_01", 1, 5, 5)
    assert a == SandboxAction.CHECKPOINT


def test_run_session_step_count() -> None:
    cfg = SessionConfig(
        session_id="t", seed=0,
        step_count=20, checkpoint_every=5,
    )
    s = run_session(cfg)
    assert len(s.trajectory) == 20


def test_run_then_replay_is_identical() -> None:
    """Pflichtfrage 1: ist jede Session
    replaybar?"""
    cfg = SessionConfig(
        session_id="t", seed=42,
        step_count=20, checkpoint_every=5,
    )
    a = run_session(cfg)
    b = replay_session(cfg)
    assert a.to_dict() == b.to_dict()


def test_rollback_reconstructs_state() -> None:
    """Pflichtfrage 2: koennen Sessions
    zurueckgerollt werden?"""
    cfg = SessionConfig(
        session_id="t", seed=42,
        step_count=20, checkpoint_every=5,
    )
    sess = run_session(cfg)
    for snap in sess.snapshots:
        state = rollback_to(cfg, snap.step)
        assert state_hash(state) == (
            snap.state_hash
        )
        assert state.step == snap.step


def test_rollback_to_zero_is_initial() -> None:
    cfg = SessionConfig(
        session_id="t", seed=0,
        step_count=10, checkpoint_every=5,
    )
    s = rollback_to(cfg, 0)
    assert s == initial_state()


def test_rollback_target_out_of_range() -> None:
    cfg = SessionConfig(
        session_id="t", seed=0,
        step_count=5, checkpoint_every=5,
    )
    try:
        rollback_to(cfg, 99)
    except ValueError:
        return
    raise AssertionError(
        "expected ValueError",
    )


def test_different_seeds_diverge() -> None:
    """Same session_id, different seed must
    produce different trajectories."""
    a = run_session(SessionConfig(
        session_id="t", seed=1,
        step_count=20, checkpoint_every=5,
    ))
    b = run_session(SessionConfig(
        session_id="t", seed=2,
        step_count=20, checkpoint_every=5,
    ))
    assert a.final_hash != b.final_hash


def test_same_seed_converges() -> None:
    """Pflichtfrage 3: bleibt Determinismus
    erhalten?"""
    cfg = SessionConfig(
        session_id="t", seed=99,
        step_count=15, checkpoint_every=5,
    )
    assert (
        run_session(cfg).to_dict()
        == run_session(cfg).to_dict()
    )


def test_default_configs_count() -> None:
    assert len(default_session_configs()) == 10


def test_session_replay_rate_one() -> None:
    assert session_replay_rate() == 1.0


def test_rollback_success_one() -> None:
    assert rollback_success() == 1.0


def test_snapshot_integrity_one() -> None:
    assert snapshot_integrity() == 1.0


def test_seed_invariance_one() -> None:
    assert seed_invariance() == 1.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "SANDBOX_READY",
        "SANDBOX_NEARLY_READY",
        "SANDBOX_UNSTABLE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_ready() -> None:
    assert build_report().recommendation == (
        "SANDBOX_READY"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("sandbox_runtime.json")
    assert art["schema_version"] == (
        "v5_0_sandbox_runtime"
    )
    assert art["session_count"] == 10


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("report.json")
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable


def test_artifact_sandbox_matches_live_build() -> (
    None
):
    art = _load("sandbox_runtime.json")
    live = build_sandbox_runtime_artifact()
    assert art == live


def test_payload_for_is_deterministic() -> None:
    a = payload_for(
        "t", 1, 0, SandboxAction.OBSERVE,
    )
    b = payload_for(
        "t", 1, 0, SandboxAction.OBSERVE,
    )
    assert a == b
