"""v16.2 - adversarial escalation chains and DESi's
governed response.

Each chain is a deliberate attempt to push a claim
or assumption to a higher certainty than the public
record supports - a chain of conjecture, an
unsupported causal jump, a hidden assumption,
narrative inflation. DESi GOVERNS every node by
capping its standing at the evidence grade and
flagging the gap. It never adopts the inflated
certainty.

The chains are stress fixtures, not factual claims.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from desi.criminal_epistemics import (
    ClaimStatus, by_id, evidence_rank,
)

_MAX_RANK = 6.0
# Attempted standing this far above evidence is an
# escalation that must be flagged and capped.
_ESCALATION_GAP = 1


class ChainId(str, Enum):
    ACOUSTIC_TO_PLOT = "acoustic_to_plot"
    KNOLL_TO_COVERUP = "knoll_to_coverup"
    SINGLE_BULLET_TO_CERTAINTY = (
        "single_bullet_to_certainty"
    )


CHAIN_IDS: tuple[str, ...] = tuple(
    c.value for c in ChainId
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class EscalationNode:
    node_id: str
    label: str
    # backing claim id, or "" for a pure assumption
    claim_id: str
    # how strongly the chain ASSERTS this node
    attempted_status: str
    # what the public record actually supports
    evidence_status: str
    is_hidden_assumption: bool
    # the dissenting claim this node tries to bury
    dissent_claim_id: str = ""

    def governed_status(self) -> str:
        """DESi caps the standing at the evidence
        grade - it never presents a node above what
        the record supports."""
        return self.evidence_status

    def attempted_rank(self) -> int:
        return evidence_rank(self.attempted_status)

    def evidence_rankv(self) -> int:
        return evidence_rank(self.evidence_status)

    def escalation_gap(self) -> int:
        return max(
            0,
            self.attempted_rank()
            - self.evidence_rankv(),
        )

    def is_escalation(self) -> bool:
        return self.escalation_gap() >= _ESCALATION_GAP

    def false_certainty_leak(self) -> bool:
        """True iff DESi's GOVERNED standing exceeds
        the evidence grade. Must always be False."""
        return (
            evidence_rank(self.governed_status())
            > self.evidence_rankv()
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "claim_id": self.claim_id,
            "attempted_status": self.attempted_status,
            "evidence_status": self.evidence_status,
            "governed_status": self.governed_status(),
            "escalation_gap": self.escalation_gap(),
            "is_escalation": self.is_escalation(),
            "is_hidden_assumption":
                self.is_hidden_assumption,
            "dissent_claim_id": self.dissent_claim_id,
        }


@dataclass(frozen=True)
class EscalationChain:
    chain_id: str
    nodes: tuple[EscalationNode, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "nodes": [n.to_dict() for n in self.nodes],
        }


def _ev(claim_id: str) -> str:
    return by_id(claim_id).status


_CHAINS: tuple[EscalationChain, ...] = (
    EscalationChain(
        chain_id=ChainId.ACOUSTIC_TO_PLOT.value,
        nodes=(
            EscalationNode(
                "A1", "Acoustic reading asserted as "
                "settled", "C09",
                ClaimStatus.STRONGLY_SUPPORTED.value,
                _ev("C09"), False,
            ),
            EscalationNode(
                "A2", "Assume recording is authentic "
                "and correctly synced", "",
                ClaimStatus.STRONGLY_SUPPORTED.value,
                ClaimStatus.UNRESOLVED.value, True,
            ),
            EscalationNode(
                "A3", "Multiple participants asserted "
                "as established", "C10",
                ClaimStatus.VERIFIED.value,
                _ev("C10"), False,
            ),
            EscalationNode(
                "A4", "Named organisation asserted as "
                "proven", "C11",
                ClaimStatus.VERIFIED.value,
                _ev("C11"), False,
                dissent_claim_id="C15",
            ),
        ),
    ),
    EscalationChain(
        chain_id=ChainId.KNOLL_TO_COVERUP.value,
        nodes=(
            EscalationNode(
                "K1", "Knoll perception asserted as "
                "proof of origin", "C14",
                ClaimStatus.STRONGLY_SUPPORTED.value,
                _ev("C14"), False,
                dissent_claim_id="C15",
            ),
            EscalationNode(
                "K2", "Assume directional hearing is "
                "reliable under gunfire", "",
                ClaimStatus.PLAUSIBLE.value,
                ClaimStatus.UNRESOLVED.value, True,
            ),
            EscalationNode(
                "K3", "Therefore a cover-up is "
                "asserted as fact", "",
                ClaimStatus.VERIFIED.value,
                ClaimStatus.SPECULATIVE.value, True,
            ),
        ),
    ),
    EscalationChain(
        chain_id=(
            ChainId.SINGLE_BULLET_TO_CERTAINTY.value
        ),
        nodes=(
            EscalationNode(
                "S1", "Single-bullet account asserted "
                "as certain", "C08",
                ClaimStatus.VERIFIED.value,
                _ev("C08"), False,
                dissent_claim_id="C09",
            ),
            EscalationNode(
                "S2", "Assume all wound timing is "
                "exactly fixed", "",
                ClaimStatus.STRONGLY_SUPPORTED.value,
                ClaimStatus.CONTESTED.value, True,
            ),
        ),
    ),
)


def chains() -> tuple[EscalationChain, ...]:
    return _CHAINS


def nodes() -> tuple[EscalationNode, ...]:
    out: list[EscalationNode] = []
    for ch in _CHAINS:
        out.extend(ch.nodes)
    return tuple(out)


def attempted_escalations() -> tuple[EscalationNode, ...]:
    return tuple(n for n in nodes() if n.is_escalation())


def flagged_escalations() -> tuple[EscalationNode, ...]:
    # DESi flags every node whose attempted standing
    # exceeds the evidence grade.
    return tuple(n for n in nodes() if n.is_escalation())


def escalation_resistance() -> float:
    """Fraction of attempted escalations that DESi
    neutralised (flagged and capped), in [0, 1]."""
    attempts = attempted_escalations()
    if not attempts:
        return 1.0
    neutralised = sum(
        1 for n in attempts
        if n in flagged_escalations()
        and not n.false_certainty_leak()
    )
    return _round(neutralised / len(attempts))


__all__ = [
    "CHAIN_IDS",
    "ChainId",
    "EscalationChain",
    "EscalationNode",
    "attempted_escalations",
    "chains",
    "escalation_resistance",
    "flagged_escalations",
    "nodes",
]
