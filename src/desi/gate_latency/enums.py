"""Closed taxonomies for v3.23 — three stacks + classifications."""
from __future__ import annotations

from enum import Enum

from ..gate_order import Gate, OrderingName, gate_sequence


class StackName(str, Enum):
    S1_CURRENT_ORDER             = "current_order"
    S2_MAXIMAL_SAFE_STACK        = "maximal_safe_stack"
    S3_MINIMAL_WITHOUT_CAUSAL_CHAIN = "minimal_without_causal_chain"


class EfficiencyClass(str, Enum):
    NO_GAIN          = "NO_GAIN"
    SIGNIFICANT_GAIN = "SIGNIFICANT_GAIN"
    MAJOR_GAIN       = "MAJOR_GAIN"


def stack_sequence(name: StackName) -> tuple[Gate, ...]:
    """Map a v3.23 stack name to the v3.22 ordering sequence."""
    if name is StackName.S1_CURRENT_ORDER:
        return gate_sequence(OrderingName.CURRENT_ORDER)
    if name is StackName.S2_MAXIMAL_SAFE_STACK:
        return gate_sequence(OrderingName.MAXIMAL_SAFE_STACK)
    if name is StackName.S3_MINIMAL_WITHOUT_CAUSAL_CHAIN:
        return gate_sequence(OrderingName.MINIMAL_WITHOUT_CAUSAL_CHAIN)
    raise AssertionError(name)


def all_stacks() -> tuple[StackName, ...]:
    return tuple(StackName)


__all__ = [
    "EfficiencyClass",
    "StackName",
    "all_stacks",
    "stack_sequence",
]
