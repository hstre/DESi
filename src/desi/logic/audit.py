"""LogicalAuditor — orchestrator for the v1.2 belief gate.

Pipeline::

    audit(text, *, source_metadata=None) ────────────────────►
        PremiseExtractor.extract(text)
            │
            ▼
        try_each_rule(propositions)        ── matches → LOGICALLY_SUPPORTED
            │ (no match)                                  + ProofChain
            ▼
        detect_gap(propositions)
            ├── AUTHORITY_CLAIM     → GAP_DETECTED       (no bridge)
            ├── NO_EXPLICIT_CHAIN    → GAP_DETECTED       (no bridge)
            ├── UNREACHABLE          → LOGICALLY_REJECTED
            └── MISSING_BRIDGE        → BRIDGE_REQUIRED   + propose_bridge

Authority-independence is enforced at the boundary: the
``source_metadata`` kwarg is accepted (so that callers don't need
to filter their context manually) but it is **never** read inside
the auditor. The boundary check is verified by the v1.2
authority-invariant tests.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..memory.claim import Claim, ClaimState, Provenance
from .bridge_claims import BridgeClaim, propose_bridge
from .gap_detector import Gap, GapKind, detect_gap
from .inference import InferenceMatch, InferenceRule, try_each_rule
from .premises import PremiseExtractor, Propositions
from .proof_chain import ProofChain


class LogicalState(str, Enum):
    """The five states a claim moves through under audit.

    Mirrors the new :class:`desi.memory.claim.ClaimState` values.
    Keeping a parallel enum here lets the logic layer be self-
    contained for tests that don't care about Claim construction.
    """

    UNDER_LOGICAL_AUDIT = "under_logical_audit"
    GAP_DETECTED = "gap_detected"
    BRIDGE_REQUIRED = "bridge_required"
    LOGICALLY_SUPPORTED = "logically_supported"
    LOGICALLY_REJECTED = "logically_rejected"


def _audit_claim_id(text: str) -> str:
    h = hashlib.sha256(text.strip().lower().encode("utf-8"))
    return "ac_" + h.hexdigest()[:16]


@dataclass(frozen=True)
class AuditResult:
    """Output of :meth:`LogicalAuditor.audit`."""

    audit_id: str
    text: str
    state: LogicalState
    propositions: Propositions
    rule: InferenceRule | None = None
    gap: Gap | None = None
    bridges: tuple[BridgeClaim, ...] = ()
    proof_chain: ProofChain | None = None
    rationale: str = ""
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @property
    def claim_state(self) -> ClaimState:
        return ClaimState(self.state.value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "state": self.state.value,
            "rule": self.rule.value if self.rule else None,
            "rationale": self.rationale,
            "premise_ids": list(self.propositions.premise_ids),
            "bridge_ids": [b.bridge_id for b in self.bridges],
            "proof_chain": (
                self.proof_chain.to_dict() if self.proof_chain else None
            ),
            "gap": self.gap.to_dict() if self.gap else None,
        }


class LogicalAuditor:
    """The authority-free belief gate.

    Construction is parameter-free in v1.2. The auditor is stateless
    and deterministic: identical input text → identical
    :class:`AuditResult`.
    """

    def __init__(
        self,
        *,
        ledger: Any | None = None,
    ) -> None:
        self._extractor = PremiseExtractor()
        self._ledger = ledger

    def audit(
        self,
        text: str,
        *,
        claim_id: str | None = None,
        source_metadata: dict[str, Any] | None = None,
    ) -> AuditResult:
        """Audit ``text``; return an :class:`AuditResult`.

        The ``source_metadata`` kwarg is **deliberately ignored**.
        It is accepted so that callers passing a per-document audit
        record do not need to drop the field by hand, and so that
        the authority-invariant tests can pass arbitrary metadata
        without it leaking into the verdict.
        """
        del source_metadata  # v1.2 invariant L1/L2/L3 — never read.
        ac_id = claim_id or _audit_claim_id(text)
        self._log("LOGICAL_AUDIT_STARTED", {
            "audit_id": ac_id,
            "text_length": len(text),
        })

        propositions = self._extractor.extract(text)
        if not propositions.has_explicit_chain:
            return self._classify_gap(ac_id, text, propositions)

        match = try_each_rule(propositions)
        if match is not None:
            chain = ProofChain(
                claim_id=ac_id,
                rule_type=match.rule,
                premise_ids=match.used_premise_ids,
                bridge_ids=(),
            )
            self._log("LOGICAL_PROOF_ACCEPTED", {
                "audit_id": ac_id,
                "rule": match.rule.value,
                "replay_hash": chain.replay_hash,
                "premise_ids": list(chain.premise_ids),
            })
            return AuditResult(
                audit_id=ac_id,
                text=text,
                state=LogicalState.LOGICALLY_SUPPORTED,
                propositions=propositions,
                rule=match.rule,
                proof_chain=chain,
                rationale=(
                    f"inference rule {match.rule.value} matches the "
                    f"premises and conclusion."
                ),
            )

        return self._classify_gap(ac_id, text, propositions)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _classify_gap(
        self,
        ac_id: str,
        text: str,
        props: Propositions,
    ) -> AuditResult:
        gap = detect_gap(props)
        if gap.kind == GapKind.MISSING_BRIDGE:
            bridge = propose_bridge(props, gap)
            bridges = (bridge,) if bridge is not None else ()
            self._log("LOGICAL_BRIDGE_CREATED", {
                "audit_id": ac_id,
                "bridge_id": bridge.bridge_id if bridge else "",
                "bridge_text": bridge.text if bridge else "",
            })
            return AuditResult(
                audit_id=ac_id,
                text=text,
                state=LogicalState.BRIDGE_REQUIRED,
                propositions=props,
                gap=gap,
                bridges=bridges,
                rationale=gap.rationale,
            )
        if gap.kind == GapKind.UNREACHABLE:
            self._log("LOGICAL_PROOF_REJECTED", {
                "audit_id": ac_id,
                "reason": "unreachable",
                "rationale": gap.rationale,
            })
            return AuditResult(
                audit_id=ac_id,
                text=text,
                state=LogicalState.LOGICALLY_REJECTED,
                propositions=props,
                gap=gap,
                rationale=gap.rationale,
            )
        # AUTHORITY_CLAIM and NO_EXPLICIT_CHAIN both produce
        # GAP_DETECTED — the directive's terminology for "no chain
        # yet, please make the reasoning explicit."
        self._log("LOGICAL_GAP_DETECTED", {
            "audit_id": ac_id,
            "kind": gap.kind.value,
            "rationale": gap.rationale,
        })
        return AuditResult(
            audit_id=ac_id,
            text=text,
            state=LogicalState.GAP_DETECTED,
            propositions=props,
            gap=gap,
            rationale=gap.rationale,
        )

    def _log(self, event_name: str, payload: dict[str, Any]) -> None:
        if self._ledger is None:
            return
        from ..evolution.ledger import LedgerEventType
        event_map = {
            "LOGICAL_AUDIT_STARTED":
                LedgerEventType.LOGICAL_AUDIT_STARTED,
            "LOGICAL_GAP_DETECTED":
                LedgerEventType.LOGICAL_GAP_DETECTED,
            "LOGICAL_BRIDGE_CREATED":
                LedgerEventType.LOGICAL_BRIDGE_CREATED,
            "LOGICAL_PROOF_ACCEPTED":
                LedgerEventType.LOGICAL_PROOF_ACCEPTED,
            "LOGICAL_PROOF_REJECTED":
                LedgerEventType.LOGICAL_PROOF_REJECTED,
        }
        self._ledger.append(event_map[event_name], payload)


def replay(chain: ProofChain) -> str:
    """Recompute the chain's hash from its content.

    Identity utility: confirms that two :class:`ProofChain` instances
    with the same content (potentially loaded from disk) carry the
    same ``replay_hash``. INV-L4: every LOGICALLY_SUPPORTED claim
    must be replayable.
    """
    return chain.replay_hash


__all__ = [
    "AuditResult",
    "LogicalAuditor",
    "LogicalState",
    "replay",
]
