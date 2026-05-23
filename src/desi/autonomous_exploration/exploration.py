"""v5.2 — autonomous exploration loop.

Generates a fixed set of proposals from the
ranked claim stream and prioritised conflicts.
The generator is read-only with respect to
production code: it composes ``Proposal``
objects but never writes to any source file.

Every proposal target deliberately avoids the
forbidden-token list in
``proposal._FORBIDDEN_TARGET_TOKENS`` so the
``gate_bypass_attempts`` Pflichtmetrik stays 0
by construction. The closed-set discipline (no
free-text targets) is what makes that
guaranteeable.
"""
from __future__ import annotations

from functools import lru_cache

from ..open_world.claim_stream import FrameType
from .curiosity import (
    curiosity_score, prioritised_conflict_kinds,
    ranked_claims,
)
from .proposal import (
    Proposal, ProposalKind, ProposalStatus,
)


_KIND_BY_FRAME: dict[str, ProposalKind] = {
    FrameType.CAUSAL.value:
        ProposalKind.HYPOTHESIS,
    FrameType.PREDICTIVE.value:
        ProposalKind.T10_CANDIDATE,
    FrameType.DEFINITIONAL.value:
        ProposalKind.FRAME_EXTENSION,
    FrameType.EVALUATIVE.value:
        ProposalKind.HYPOTHESIS,
    FrameType.NORMATIVE.value:
        ProposalKind.INTERVENTION,
    FrameType.REPORT.value:
        ProposalKind.HYPOTHESIS,
    FrameType.BUG_REPORT.value:
        ProposalKind.INTERVENTION,
}


_TARGET_PREFIX = "sandbox/proposal/"


def _claim_to_proposal(
    claim, score: float,
) -> Proposal:
    kind = _KIND_BY_FRAME.get(
        claim.frame, ProposalKind.HYPOTHESIS,
    )
    target = (
        f"{_TARGET_PREFIX}{kind.value}/"
        f"{claim.claim_id}"
    )
    rationale = (
        f"frame={claim.frame} "
        f"source={claim.source} "
        f"curiosity={score}"
    )
    pid = (
        f"prop:{kind.value}:{claim.claim_id}"
    )
    return Proposal(
        proposal_id=pid, kind=kind.value,
        target=target, rationale=rationale,
        quality_score=score,
        status=ProposalStatus.PROPOSED.value,
    )


def _conflict_kind_proposal(
    rank: int, kind: str,
) -> Proposal:
    score = max(0.1, 0.8 - 0.1 * rank)
    target = (
        f"{_TARGET_PREFIX}"
        f"conflict_resolution/{kind}"
    )
    return Proposal(
        proposal_id=(
            f"prop:conflict_resolution:{kind}"
        ),
        kind=(
            ProposalKind
            .CONFLICT_RESOLUTION.value
        ),
        target=target,
        rationale=(
            f"conflict_kind={kind} "
            f"priority_rank={rank}"
        ),
        quality_score=round(score, 6),
        status=ProposalStatus.PROPOSED.value,
    )


@lru_cache(maxsize=1)
def all_proposals() -> tuple[Proposal, ...]:
    out: list[Proposal] = []
    # Top-N curious claims become proposals
    # (N=15 of 30 to leave half the stream
    # uncovered, surfacing exploration choice).
    for c in ranked_claims()[:15]:
        score = curiosity_score(c)
        if score < 0.15:
            continue
        out.append(
            _claim_to_proposal(c, score),
        )
    # Plus one proposal per prioritised conflict
    # kind.
    for rank, kind in enumerate(
        prioritised_conflict_kinds(),
    ):
        out.append(
            _conflict_kind_proposal(rank, kind),
        )
    return tuple(out)


def proposals_by_kind() -> dict[
    str, tuple[Proposal, ...],
]:
    out: dict[str, list[Proposal]] = {}
    for p in all_proposals():
        out.setdefault(p.kind, []).append(p)
    return {
        k: tuple(v)
        for k, v in sorted(out.items())
    }


def proposal_kind_counts() -> dict[str, int]:
    return {
        k: len(v)
        for k, v in proposals_by_kind().items()
    }


__all__ = [
    "all_proposals",
    "proposal_kind_counts",
    "proposals_by_kind",
]
