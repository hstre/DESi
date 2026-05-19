"""v5.3 — long-horizon trajectory generator.

DESi runs 200 deterministic steps under sandbox
governance, consuming the open-world claim
stream cyclically. Each step produces a closed
``LongHorizonStep`` record so the trajectory is
fully replayable.

No stochastic state, no PRNG. Each step's
proposal is a deterministic function of the
claim it consumed at that step.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache

from ..autonomous_exploration.curiosity import (
    curiosity_score,
)
from ..autonomous_exploration.exploration import (
    _KIND_BY_FRAME, _TARGET_PREFIX,
)
from ..autonomous_exploration.proposal import (
    Proposal, ProposalKind, ProposalStatus,
    is_gate_bypass,
)
from ..open_world.claim_stream import (
    FrameType, stream_claims,
)


STEP_COUNT: int = 200


@dataclass(frozen=True)
class LongHorizonStep:
    step: int
    claim_id: str
    frame: str
    proposal_kind: str
    curiosity: float
    cumulative_state_hash: str
    gate_bypass: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "claim_id": self.claim_id,
            "frame": self.frame,
            "proposal_kind":
                self.proposal_kind,
            "curiosity": self.curiosity,
            "cumulative_state_hash":
                self.cumulative_state_hash,
            "gate_bypass": self.gate_bypass,
        }


def _kind_for_frame(frame: str) -> str:
    kind = _KIND_BY_FRAME.get(
        frame, ProposalKind.HYPOTHESIS,
    )
    return kind.value


def _step_proposal(
    step: int, claim, score: float,
) -> Proposal:
    kind = _kind_for_frame(claim.frame)
    target = (
        f"{_TARGET_PREFIX}{kind}/"
        f"step_{step:03d}/{claim.claim_id}"
    )
    return Proposal(
        proposal_id=(
            f"prop:step_{step:03d}:"
            f"{claim.claim_id}"
        ),
        kind=kind, target=target,
        rationale=(
            f"step={step} frame={claim.frame} "
            f"curiosity={score}"
        ),
        quality_score=score,
        status=ProposalStatus.PROPOSED.value,
    )


@lru_cache(maxsize=1)
def trajectory() -> tuple[LongHorizonStep, ...]:
    claims = stream_claims()
    out: list[LongHorizonStep] = []
    running = b""
    for step in range(STEP_COUNT):
        claim = claims[step % len(claims)]
        score = curiosity_score(claim)
        proposal = _step_proposal(
            step, claim, score,
        )
        bypass = is_gate_bypass(proposal)
        running = hashlib.sha256(
            running
            + f"{step}:{claim.claim_id}:"
              f"{proposal.kind}:{bypass}"
              .encode("utf-8"),
        ).digest()
        out.append(LongHorizonStep(
            step=step,
            claim_id=claim.claim_id,
            frame=claim.frame,
            proposal_kind=proposal.kind,
            curiosity=score,
            cumulative_state_hash=(
                running.hex()[:16]
            ),
            gate_bypass=bypass,
        ))
    return tuple(out)


def replay_trajectory() -> tuple[
    LongHorizonStep, ...,
]:
    trajectory.cache_clear()
    return trajectory()


def trajectory_final_hash() -> str:
    t = trajectory()
    if not t:
        return ""
    return t[-1].cumulative_state_hash


__all__ = [
    "LongHorizonStep",
    "STEP_COUNT",
    "replay_trajectory",
    "trajectory",
    "trajectory_final_hash",
]
