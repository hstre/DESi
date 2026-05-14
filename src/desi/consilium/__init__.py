"""Authority-free bridge consilium (v1.3).

A bridge claim is never accepted because it is convenient,
intuitive, popular, repeated, highly cited, authored by experts,
or supported by institutional prestige.

A bridge claim may only be accepted if an adversarial consilium of
four roles (LOGICIAN, SKEPTIC, DOMAIN_EXAMINER, INTEGRATOR) fails
to find an unresolved logical gap. A single unresolved veto blocks
acceptance.

The consilium never reads author / title / source / citation_count /
document_count metadata, even when those values are stapled to the
context. ``source_metadata`` is accepted as a kwarg and immediately
dropped.
"""
from __future__ import annotations

from .consilium import BridgeConsilium, ConsiliumResult
from .counterexamples import (
    CounterexampleHit,
    MetaphorHit,
    find_counterexample,
    find_metaphor,
    supported_contexts,
)
from .obligations import (
    ClaimUpgradeError,
    promote_accepted_bridge,
    upgrade_original_claim,
)
from .replay import ConsiliumReplay
from .review import (
    ReviewContext,
    RoleReview,
    review_domain_examiner,
    review_integrator,
    review_logician,
    review_skeptic,
    run_role_reviews,
)
from .roles import CANONICAL_ROLE_ORDER, ConsiliumRole
from .verdict import (
    BridgeState,
    ConsiliumVerdict,
    Verdict,
    verdict_to_state,
)

__all__ = [
    "BridgeConsilium",
    "BridgeState",
    "CANONICAL_ROLE_ORDER",
    "ClaimUpgradeError",
    "ConsiliumReplay",
    "ConsiliumResult",
    "ConsiliumRole",
    "ConsiliumVerdict",
    "CounterexampleHit",
    "MetaphorHit",
    "ReviewContext",
    "RoleReview",
    "Verdict",
    "find_counterexample",
    "find_metaphor",
    "promote_accepted_bridge",
    "review_domain_examiner",
    "review_integrator",
    "review_logician",
    "review_skeptic",
    "run_role_reviews",
    "supported_contexts",
    "upgrade_original_claim",
    "verdict_to_state",
]
