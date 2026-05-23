"""v5.0 — isolated sandbox state and pure
action application.

The state is intentionally tiny: a step counter,
an immutable list of observations, an immutable
list of hypotheses, and the set of checkpoint
indices that have been recorded so far. Every
action is a pure function from ``(state,
session_id, seed, step)`` to a new state, so the
entire trajectory is determined by the
``SessionConfig`` alone.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache

from .session import SandboxAction


@dataclass(frozen=True)
class SandboxState:
    step: int
    observations: tuple[str, ...]
    hypotheses: tuple[str, ...]
    checkpoints: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "observations":
                list(self.observations),
            "hypotheses":
                list(self.hypotheses),
            "checkpoints":
                list(self.checkpoints),
        }


def initial_state() -> SandboxState:
    return SandboxState(
        step=0, observations=(),
        hypotheses=(), checkpoints=(),
    )


def state_hash(state: SandboxState) -> str:
    raw = json.dumps(
        state.to_dict(), sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@lru_cache(maxsize=None)
def _step_digest(
    session_id: str, seed: int, step: int,
) -> bytes:
    raw = (
        f"{session_id}:{seed}:{step}"
        .encode("utf-8")
    )
    return hashlib.sha256(raw).digest()


def pick_action(
    session_id: str, seed: int, step: int,
    checkpoint_every: int,
) -> SandboxAction:
    """Deterministic action selection.

    Every ``checkpoint_every`` steps we force a
    CHECKPOINT so rollback has anchors. Otherwise
    the action is chosen by the low byte of the
    step digest, biased away from CHECKPOINT so
    OBSERVE/HYPOTHESIZE dominate the trajectory.
    """
    if (
        checkpoint_every > 0
        and step > 0
        and step % checkpoint_every == 0
    ):
        return SandboxAction.CHECKPOINT
    d = _step_digest(session_id, seed, step)
    pick = d[0] % 4
    if pick == 0:
        return SandboxAction.OBSERVE
    if pick == 1:
        return SandboxAction.HYPOTHESIZE
    if pick == 2:
        return SandboxAction.OBSERVE
    return SandboxAction.HYPOTHESIZE


def payload_for(
    session_id: str, seed: int, step: int,
    action: SandboxAction,
) -> str:
    d = _step_digest(session_id, seed, step)
    tag = d[:4].hex()
    return f"{action.value}:{tag}"


def apply_action(
    state: SandboxState,
    action: SandboxAction, payload: str,
) -> SandboxState:
    new_step = state.step + 1
    if action == SandboxAction.OBSERVE:
        return SandboxState(
            step=new_step,
            observations=(
                state.observations + (payload,)
            ),
            hypotheses=state.hypotheses,
            checkpoints=state.checkpoints,
        )
    if action == SandboxAction.HYPOTHESIZE:
        return SandboxState(
            step=new_step,
            observations=state.observations,
            hypotheses=(
                state.hypotheses + (payload,)
            ),
            checkpoints=state.checkpoints,
        )
    if action == SandboxAction.CHECKPOINT:
        return SandboxState(
            step=new_step,
            observations=state.observations,
            hypotheses=state.hypotheses,
            checkpoints=(
                state.checkpoints + (new_step,)
            ),
        )
    # NOOP
    return SandboxState(
        step=new_step,
        observations=state.observations,
        hypotheses=state.hypotheses,
        checkpoints=state.checkpoints,
    )


__all__ = [
    "SandboxState",
    "apply_action",
    "initial_state",
    "payload_for",
    "pick_action",
    "state_hash",
]
