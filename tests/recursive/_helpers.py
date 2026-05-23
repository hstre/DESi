"""Shared test helpers — scripted Auditor / Consilium for v1.4.

The recursive resolver is testable with real components for R1 (a
single-bridge resolution that the v1.2 auditor naturally produces).
For R2 (two-bridge chain), R3 (blocked child), R4 (cycle), R5
(depth limit), and R6 (permutation), we inject deterministic
*scripts* keyed by claim text so the resolver's behaviour can be
exercised without coupling tests to the v1.2 phrase library.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from desi.consilium import (
    BridgeState,
    ConsiliumResult,
    ConsiliumRole,
    ConsiliumVerdict,
    Verdict,
)
from desi.consilium.consilium import CANONICAL_ROLE_ORDER
from desi.logic import (
    AuditResult,
    InferenceRule,
    LogicalState,
    PremiseExtractor,
    ProofChain,
)
from desi.logic.bridge_claims import BRIDGE_METHOD, BridgeClaim
from desi.memory.claim import Claim, ClaimState, Provenance


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).rstrip(".")


# ---------------------------------------------------------------------------
# Bridge factory
# ---------------------------------------------------------------------------


def make_bridge(text: str, *, source_run_id: str = "scripted") -> BridgeClaim:
    """Construct a v1.2-shaped BridgeClaim with the given text."""
    claim = Claim(
        content=text,
        method=BRIDGE_METHOD,
        state=ClaimState.PROPOSED,
        provenance=Provenance(
            source="scripted_test", run_id=source_run_id,
            operator_path=(BRIDGE_METHOD,),
        ),
    )
    import hashlib
    bid = "br_" + hashlib.sha256(text.lower().strip().encode()).hexdigest()[:12]
    return BridgeClaim(
        bridge_id=bid,
        text=text,
        claim=claim,
        rationale=f"scripted bridge for '{text}'",
    )


# ---------------------------------------------------------------------------
# Scripted auditor
# ---------------------------------------------------------------------------


def supported(text: str) -> AuditResult:
    """A scripted AuditResult that pretends ``text`` is supported."""
    import hashlib
    aid = "ac_" + hashlib.sha256(_norm(text).encode()).hexdigest()[:16]
    return AuditResult(
        audit_id=aid,
        text=text,
        state=LogicalState.LOGICALLY_SUPPORTED,
        propositions=PremiseExtractor().extract(text),
        rule=InferenceRule.SYLLOGISM,
        proof_chain=ProofChain(
            claim_id=aid,
            rule_type=InferenceRule.SYLLOGISM,
            premise_ids=("pr_a", "pr_b"),
        ),
        rationale="scripted: supported",
    )


def gap(text: str) -> AuditResult:
    """A scripted AuditResult: gap detected (leaf if depth>0)."""
    import hashlib
    aid = "ac_" + hashlib.sha256(_norm(text).encode()).hexdigest()[:16]
    return AuditResult(
        audit_id=aid,
        text=text,
        state=LogicalState.GAP_DETECTED,
        propositions=PremiseExtractor().extract(text),
        rationale="scripted: gap detected",
    )


def needs_bridge(text: str, *bridges: str) -> AuditResult:
    """A scripted AuditResult: BRIDGE_REQUIRED with the given bridge texts."""
    import hashlib
    aid = "ac_" + hashlib.sha256(_norm(text).encode()).hexdigest()[:16]
    return AuditResult(
        audit_id=aid,
        text=text,
        state=LogicalState.BRIDGE_REQUIRED,
        propositions=PremiseExtractor().extract(text),
        bridges=tuple(make_bridge(b) for b in bridges),
        rationale="scripted: bridge required",
    )


@dataclass
class ScriptedAuditor:
    """Routes ``audit(text)`` calls through a script keyed by the text."""

    script: dict[str, AuditResult] = field(default_factory=dict)

    def audit(self, text: str, *, source_metadata: Any = None) -> AuditResult:
        del source_metadata  # never read — invariance check
        key = _norm(text)
        if key in self.script:
            return self.script[key]
        # Default: GAP — handles "unknown" leaf claims.
        return gap(text)


# ---------------------------------------------------------------------------
# Scripted consilium
# ---------------------------------------------------------------------------


def _verdict(bridge_id: str, source_claim_id: str, verdict: Verdict,
              blocking_roles: tuple[ConsiliumRole, ...] = ()
              ) -> ConsiliumVerdict:
    state = (BridgeState.CONSILIUM_ACCEPTED
             if verdict is Verdict.ACCEPT_AS_BRIDGE
             else BridgeState.CONSILIUM_BLOCKED
             if verdict in (Verdict.VETO, Verdict.NEEDS_MORE_PREMISES)
             else BridgeState.CONSILIUM_REJECTED)
    return ConsiliumVerdict(
        bridge_id=bridge_id,
        source_claim_id=source_claim_id,
        verdict=verdict,
        bridge_state=state,
        blocking_roles=blocking_roles,
        rationale="scripted",
    )


def _consilium_result(bridge: BridgeClaim, source_claim_id: str,
                       verdict: Verdict,
                       blocking_roles: tuple[ConsiliumRole, ...] = ()
                       ) -> ConsiliumResult:
    return ConsiliumResult(
        bridge_id=bridge.bridge_id,
        source_claim_id=source_claim_id,
        bridge_text=bridge.text,
        role_order=CANONICAL_ROLE_ORDER,
        reviews=(),
        verdict=_verdict(bridge.bridge_id, source_claim_id, verdict,
                          blocking_roles),
        replay_hash="cr_scripted",
    )


@dataclass
class ScriptedConsilium:
    """Routes ``deliberate(bridge, ...)`` through a script keyed by
    the bridge text. Default verdict is ACCEPT_AS_BRIDGE so tests
    only need to enumerate the bridges they want to *block*.
    """

    blocked_bridges: dict[str, Verdict] = field(default_factory=dict)

    def deliberate(
        self,
        bridge: BridgeClaim,
        *,
        source_claim_id: str,
        original_text: str,
        additional_conditions: tuple[str, ...] = (),
        context: str = "",
        role_order: tuple = None,
        source_metadata: Any = None,
    ) -> ConsiliumResult:
        del source_metadata  # never read
        key = _norm(bridge.text)
        verdict = self.blocked_bridges.get(key, Verdict.ACCEPT_AS_BRIDGE)
        blocking = ((ConsiliumRole.SKEPTIC,)
                    if verdict is Verdict.VETO else ())
        return _consilium_result(
            bridge, source_claim_id, verdict, blocking,
        )


__all__ = [
    "ScriptedAuditor",
    "ScriptedConsilium",
    "gap",
    "make_bridge",
    "needs_bridge",
    "supported",
]
