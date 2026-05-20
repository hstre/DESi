"""Verdict + BridgeState — outcomes of a consilium deliberation.

Both enums are closed. A single unresolved gap (any role) drives
``VETO``. A domain-examiner ambiguity (without an unresolved gap)
drives ``NEEDS_MORE_PREMISES``. All four passing → ``ACCEPT_AS_BRIDGE``.
A bridge that fails the input contract → ``REJECT_BRIDGE``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .roles import ConsiliumRole


class Verdict(str, Enum):
    """The four closed verdicts the consilium may produce."""

    ACCEPT_AS_BRIDGE = "accept_as_bridge"
    REJECT_BRIDGE = "reject_bridge"
    NEEDS_MORE_PREMISES = "needs_more_premises"
    VETO = "veto"


class BridgeState(str, Enum):
    """The four lifecycle states of a bridge under consilium."""

    UNDER_CONSILIUM = "under_consilium"
    CONSILIUM_ACCEPTED = "consilium_accepted"
    CONSILIUM_REJECTED = "consilium_rejected"
    CONSILIUM_BLOCKED = "consilium_blocked"


def verdict_to_state(verdict: Verdict) -> BridgeState:
    """Map a final verdict to the resulting bridge state."""
    if verdict is Verdict.ACCEPT_AS_BRIDGE:
        return BridgeState.CONSILIUM_ACCEPTED
    if verdict is Verdict.REJECT_BRIDGE:
        return BridgeState.CONSILIUM_REJECTED
    # VETO and NEEDS_MORE_PREMISES both block the bridge — the
    # caller may re-submit with more premises or a different bridge.
    return BridgeState.CONSILIUM_BLOCKED


@dataclass(frozen=True)
class ConsiliumVerdict:
    """The aggregated outcome of one consilium session.

    Frozen so it can be appended to the ledger and round-tripped
    without copying. The ``per_role`` mapping is keyed by
    :class:`ConsiliumRole` for stable lookup.
    """

    bridge_id: str
    source_claim_id: str
    verdict: Verdict
    bridge_state: BridgeState
    blocking_roles: tuple[ConsiliumRole, ...] = ()
    rationale: str = ""
    per_role_unresolved: dict[ConsiliumRole, bool] = field(
        default_factory=dict,
    )
    per_role_needs_more: dict[ConsiliumRole, bool] = field(
        default_factory=dict,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bridge_id": self.bridge_id,
            "source_claim_id": self.source_claim_id,
            "verdict": self.verdict.value,
            "bridge_state": self.bridge_state.value,
            "blocking_roles": [r.value for r in self.blocking_roles],
            "rationale": self.rationale,
            "per_role_unresolved": {
                r.value: v for r, v in self.per_role_unresolved.items()
            },
            "per_role_needs_more": {
                r.value: v for r, v in self.per_role_needs_more.items()
            },
        }


__all__ = [
    "BridgeState",
    "ConsiliumVerdict",
    "Verdict",
    "verdict_to_state",
]
