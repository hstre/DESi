"""v5.1 — claim-stream injector into the
adolescence sandbox.

Each open-world claim becomes one sandbox step
(OBSERVE if its frame is recognised, NOOP if
UNKNOWN). The injector reuses the v5.0
deterministic state-hashing primitives so an
injected session is fully replayable.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache

from ..adolescence.sandbox import (
    SandboxState, apply_action, initial_state,
    state_hash,
)
from ..adolescence.session import SandboxAction
from .claim_stream import (
    Claim, FrameType, stream_claims,
)


@dataclass(frozen=True)
class InjectedStep:
    step: int
    claim_id: str
    source: str
    frame: str
    action: str
    state_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "claim_id": self.claim_id,
            "source": self.source,
            "frame": self.frame,
            "action": self.action,
            "state_hash": self.state_hash,
        }


def _action_for(claim: Claim) -> SandboxAction:
    if claim.frame == FrameType.UNKNOWN.value:
        return SandboxAction.NOOP
    return SandboxAction.OBSERVE


def _payload_for(claim: Claim) -> str:
    h = hashlib.sha256(
        f"{claim.claim_id}:{claim.text}"
        .encode("utf-8"),
    ).digest()[:4].hex()
    return f"claim:{claim.claim_id}:{h}"


@dataclass(frozen=True)
class InjectedSession:
    initial_hash: str
    final_hash: str
    steps: tuple[InjectedStep, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "initial_hash": self.initial_hash,
            "final_hash": self.final_hash,
            "steps": [
                s.to_dict() for s in self.steps
            ],
        }


@lru_cache(maxsize=1)
def inject_all() -> InjectedSession:
    state = initial_state()
    initial_h = state_hash(state)
    steps: list[InjectedStep] = []
    for c in stream_claims():
        action = _action_for(c)
        payload = _payload_for(c)
        state = apply_action(
            state, action, payload,
        )
        steps.append(InjectedStep(
            step=state.step,
            claim_id=c.claim_id,
            source=c.source, frame=c.frame,
            action=action.value,
            state_hash=state_hash(state),
        ))
    return InjectedSession(
        initial_hash=initial_h,
        final_hash=state_hash(state),
        steps=tuple(steps),
    )


def replay_injection() -> InjectedSession:
    inject_all.cache_clear()
    return inject_all()


__all__ = [
    "InjectedSession",
    "InjectedStep",
    "inject_all",
    "replay_injection",
]
