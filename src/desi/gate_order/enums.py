"""Closed taxonomies — 7 gates × 8 candidate orderings."""
from __future__ import annotations

from enum import Enum


class Gate(str, Enum):
    G1_PREMISE_EXTRACTOR = "PremiseExtractor"
    G2_SPL               = "SPL"
    G3_FRAME_DECLARATION = "FrameDeclaration"
    G4_FRAME_TENSION     = "FrameTension"
    G5_ROUTER            = "FrameTensionRouter"
    G6_CAUSAL_CHAIN      = "CAUSAL_CHAIN"
    G7_SUSPENSION_GATE   = "SuspensionGate"


class OrderingName(str, Enum):
    CURRENT_ORDER                = "current_order"
    FRAME_TENSION_BEFORE_SPL     = "frame_tension_before_spl"
    ROUTER_BEFORE_FRAME_DECL     = "router_before_frame_declaration"
    CAUSAL_BEFORE_FRAME_TENSION  = "causal_before_frame_tension"
    SUSPENSION_BEFORE_CAUSAL     = "suspension_before_causal"
    MINIMAL_WITHOUT_CAUSAL_CHAIN = "minimal_without_causal_chain"
    MINIMAL_WITHOUT_FRAME_TENSION = "minimal_without_frame_tension"
    MAXIMAL_SAFE_STACK           = "maximal_safe_stack"


_CURRENT_ORDER: tuple[Gate, ...] = (
    Gate.G1_PREMISE_EXTRACTOR,
    Gate.G2_SPL,
    Gate.G3_FRAME_DECLARATION,
    Gate.G4_FRAME_TENSION,
    Gate.G5_ROUTER,
    Gate.G6_CAUSAL_CHAIN,
    Gate.G7_SUSPENSION_GATE,
)


def gate_sequence(order: OrderingName) -> tuple[Gate, ...]:
    if order is OrderingName.CURRENT_ORDER:
        return _CURRENT_ORDER
    if order is OrderingName.FRAME_TENSION_BEFORE_SPL:
        return (
            Gate.G1_PREMISE_EXTRACTOR,
            Gate.G4_FRAME_TENSION,
            Gate.G2_SPL,
            Gate.G3_FRAME_DECLARATION,
            Gate.G5_ROUTER,
            Gate.G6_CAUSAL_CHAIN,
            Gate.G7_SUSPENSION_GATE,
        )
    if order is OrderingName.ROUTER_BEFORE_FRAME_DECL:
        return (
            Gate.G1_PREMISE_EXTRACTOR,
            Gate.G2_SPL,
            Gate.G4_FRAME_TENSION,
            Gate.G5_ROUTER,
            Gate.G3_FRAME_DECLARATION,
            Gate.G6_CAUSAL_CHAIN,
            Gate.G7_SUSPENSION_GATE,
        )
    if order is OrderingName.CAUSAL_BEFORE_FRAME_TENSION:
        return (
            Gate.G1_PREMISE_EXTRACTOR,
            Gate.G2_SPL,
            Gate.G3_FRAME_DECLARATION,
            Gate.G6_CAUSAL_CHAIN,
            Gate.G4_FRAME_TENSION,
            Gate.G5_ROUTER,
            Gate.G7_SUSPENSION_GATE,
        )
    if order is OrderingName.SUSPENSION_BEFORE_CAUSAL:
        return (
            Gate.G1_PREMISE_EXTRACTOR,
            Gate.G2_SPL,
            Gate.G3_FRAME_DECLARATION,
            Gate.G4_FRAME_TENSION,
            Gate.G5_ROUTER,
            Gate.G7_SUSPENSION_GATE,
            Gate.G6_CAUSAL_CHAIN,
        )
    if order is OrderingName.MINIMAL_WITHOUT_CAUSAL_CHAIN:
        return (
            Gate.G1_PREMISE_EXTRACTOR,
            Gate.G2_SPL,
            Gate.G3_FRAME_DECLARATION,
            Gate.G4_FRAME_TENSION,
            Gate.G5_ROUTER,
            Gate.G7_SUSPENSION_GATE,
        )
    if order is OrderingName.MINIMAL_WITHOUT_FRAME_TENSION:
        return (
            Gate.G1_PREMISE_EXTRACTOR,
            Gate.G2_SPL,
            Gate.G3_FRAME_DECLARATION,
            Gate.G5_ROUTER,
            Gate.G6_CAUSAL_CHAIN,
            Gate.G7_SUSPENSION_GATE,
        )
    if order is OrderingName.MAXIMAL_SAFE_STACK:
        # All seven gates with the most defensive-forward order:
        # Suspension (G7) fires earliest after parsing, then
        # FrameTension/Router, then CAUSAL_CHAIN, then frame
        # declaration last (least gain).
        return (
            Gate.G1_PREMISE_EXTRACTOR,
            Gate.G2_SPL,
            Gate.G7_SUSPENSION_GATE,
            Gate.G4_FRAME_TENSION,
            Gate.G5_ROUTER,
            Gate.G6_CAUSAL_CHAIN,
            Gate.G3_FRAME_DECLARATION,
        )
    raise AssertionError(order)


def all_orderings() -> tuple[OrderingName, ...]:
    return tuple(OrderingName)


__all__ = ["Gate", "OrderingName", "all_orderings", "gate_sequence"]
