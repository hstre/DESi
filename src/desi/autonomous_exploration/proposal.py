"""v5.2 — autonomous-exploration proposal model.

A proposal is a READ-ONLY suggestion: it never
mutates production code, never re-deploys the
gate, never rewrites a threshold. The closed
``ProposalKind`` enum is the only universe of
allowed proposal shapes; ``ProposalStatus`` is
always ``PROPOSED`` — there is no
``ACCEPTED`` / ``DEPLOYED`` value because the
sandbox rules forbid auto-activation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProposalKind(str, Enum):
    HYPOTHESIS           = "hypothesis"
    T10_CANDIDATE        = "t10_candidate"
    FRAME_EXTENSION      = "frame_extension"
    CONFLICT_RESOLUTION  = "conflict_resolution"
    INTERVENTION         = "intervention"


PROPOSAL_KINDS: tuple[str, ...] = tuple(
    k.value for k in ProposalKind
)


class ProposalStatus(str, Enum):
    PROPOSED = "proposed"


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    kind: str
    target: str
    rationale: str
    quality_score: float
    status: str = ProposalStatus.PROPOSED.value

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "kind": self.kind,
            "target": self.target,
            "rationale": self.rationale,
            "quality_score": self.quality_score,
            "status": self.status,
        }


_FORBIDDEN_TARGET_TOKENS: tuple[str, ...] = (
    "src/desi/pre_t10_rule",
    "src/desi/pre_t10_v2/rule.py",
    "src/desi/pre_t10_v2_deploy/decision.py",
    "src/desi/frames/",
    "src/desi/frame_inference/",
    "src/desi/state_blindness/",
    "BLINDNESS_CHECK_THRESHOLD",
    "FAR_CEILING",
    "TPR_FLOOR",
    "auto_deploy",
    "self_modify",
    "skip_gate",
    "disable_check",
)


def is_gate_bypass(p: Proposal) -> bool:
    """A proposal is a gate-bypass attempt if its
    target references any forbidden production
    path or any closed-gate threshold constant.

    The exploration generator must never emit
    such proposals; this function is the closed
    auditor used by the report to verify the
    invariant."""
    low_target = p.target.lower()
    low_rat = p.rationale.lower()
    for tok in _FORBIDDEN_TARGET_TOKENS:
        if (
            tok.lower() in low_target
            or tok.lower() in low_rat
        ):
            return True
    return False


__all__ = [
    "PROPOSAL_KINDS",
    "Proposal",
    "ProposalKind",
    "ProposalStatus",
    "is_gate_bypass",
]
