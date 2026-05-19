"""v5.0 — deterministic adolescence sandbox
runtime.

``run_session(config)`` produces a complete
``Session`` from a ``SessionConfig`` by stepping
the sandbox state forward through a closed,
pure-function action loop. ``replay_session``
recomputes the trajectory from the config alone
and must produce a bit-identical Session.
``rollback`` reconstructs the state at any prior
step.

No PYTHONHASHSEED dependency, no PRNG state, no
external I/O: every byte comes from
``hashlib.sha256(f"{session_id}:{seed}:{step}")``
and the closed action enum.
"""
from __future__ import annotations

from functools import lru_cache

from .sandbox import (
    SandboxState, apply_action, initial_state,
    payload_for, pick_action, state_hash,
)
from .session import (
    SandboxAction, Session, SessionConfig,
    Snapshot, TrajectoryStep,
)


def _step_once(
    state: SandboxState, config: SessionConfig,
) -> tuple[SandboxState, TrajectoryStep]:
    action_enum = pick_action(
        config.session_id, config.seed,
        state.step, config.checkpoint_every,
    )
    payload = payload_for(
        config.session_id, config.seed,
        state.step, action_enum,
    )
    new_state = apply_action(
        state, action_enum, payload,
    )
    step_record = TrajectoryStep(
        step=new_state.step,
        action=action_enum.value,
        payload=payload,
        state_hash=state_hash(new_state),
    )
    return new_state, step_record


def run_session(
    config: SessionConfig,
) -> Session:
    state = initial_state()
    initial_h = state_hash(state)
    traj: list[TrajectoryStep] = []
    snaps: list[Snapshot] = []
    for _ in range(config.step_count):
        state, rec = _step_once(state, config)
        traj.append(rec)
        if rec.action == (
            SandboxAction.CHECKPOINT.value
        ):
            snaps.append(Snapshot(
                step=rec.step,
                state_hash=rec.state_hash,
                label=(
                    f"checkpoint@{rec.step}"
                ),
            ))
    return Session(
        config=config,
        initial_hash=initial_h,
        final_hash=state_hash(state),
        trajectory=tuple(traj),
        snapshots=tuple(snaps),
    )


def replay_session(
    config: SessionConfig,
) -> Session:
    """Replay is identical to run_session by
    construction; we provide the function so the
    intent is explicit at call sites and the
    determinism gate can compare run vs replay."""
    return run_session(config)


def rollback_to(
    config: SessionConfig, target_step: int,
) -> SandboxState:
    """Reconstruct the sandbox state at
    ``target_step`` by replaying from the initial
    state. Returns the state immediately AFTER
    target_step has been applied (so step ==
    target_step in the returned state)."""
    if target_step < 0:
        raise ValueError(
            "target_step must be >= 0",
        )
    if target_step > config.step_count:
        raise ValueError(
            "target_step exceeds step_count",
        )
    state = initial_state()
    for _ in range(target_step):
        state, _ = _step_once(state, config)
    return state


def snapshot_steps(
    session: Session,
) -> tuple[int, ...]:
    return tuple(
        s.step for s in session.snapshots
    )


def state_at(
    config: SessionConfig, step: int,
) -> SandboxState:
    return rollback_to(config, step)


@lru_cache(maxsize=1)
def default_session_configs() -> tuple[
    SessionConfig, ...,
]:
    """Closed set of sandbox sessions used for
    v5.0's Pflichtmetriken. Ten seeds, twenty
    steps each, checkpoints every five steps."""
    return tuple(
        SessionConfig(
            session_id=f"sess_{seed:02d}",
            seed=seed, step_count=20,
            checkpoint_every=5,
        )
        for seed in range(10)
    )


__all__ = [
    "default_session_configs",
    "replay_session",
    "rollback_to",
    "run_session",
    "snapshot_steps",
    "state_at",
]
