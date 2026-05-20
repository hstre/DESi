"""Tests for v1.4 depth guard — R5 scenario."""
from __future__ import annotations

import pytest

from desi.recursive import (
    DEFAULT_MAX_DEPTH,
    DepthExceeded,
    RecursiveResolver,
    ResolutionState,
    check_depth,
)

from ._helpers import (
    ScriptedAuditor,
    ScriptedConsilium,
    needs_bridge,
)


# ---------------------------------------------------------------------------
# Default
# ---------------------------------------------------------------------------


def test_default_max_depth_is_three() -> None:
    assert DEFAULT_MAX_DEPTH == 3


# ---------------------------------------------------------------------------
# check_depth helper
# ---------------------------------------------------------------------------


def test_check_depth_returns_none_under_cap() -> None:
    assert check_depth(0, 3) is None
    assert check_depth(3, 3) is None


def test_check_depth_flags_violation() -> None:
    hit = check_depth(4, 3)
    assert isinstance(hit, DepthExceeded)
    assert hit.current_depth == 4
    assert hit.max_depth == 3


def test_check_depth_rejects_negative_max() -> None:
    with pytest.raises(ValueError):
        check_depth(0, -1)


# ---------------------------------------------------------------------------
# R5: chain of length 5, max_depth=3 → DEPTH_EXCEEDED
# ---------------------------------------------------------------------------


def _five_chain():
    return ScriptedAuditor(script={
        "n0": needs_bridge("n0", "n1"),
        "n1": needs_bridge("n1", "n2"),
        "n2": needs_bridge("n2", "n3"),
        "n3": needs_bridge("n3", "n4"),
        "n4": needs_bridge("n4", "n5"),
    })


def test_r5_chain_of_five_exceeds_default_depth() -> None:
    r = RecursiveResolver(
        auditor=_five_chain(), consilium=ScriptedConsilium(),
    ).resolve("n0")
    assert r.final_state is ResolutionState.RESOLUTION_DEPTH_EXCEEDED


def test_chain_of_five_completes_with_max_depth_5() -> None:
    auditor = _five_chain()
    # Add a leaf for the deepest node so it can resolve.
    from desi.logic import LogicalState
    auditor.script["n5"] = ScriptedAuditor().audit("n5")  # default GAP → leaf
    r = RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    ).resolve("n0", max_depth=5)
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.depth_reached == 5


def test_max_depth_zero_blocks_any_bridge_required_root() -> None:
    auditor = ScriptedAuditor(script={
        "root": needs_bridge("root", "child"),
    })
    r = RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    ).resolve("root", max_depth=0)
    assert r.final_state is ResolutionState.RESOLUTION_DEPTH_EXCEEDED
