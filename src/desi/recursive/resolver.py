"""RecursiveResolver — walks the bridge dependency graph (v1.4).

A recursive resolution has five possible final states (closed enum):

* ``RESOLUTION_COMPLETE``         — every node in the dependency
  graph closed without a block.
* ``RESOLUTION_INCOMPLETE``        — the resolver could not reach a
  terminal verdict for at least one node, but no hard block was
  raised. (Reserved for future use; v1.4 always lands on one of
  the other four.)
* ``RESOLUTION_BLOCKED``           — at least one bridge was vetoed
  by consilium, or a leaf claim was logically rejected. Per
  INV-R3 the block propagates to every ancestor.
* ``RESOLUTION_CYCLE_DETECTED``     — entering a child would revisit
  an ancestor; the resolver halts immediately (INV-R4).
* ``RESOLUTION_DEPTH_EXCEEDED``    — depth went past
  :data:`DEFAULT_MAX_DEPTH` (or the caller-supplied cap).

Authority-independence: ``source_metadata`` is accepted on the
resolver entry point and immediately dropped (INV-R6). The
:class:`LogicalAuditor` and :class:`BridgeConsilium` invocations
each pass through identical ``source_metadata=None`` so the
guarantee carries end-to-end.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..consilium import (
    BridgeConsilium,
    BridgeState,
    ConsiliumRole,
    Verdict,
)
from ..logic import LogicalAuditor, LogicalState
from ..logic.gap_detector import GapKind
from ..logic.premises import PremiseKind
from .cycle_detector import CycleHit, check_for_cycle
from .depth_guard import DEFAULT_MAX_DEPTH, DepthExceeded, check_depth
from .graph import GraphNode, ResolutionGraph, node_id
from .replay import ResolutionReplay


class ResolutionState(str, Enum):
    """The five closed final states of a recursive resolution."""

    RESOLUTION_COMPLETE = "resolution_complete"
    RESOLUTION_INCOMPLETE = "resolution_incomplete"
    RESOLUTION_BLOCKED = "resolution_blocked"
    RESOLUTION_CYCLE_DETECTED = "resolution_cycle_detected"
    RESOLUTION_DEPTH_EXCEEDED = "resolution_depth_exceeded"


class BlockingReason(str, Enum):
    """v1.7 — closed taxonomy for *why* a resolution was blocked.

    Set on the result whenever ``final_state`` is
    :attr:`ResolutionState.RESOLUTION_BLOCKED`. The five values are
    disjoint and exhaustive within the v1.7 surface; they capture
    the distinction between a *parser failure* (the system didn't
    understand the input) and an *actual logical block* (the
    system understood and rejected on principled grounds).

    * ``INVALID_INFERENCE``        — an inference rule was attempted
      and the conclusion does not follow from the premises (e.g.
      bad transitivity in B6).
    * ``REAL_LOGICAL_GAP``         — a real missing premise that no
      bridge / counterexample / authority match resolves. Typically
      the LOGICIAN's structural-disconnect signal.
    * ``PARSER_UNSUPPORTED_FORM``  — the premise extractor could not
      structure the input (atomic premise or conclusion, no
      explicit chain). Block-by-incomprehension, not by logical
      pushback.
    * ``AUTHORITY_CLAIM``          — an "X says Y" framing was
      detected; authority is never grounds for promotion.
    * ``COUNTEREXAMPLE_FOUND``      — the SKEPTIC surfaced an
      adversarial condition (user-supplied or the v1.6 auto-veto on
      GENERIC_FALLBACK).
    """

    INVALID_INFERENCE = "invalid_inference"
    REAL_LOGICAL_GAP = "real_logical_gap"
    PARSER_UNSUPPORTED_FORM = "parser_unsupported_form"
    AUTHORITY_CLAIM = "authority_claim"
    COUNTEREXAMPLE_FOUND = "counterexample_found"


@dataclass(frozen=True)
class RecursiveResolutionResult:
    """Output of :meth:`RecursiveResolver.resolve`.

    The four ``*_claim_ids`` fields are sorted for deterministic
    serialisation; the resolver populates them as plain sets at
    walk time and converts to sorted tuples on return.

    v1.7: ``blocking_reason`` is set whenever ``final_state`` is
    :attr:`ResolutionState.RESOLUTION_BLOCKED`. It carries one of
    the five :class:`BlockingReason` values so downstream consumers
    can distinguish a real logical block from a parser failure.
    """

    root_claim_id: str
    final_state: ResolutionState
    resolved_claims: tuple[str, ...] = ()
    open_gaps: tuple[str, ...] = ()
    blocked_claims: tuple[str, ...] = ()
    depth_reached: int = 0
    replay_hash: str = ""
    cycle_path: tuple[str, ...] = ()
    rationale: str = ""
    blocking_reason: BlockingReason | None = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_claim_id": self.root_claim_id,
            "final_state": self.final_state.value,
            "resolved_claims": list(self.resolved_claims),
            "open_gaps": list(self.open_gaps),
            "blocked_claims": list(self.blocked_claims),
            "depth_reached": self.depth_reached,
            "replay_hash": self.replay_hash,
            "cycle_path": list(self.cycle_path),
            "rationale": self.rationale,
            "blocking_reason": (
                self.blocking_reason.value if self.blocking_reason else None
            ),
        }


# ---------------------------------------------------------------------------
# Internal per-node walker result
# ---------------------------------------------------------------------------


@dataclass
class _NodeOutcome:
    """Per-node return shape used during the recursive walk."""

    state: ResolutionState
    resolved: set[str] = field(default_factory=set)
    open_gaps: set[str] = field(default_factory=set)
    blocked: set[str] = field(default_factory=set)
    depth_reached: int = 0
    cycle_path: tuple[str, ...] = ()
    rationale: str = ""
    blocking_reason: BlockingReason | None = None


class RecursiveResolver:
    """Orchestrator for the v1.4 recursive bridge resolution.

    Construction takes optional dependency injections so the test
    suite can drive scripted audits and consiliums without touching
    the real LogicalAuditor / BridgeConsilium. Production callers
    pass nothing and get the real components.
    """

    def __init__(
        self,
        *,
        auditor: LogicalAuditor | Any | None = None,
        consilium: BridgeConsilium | Any | None = None,
        ledger: Any | None = None,
    ) -> None:
        self._auditor = auditor or LogicalAuditor()
        self._consilium = consilium or BridgeConsilium()
        self._ledger = ledger

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def resolve(
        self,
        claim_text: str,
        *,
        max_depth: int = DEFAULT_MAX_DEPTH,
        context: str = "",
        additional_conditions: tuple[str, ...] = (),
        source_metadata: dict[str, Any] | None = None,
    ) -> RecursiveResolutionResult:
        """Resolve ``claim_text`` recursively.

        ``source_metadata`` is accepted for API parity with the v1.2
        auditor and v1.3 consilium; the resolver immediately drops
        it (INV-R6). Same contract as the underlying components —
        the metadata is never read.

        v1.6: ``context`` (e.g. ``"financial_newspaper"``) and
        ``additional_conditions`` are threaded through every
        consilium call inside the walk. No silent empty calls — the
        DOMAIN_EXAMINER and the SKEPTIC see exactly what the caller
        provided.
        """
        del source_metadata  # INV-R6
        graph = ResolutionGraph()
        root_id = node_id(claim_text)
        self._context = context
        self._additional_conditions = tuple(additional_conditions)
        self._emit("RECURSIVE_RESOLUTION_STARTED", {
            "root_claim_id": root_id,
            "max_depth": max_depth,
            "context": context,
            "additional_conditions": list(additional_conditions),
        })
        outcome = self._resolve_node(
            claim_text=claim_text,
            depth=0,
            max_depth=max_depth,
            ancestors=(),
            graph=graph,
        )
        replay = ResolutionReplay(
            root_node_id=root_id,
            sorted_node_ids=graph.canonical_nodes(),
            sorted_edges=graph.canonical_edges(),
            final_state=outcome.state.value,
            depth_reached=outcome.depth_reached,
        )
        result = RecursiveResolutionResult(
            root_claim_id=root_id,
            final_state=outcome.state,
            resolved_claims=tuple(sorted(outcome.resolved)),
            open_gaps=tuple(sorted(outcome.open_gaps)),
            blocked_claims=tuple(sorted(outcome.blocked)),
            depth_reached=outcome.depth_reached,
            replay_hash=replay.replay_hash,
            cycle_path=outcome.cycle_path,
            rationale=outcome.rationale,
            blocking_reason=outcome.blocking_reason if (
                outcome.state is ResolutionState.RESOLUTION_BLOCKED
            ) else None,
        )
        self._emit_outcome(result)
        return result

    # ------------------------------------------------------------------
    # Recursive walker
    # ------------------------------------------------------------------

    def _resolve_node(
        self,
        *,
        claim_text: str,
        depth: int,
        max_depth: int,
        ancestors: tuple[str, ...],
        graph: ResolutionGraph,
    ) -> _NodeOutcome:
        nid = node_id(claim_text)

        # Cycle check FIRST so a cycle never silently truncates.
        cycle = check_for_cycle(nid, ancestors)
        if cycle is not None:
            self._emit("RECURSIVE_CYCLE_DETECTED", {
                "node_id": nid,
                "cycle_path": list(cycle.cycle_path),
            })
            return _NodeOutcome(
                state=ResolutionState.RESOLUTION_CYCLE_DETECTED,
                cycle_path=cycle.cycle_path,
                depth_reached=depth,
                open_gaps={nid},
                rationale=(
                    "cycle detected: "
                    + " → ".join(cycle.cycle_path)
                ),
            )

        # Depth check.
        depth_violation = check_depth(depth, max_depth)
        if depth_violation is not None:
            self._emit("RECURSIVE_DEPTH_EXCEEDED", {
                "node_id": nid,
                "current_depth": depth_violation.current_depth,
                "max_depth": depth_violation.max_depth,
            })
            return _NodeOutcome(
                state=ResolutionState.RESOLUTION_DEPTH_EXCEEDED,
                depth_reached=depth,
                open_gaps={nid},
                rationale=(
                    f"depth {depth_violation.current_depth} > "
                    f"max_depth {depth_violation.max_depth}"
                ),
            )

        graph.add_node(claim_text, depth=depth)
        self._emit("RECURSIVE_NODE_ENTERED", {
            "node_id": nid,
            "depth": depth,
        })

        # Audit the claim text. NOTE: source_metadata is omitted on
        # purpose so the auditor cannot read anything authority-like.
        audit = self._auditor.audit(claim_text)

        if audit.state == LogicalState.LOGICALLY_SUPPORTED:
            self._emit("RECURSIVE_NODE_RESOLVED", {
                "node_id": nid, "via": "audit_supported", "depth": depth,
            })
            return _NodeOutcome(
                state=ResolutionState.RESOLUTION_COMPLETE,
                resolved={nid},
                depth_reached=depth,
                rationale="audit returned LOGICALLY_SUPPORTED.",
            )

        if audit.state == LogicalState.LOGICALLY_REJECTED:
            reason = _classify_audit_block(audit)
            self._emit("RECURSIVE_NODE_BLOCKED", {
                "node_id": nid,
                "reason": "logically_rejected",
                "blocking_reason": reason.value,
                "depth": depth,
            })
            return _NodeOutcome(
                state=ResolutionState.RESOLUTION_BLOCKED,
                blocked={nid},
                open_gaps={nid},
                depth_reached=depth,
                rationale="audit returned LOGICALLY_REJECTED.",
                blocking_reason=reason,
            )

        if audit.state == LogicalState.GAP_DETECTED:
            # Two cases:
            # * depth == 0  → the root has no chain; cannot resolve.
            # * depth > 0   → the bridge is a leaf proposition; the
            #                  parent's consilium has already vetted it.
            if depth == 0:
                reason = _classify_audit_block(audit)
                self._emit("RECURSIVE_NODE_BLOCKED", {
                    "node_id": nid,
                    "reason": "root_has_no_chain",
                    "blocking_reason": reason.value,
                    "depth": depth,
                })
                return _NodeOutcome(
                    state=ResolutionState.RESOLUTION_BLOCKED,
                    blocked={nid},
                    open_gaps={nid},
                    depth_reached=depth,
                    rationale=(
                        "root claim is GAP_DETECTED — no chain to "
                        "resolve."
                    ),
                    blocking_reason=reason,
                )
            self._emit("RECURSIVE_NODE_RESOLVED", {
                "node_id": nid,
                "via": "leaf_consilium_accepted",
                "depth": depth,
            })
            return _NodeOutcome(
                state=ResolutionState.RESOLUTION_COMPLETE,
                resolved={nid},
                depth_reached=depth,
                rationale=(
                    "leaf bridge — accepted by consilium at the "
                    "parent and structurally atomic."
                ),
            )

        # BRIDGE_REQUIRED — every bridge gets its own consilium, and
        # accepted bridges are recursively resolved. The parent id
        # joins ``resolved`` only on the COMPLETE return; if any
        # subtree blocks, the parent never enters resolved.
        agg_resolved: set[str] = set()
        agg_blocked: set[str] = set()
        agg_open: set[str] = set()
        agg_depth = depth
        all_complete = True
        rationale_parts: list[str] = []
        new_ancestors = ancestors + (nid,)

        node_block_reason: BlockingReason | None = None
        for bridge in audit.bridges:
            bridge_id = node_id(bridge.text)
            graph.add_node(bridge.text, depth=depth + 1)
            graph.add_edge(claim_text, bridge.text)

            cons = self._consilium.deliberate(
                bridge,
                source_claim_id=audit.audit_id,
                original_text=claim_text,
                context=getattr(self, "_context", ""),
                additional_conditions=getattr(
                    self, "_additional_conditions", (),
                ),
            )
            if cons.verdict.verdict is not Verdict.ACCEPT_AS_BRIDGE:
                consilium_reason = _classify_consilium_block(cons)
                self._emit("RECURSIVE_NODE_BLOCKED", {
                    "node_id": bridge_id,
                    "reason": f"consilium_{cons.verdict.verdict.value}",
                    "blocking_roles": [
                        r.value for r in cons.verdict.blocking_roles
                    ],
                    "blocking_reason": consilium_reason.value,
                    "depth": depth + 1,
                })
                agg_blocked.add(bridge_id)
                agg_open.add(bridge_id)
                all_complete = False
                rationale_parts.append(
                    f"bridge '{bridge.text}' → "
                    f"{cons.verdict.verdict.value}"
                )
                # First consilium block at this level seeds the
                # node's blocking_reason; subsequent ones do not
                # overwrite — the first observable cause wins.
                if node_block_reason is None:
                    node_block_reason = consilium_reason
                continue

            # Bridge accepted — recurse on the bridge text.
            child = self._resolve_node(
                claim_text=bridge.text,
                depth=depth + 1,
                max_depth=max_depth,
                ancestors=new_ancestors,
                graph=graph,
            )
            agg_depth = max(agg_depth, child.depth_reached)

            # Cycle / depth: propagate immediately.
            if child.state in (
                ResolutionState.RESOLUTION_CYCLE_DETECTED,
                ResolutionState.RESOLUTION_DEPTH_EXCEEDED,
            ):
                # Carry the child's open_gaps up so the root surfaces them.
                return _NodeOutcome(
                    state=child.state,
                    resolved=agg_resolved | child.resolved,
                    open_gaps=agg_open | child.open_gaps,
                    blocked=agg_blocked | child.blocked,
                    depth_reached=child.depth_reached,
                    cycle_path=child.cycle_path,
                    rationale=child.rationale,
                )

            agg_resolved |= child.resolved
            agg_blocked |= child.blocked
            agg_open |= child.open_gaps
            if child.state is not ResolutionState.RESOLUTION_COMPLETE:
                all_complete = False
                rationale_parts.append(
                    f"bridge '{bridge.text}' subtree → "
                    f"{child.state.value}"
                )
                # Inherit the child's blocking_reason if we don't
                # already have one from a sibling consilium veto.
                if (node_block_reason is None
                        and child.blocking_reason is not None):
                    node_block_reason = child.blocking_reason

        if not all_complete or agg_blocked:
            if node_block_reason is None:
                # Defensive fallback — should not normally trigger.
                node_block_reason = BlockingReason.REAL_LOGICAL_GAP
            self._emit("RECURSIVE_NODE_BLOCKED", {
                "node_id": nid,
                "reason": "child_blocked",
                "blocking_reason": node_block_reason.value,
                "depth": depth,
            })
            return _NodeOutcome(
                state=ResolutionState.RESOLUTION_BLOCKED,
                resolved=agg_resolved,
                open_gaps=agg_open | {nid},
                blocked=agg_blocked,
                depth_reached=agg_depth,
                rationale=(
                    "; ".join(rationale_parts)
                    or "at least one bridge subtree did not complete."
                ),
                blocking_reason=node_block_reason,
            )

        self._emit("RECURSIVE_NODE_RESOLVED", {
            "node_id": nid,
            "via": "all_bridges_resolved",
            "depth": depth,
        })
        return _NodeOutcome(
            state=ResolutionState.RESOLUTION_COMPLETE,
            resolved=agg_resolved | {nid},   # parent enters only on COMPLETE
            depth_reached=agg_depth,
            rationale="all bridge subtrees completed.",
        )

    # ------------------------------------------------------------------
    # Ledger helpers
    # ------------------------------------------------------------------

    def _emit(self, event_name: str, payload: dict[str, Any]) -> None:
        if self._ledger is None:
            return
        from ..evolution.ledger import LedgerEventType
        event_map = {
            "RECURSIVE_RESOLUTION_STARTED":
                LedgerEventType.RECURSIVE_RESOLUTION_STARTED,
            "RECURSIVE_NODE_ENTERED":
                LedgerEventType.RECURSIVE_NODE_ENTERED,
            "RECURSIVE_NODE_RESOLVED":
                LedgerEventType.RECURSIVE_NODE_RESOLVED,
            "RECURSIVE_NODE_BLOCKED":
                LedgerEventType.RECURSIVE_NODE_BLOCKED,
            "RECURSIVE_CYCLE_DETECTED":
                LedgerEventType.RECURSIVE_CYCLE_DETECTED,
            "RECURSIVE_DEPTH_EXCEEDED":
                LedgerEventType.RECURSIVE_DEPTH_EXCEEDED,
            "RECURSIVE_RESOLUTION_COMPLETED":
                LedgerEventType.RECURSIVE_RESOLUTION_COMPLETED,
        }
        self._ledger.append(event_map[event_name], payload)

    def _emit_outcome(self, result: RecursiveResolutionResult) -> None:
        self._emit("RECURSIVE_RESOLUTION_COMPLETED", {
            "root_claim_id": result.root_claim_id,
            "final_state": result.final_state.value,
            "depth_reached": result.depth_reached,
            "replay_hash": result.replay_hash,
            "n_resolved": len(result.resolved_claims),
            "n_blocked": len(result.blocked_claims),
        })


# ---------------------------------------------------------------------------
# Blocking-reason classifiers (v1.7)
# ---------------------------------------------------------------------------


def _classify_audit_block(audit) -> BlockingReason:
    """Classify an audit-level block into a v1.7 BlockingReason.

    Distinguishes "the parser didn't understand" (atomic / no chain)
    from "the inference is structurally invalid" (transitivity that
    doesn't close, etc.) — INV: parser failure must never be
    reported as INVALID_INFERENCE.
    """
    if audit.state is LogicalState.LOGICALLY_REJECTED:
        # v1.8: authority premises now reach LOGICALLY_REJECTED via
        # the early-exit in the auditor. Classify on the gap kind
        # first so the directive's "AUTHORITY_CLAIM under
        # LOGICALLY_REJECTED" mapping is honoured.
        if audit.gap is not None and audit.gap.kind is GapKind.AUTHORITY_CLAIM:
            return BlockingReason.AUTHORITY_CLAIM
        if audit.gap is not None and audit.gap.kind is GapKind.UNREACHABLE:
            conclusion = audit.propositions.conclusion
            if conclusion is None or conclusion.kind is PremiseKind.ATOMIC:
                return BlockingReason.PARSER_UNSUPPORTED_FORM
            return BlockingReason.INVALID_INFERENCE
        return BlockingReason.INVALID_INFERENCE
    if audit.state is LogicalState.GAP_DETECTED:
        if audit.gap is None:
            return BlockingReason.PARSER_UNSUPPORTED_FORM
        if audit.gap.kind is GapKind.AUTHORITY_CLAIM:
            return BlockingReason.AUTHORITY_CLAIM
        if audit.gap.kind is GapKind.NO_EXPLICIT_CHAIN:
            return BlockingReason.PARSER_UNSUPPORTED_FORM
        if audit.gap.kind is GapKind.UNREACHABLE:
            conclusion = audit.propositions.conclusion
            if conclusion is None or conclusion.kind is PremiseKind.ATOMIC:
                return BlockingReason.PARSER_UNSUPPORTED_FORM
            return BlockingReason.INVALID_INFERENCE
        # MISSING_BRIDGE shouldn't reach this path (it leads to
        # BRIDGE_REQUIRED, not GAP_DETECTED) but be defensive.
        return BlockingReason.REAL_LOGICAL_GAP
    return BlockingReason.REAL_LOGICAL_GAP


def _classify_consilium_block(cons_result) -> BlockingReason:
    """Classify a consilium-level block into a v1.7 BlockingReason.

    Priority:
    1. SKEPTIC in blocking_roles → COUNTEREXAMPLE_FOUND
       (covers both v1.3 explicit counterexamples and v1.6 auto-veto
       on GENERIC_FALLBACK).
    2. LOGICIAN-only block → REAL_LOGICAL_GAP (structural disconnect).
    3. REJECT_BRIDGE (input contract failure) → REAL_LOGICAL_GAP.
    4. Default → REAL_LOGICAL_GAP.
    """
    verdict = cons_result.verdict.verdict
    if verdict is Verdict.REJECT_BRIDGE:
        return BlockingReason.REAL_LOGICAL_GAP
    blocking = set(cons_result.verdict.blocking_roles)
    if ConsiliumRole.SKEPTIC in blocking:
        return BlockingReason.COUNTEREXAMPLE_FOUND
    return BlockingReason.REAL_LOGICAL_GAP


__all__ = [
    "BlockingReason",
    "RecursiveResolutionResult",
    "RecursiveResolver",
    "ResolutionState",
]
