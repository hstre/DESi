"""Aufgabe 8 — cross-frame probe.

Combines the v3.13 ``FrameTensionRouter`` with the v2.7
``CAUSAL_CHAIN`` rule. The question is: *of the attacks that
CAUSAL_CHAIN alone misclassifies as supported, how many would
the v3.13 routing layer have blocked?*

We feed each attack to the router under a deliberately misleading
outer context (the v3.13 routing gate sees ``Frame: <something>``
that conflicts with the inner claim). The router can intercept
attacks the rule alone cannot.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..frame_tension_integration import (
    FrameRoutingLedgerEvent,
    FrameTensionRouter,
)
from .cases import ALL_ADVERSARIAL_CASES, AttackFamily
from .runner import AdversarialOutcome, run_attacks


# Per-family misleading outer attached to each attack so the
# routing gate has a meaningful comparison to make. Each entry
# pairs an outer-frame marker that *conflicts* with the typical
# inner content of that family.
_FAMILY_OUTER: dict[AttackFamily, str] = {
    AttackFamily.A_HIDDEN_NEGATION:     "Frame: formal logic",
    AttackFamily.B_QUANTIFIER_DRIFT:    "Frame: tool computable",
    AttackFamily.C_AUTHORITY_INSERTION: "Frame: empirical causal",
    AttackFamily.D_METAPHOR_INSERTION:  "Frame: thermodynamic",
    AttackFamily.E_FRAME_SWITCH:        "Frame: information-theoretic",
    AttackFamily.F_TOOL_CONTAMINATION:  "Frame: metaphorical",
    AttackFamily.G_CYCLE_DISGUISE:      "Frame: empirical causal",
    AttackFamily.H_SEMANTIC_LEAP:       "Frame: ontological distinguishability",
}


@dataclass(frozen=True)
class CrossFrameOutcome:
    case_id: str
    chain_only_supported: bool
    routing_event: str
    routing_allowed: bool
    routing_prevented_attack: bool
    combined_false_support: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "chain_only_supported": self.chain_only_supported,
            "routing_event": self.routing_event,
            "routing_allowed": self.routing_allowed,
            "routing_prevented_attack": self.routing_prevented_attack,
            "combined_false_support": self.combined_false_support,
        }


@dataclass(frozen=True)
class CrossFrameSummary:
    total: int
    chain_only_attacks: int
    routing_prevented_attacks: int
    combined_false_support: int

    def to_dict(self) -> dict[str, int]:
        return {
            "total": self.total,
            "chain_only_attacks": self.chain_only_attacks,
            "routing_prevented_attacks": self.routing_prevented_attacks,
            "combined_false_support": self.combined_false_support,
        }


def run_cross_frame(
    attack_outcomes: tuple[AdversarialOutcome, ...] | None = None,
) -> tuple[CrossFrameSummary, tuple[CrossFrameOutcome, ...]]:
    if attack_outcomes is None:
        attack_outcomes = run_attacks()
    family_map = {c.case_id: c.attack_family for c in ALL_ADVERSARIAL_CASES}
    router = FrameTensionRouter()
    when = datetime(2026, 5, 16, 0, 0, 0, tzinfo=timezone.utc)
    out: list[CrossFrameOutcome] = []
    for ao in attack_outcomes:
        family = family_map[ao.case_id]
        outer = _FAMILY_OUTER[family]
        rd = router.route(
            claim_id=f"redteam:{ao.case_id}",
            claim_text=ao.text,
            inherited_context_text=outer,
            recorded_at=when,
        )
        chain_supported = ao.attack_succeeded
        routing_allowed = (
            rd.event is FrameRoutingLedgerEvent.FRAME_ROUTING_ALLOWED
        )
        # A routing block of a chain-only attack is a "prevented
        # attack" — the chain layer would have supported it but
        # the v3.13 gate refuses to route.
        routing_prevented_attack = chain_supported and not routing_allowed
        # Combined false-support: both layers let the attack
        # through (chain supports + routing allows).
        combined_false_support = chain_supported and routing_allowed
        out.append(CrossFrameOutcome(
            case_id=ao.case_id,
            chain_only_supported=chain_supported,
            routing_event=rd.event.value,
            routing_allowed=routing_allowed,
            routing_prevented_attack=routing_prevented_attack,
            combined_false_support=combined_false_support,
        ))

    summary = CrossFrameSummary(
        total=len(out),
        chain_only_attacks=sum(1 for c in out if c.chain_only_supported),
        routing_prevented_attacks=sum(
            1 for c in out if c.routing_prevented_attack
        ),
        combined_false_support=sum(
            1 for c in out if c.combined_false_support
        ),
    )
    return summary, tuple(out)


__all__ = [
    "CrossFrameOutcome",
    "CrossFrameSummary",
    "run_cross_frame",
]
