"""BridgeConsilium — the v1.3 orchestrator.

A consilium session:

1. Validates the input contract (bridge_id, text, source_claim_id,
   rationale all non-empty). Hard-reject if not.
2. Runs the four roles. Reviews are independent.
3. Aggregates the reviews into a :class:`ConsiliumVerdict` using
   set-based logic (so role-order permutation is irrelevant).
4. Computes a deterministic ``replay_hash``.
5. Writes one entry per role + the verdict to the ledger.

Authority-independence: the ``source_metadata`` kwarg is accepted
for API completeness and immediately dropped. Same contract as the
v1.2 auditor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..logic.bridge_claims import BridgeClaim
from ..logic.premises import PremiseExtractor
from .replay import ConsiliumReplay
from .review import ReviewContext, RoleReview, run_role_reviews
from .roles import CANONICAL_ROLE_ORDER, ConsiliumRole
from .verdict import (
    BridgeState,
    ConsiliumVerdict,
    Verdict,
    verdict_to_state,
)


@dataclass(frozen=True)
class ConsiliumResult:
    """Full record of one consilium session."""

    bridge_id: str
    source_claim_id: str
    bridge_text: str
    role_order: tuple[ConsiliumRole, ...]
    reviews: tuple[RoleReview, ...]
    verdict: ConsiliumVerdict
    replay_hash: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @property
    def bridge_state(self) -> BridgeState:
        return self.verdict.bridge_state

    def to_dict(self) -> dict[str, Any]:
        return {
            "bridge_id": self.bridge_id,
            "source_claim_id": self.source_claim_id,
            "bridge_text": self.bridge_text,
            "role_order": [r.value for r in self.role_order],
            "reviews": [r.to_dict() for r in self.reviews],
            "verdict": self.verdict.to_dict(),
            "replay_hash": self.replay_hash,
        }


class BridgeConsilium:
    """Authority-free consilium that adversarially reviews bridge claims.

    Construction is parameter-free in v1.3. The optional ``ledger``
    receives one event per role review + one verdict event. The
    optional ``role_order`` argument to ``deliberate()`` reorders
    the ledger writes only; the verdict is set-based and therefore
    order-independent.
    """

    def __init__(self, *, ledger: Any | None = None) -> None:
        self._ledger = ledger

    def deliberate(
        self,
        bridge: BridgeClaim,
        *,
        source_claim_id: str,
        original_text: str,
        additional_conditions: tuple[str, ...] = (),
        context: str = "",
        role_order: tuple[ConsiliumRole, ...] | None = None,
        source_metadata: dict[str, Any] | None = None,
    ) -> ConsiliumResult:
        """Run the consilium; return the full result.

        ``source_metadata`` is accepted for API parity with the v1.2
        auditor but explicitly dropped on entry — INV-C2.
        """
        del source_metadata  # v1.3 INV-C2: never read author/title/source.

        # 1. Input contract.
        hard_reject = _hard_reject_reason(
            bridge=bridge,
            source_claim_id=source_claim_id,
            original_text=original_text,
        )
        if hard_reject is not None:
            verdict = ConsiliumVerdict(
                bridge_id=bridge.bridge_id,
                source_claim_id=source_claim_id,
                verdict=Verdict.REJECT_BRIDGE,
                bridge_state=BridgeState.CONSILIUM_REJECTED,
                blocking_roles=(),
                rationale=hard_reject,
            )
            replay = ConsiliumReplay(
                bridge_text=bridge.text,
                source_claim_id=source_claim_id,
                verdict=Verdict.REJECT_BRIDGE,
            )
            result = ConsiliumResult(
                bridge_id=bridge.bridge_id,
                source_claim_id=source_claim_id,
                bridge_text=bridge.text,
                role_order=role_order or CANONICAL_ROLE_ORDER,
                reviews=(),
                verdict=verdict,
                replay_hash=replay.replay_hash,
            )
            self._log_start(result)
            self._log_rejected(result)
            return result

        # 2. Role reviews.
        self._log_start_with_meta(bridge.bridge_id, source_claim_id)
        ctx = ReviewContext(
            bridge=bridge,
            source_claim_id=source_claim_id,
            original_text=original_text,
            additional_conditions=tuple(additional_conditions),
            context=context,
        )
        reviews = run_role_reviews(ctx, role_order=role_order)
        for review in reviews:
            self._log_role(bridge.bridge_id, review)

        # 3. Aggregate.
        verdict = self._aggregate(
            bridge_id=bridge.bridge_id,
            source_claim_id=source_claim_id,
            reviews=reviews,
        )

        # 4. Replay hash.
        premise_ids = _premise_ids_from(original_text)
        replay = ConsiliumReplay(
            bridge_text=bridge.text,
            source_claim_id=source_claim_id,
            verdict=verdict.verdict,
            premise_ids=premise_ids,
            conditions=tuple(additional_conditions),
            context=context,
        )

        result = ConsiliumResult(
            bridge_id=bridge.bridge_id,
            source_claim_id=source_claim_id,
            bridge_text=bridge.text,
            role_order=role_order or CANONICAL_ROLE_ORDER,
            reviews=reviews,
            verdict=verdict,
            replay_hash=replay.replay_hash,
        )

        # 5. Ledger writes for the final outcome.
        if verdict.verdict is Verdict.ACCEPT_AS_BRIDGE:
            self._log_accepted(result)
        elif verdict.verdict is Verdict.VETO:
            self._log_veto(result)
        else:
            self._log_rejected(result)
        return result

    # ------------------------------------------------------------------
    # Aggregation — set-based; role order is irrelevant (INV-C1).
    # ------------------------------------------------------------------

    def _aggregate(
        self,
        *,
        bridge_id: str,
        source_claim_id: str,
        reviews: tuple[RoleReview, ...],
    ) -> ConsiliumVerdict:
        per_unresolved = {r.role: r.unresolved_gap for r in reviews}
        per_needs_more = {r.role: r.needs_more_premises for r in reviews}
        # INV-C3: a single unresolved veto blocks.
        veto_roles = tuple(
            r.role for r in sorted(reviews, key=lambda r: r.role.value)
            if r.unresolved_gap
        )
        if veto_roles:
            rationale = "; ".join(
                f"{r.role.value}: {r.rationale}"
                for r in reviews if r.unresolved_gap
            )
            return ConsiliumVerdict(
                bridge_id=bridge_id,
                source_claim_id=source_claim_id,
                verdict=Verdict.VETO,
                bridge_state=BridgeState.CONSILIUM_BLOCKED,
                blocking_roles=veto_roles,
                rationale=rationale,
                per_role_unresolved=per_unresolved,
                per_role_needs_more=per_needs_more,
            )
        needs_more = tuple(
            r.role for r in sorted(reviews, key=lambda r: r.role.value)
            if r.needs_more_premises
        )
        if needs_more:
            rationale = "; ".join(
                f"{r.role.value}: {r.rationale}"
                for r in reviews if r.needs_more_premises
            )
            return ConsiliumVerdict(
                bridge_id=bridge_id,
                source_claim_id=source_claim_id,
                verdict=Verdict.NEEDS_MORE_PREMISES,
                bridge_state=BridgeState.CONSILIUM_BLOCKED,
                blocking_roles=needs_more,
                rationale=rationale,
                per_role_unresolved=per_unresolved,
                per_role_needs_more=per_needs_more,
            )
        return ConsiliumVerdict(
            bridge_id=bridge_id,
            source_claim_id=source_claim_id,
            verdict=Verdict.ACCEPT_AS_BRIDGE,
            bridge_state=BridgeState.CONSILIUM_ACCEPTED,
            blocking_roles=(),
            rationale="all four roles passed; no unresolved gap.",
            per_role_unresolved=per_unresolved,
            per_role_needs_more=per_needs_more,
        )

    # ------------------------------------------------------------------
    # Ledger helpers — every event is optional (ledger may be None).
    # ------------------------------------------------------------------

    def _emit(self, event_name: str, payload: dict[str, Any]) -> None:
        if self._ledger is None:
            return
        from ..evolution.ledger import LedgerEventType
        event_map = {
            "CONSILIUM_STARTED": LedgerEventType.CONSILIUM_STARTED,
            "CONSILIUM_ROLE_REVIEWED":
                LedgerEventType.CONSILIUM_ROLE_REVIEWED,
            "CONSILIUM_COUNTEREXAMPLE_FOUND":
                LedgerEventType.CONSILIUM_COUNTEREXAMPLE_FOUND,
            "CONSILIUM_VETO": LedgerEventType.CONSILIUM_VETO,
            "CONSILIUM_ACCEPTED": LedgerEventType.CONSILIUM_ACCEPTED,
            "CONSILIUM_REJECTED": LedgerEventType.CONSILIUM_REJECTED,
            "CLAIM_UPGRADED_BY_CONSILIUM":
                LedgerEventType.CLAIM_UPGRADED_BY_CONSILIUM,
        }
        self._ledger.append(event_map[event_name], payload)

    def _log_start(self, result: ConsiliumResult) -> None:
        self._emit("CONSILIUM_STARTED", {
            "bridge_id": result.bridge_id,
            "source_claim_id": result.source_claim_id,
            "role_order": [r.value for r in result.role_order],
        })

    def _log_start_with_meta(
        self, bridge_id: str, source_claim_id: str,
    ) -> None:
        self._emit("CONSILIUM_STARTED", {
            "bridge_id": bridge_id,
            "source_claim_id": source_claim_id,
        })

    def _log_role(self, bridge_id: str, review: RoleReview) -> None:
        self._emit("CONSILIUM_ROLE_REVIEWED", {
            "bridge_id": bridge_id,
            "role": review.role.value,
            "unresolved_gap": review.unresolved_gap,
            "needs_more_premises": review.needs_more_premises,
            "rationale": review.rationale,
            "findings": list(review.findings),
        })
        if any(f.startswith("counterexample:") for f in review.findings):
            self._emit("CONSILIUM_COUNTEREXAMPLE_FOUND", {
                "bridge_id": bridge_id,
                "role": review.role.value,
                "findings": list(review.findings),
                "rationale": review.rationale,
            })

    def _log_accepted(self, result: ConsiliumResult) -> None:
        self._emit("CONSILIUM_ACCEPTED", {
            "bridge_id": result.bridge_id,
            "source_claim_id": result.source_claim_id,
            "replay_hash": result.replay_hash,
        })

    def _log_veto(self, result: ConsiliumResult) -> None:
        self._emit("CONSILIUM_VETO", {
            "bridge_id": result.bridge_id,
            "source_claim_id": result.source_claim_id,
            "blocking_roles": [
                r.value for r in result.verdict.blocking_roles
            ],
            "rationale": result.verdict.rationale,
            "replay_hash": result.replay_hash,
        })

    def _log_rejected(self, result: ConsiliumResult) -> None:
        self._emit("CONSILIUM_REJECTED", {
            "bridge_id": result.bridge_id,
            "source_claim_id": result.source_claim_id,
            "verdict": result.verdict.verdict.value,
            "blocking_roles": [
                r.value for r in result.verdict.blocking_roles
            ],
            "rationale": result.verdict.rationale,
            "replay_hash": result.replay_hash,
        })


def _hard_reject_reason(
    *,
    bridge: BridgeClaim,
    source_claim_id: str,
    original_text: str,
) -> str | None:
    """Return a string describing why the input fails the contract,
    or ``None`` if the input is admissible."""
    if not bridge.bridge_id:
        return "bridge_id is required."
    if not bridge.text.strip():
        return "bridge text is required."
    if not source_claim_id:
        return "source_claim_id is required."
    if not bridge.rationale.strip():
        return "bridge rationale is required."
    if not original_text.strip():
        return "original_text is required."
    return None


def _premise_ids_from(text: str) -> tuple[str, ...]:
    props = PremiseExtractor().extract(text)
    return tuple(sorted(p.premise_id for p in props.premises))


__all__ = [
    "BridgeConsilium",
    "ConsiliumResult",
]
