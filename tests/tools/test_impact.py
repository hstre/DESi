"""Tests for v1.9 ImpactScan + ContaminationPropagation."""
from __future__ import annotations

from desi.tools import (
    ContaminationPropagation,
    ImpactScan,
    ToolBenchmarkRunner,
    ToolGate,
    ToolKind,
    ToolUsageRecord,
    ToolUsageRegistry,
    ToolUseProposal,
)


def _populate_registry():
    """Run the mini-benchmark to populate a usage registry."""
    return ToolBenchmarkRunner().run().registry


# ---------------------------------------------------------------------------
# ImpactScan
# ---------------------------------------------------------------------------


def test_impact_scan_finds_decimal_users() -> None:
    reg = _populate_registry()
    scan = ImpactScan.for_tool(reg, tool_name="python_decimal")
    # Cat-A ids TA1..TA4 use python_decimal.
    assert set(scan.claim_ids) == {"TA1", "TA2", "TA3", "TA4"}


def test_impact_scan_filters_by_version() -> None:
    reg = _populate_registry()
    scan_with_real = ImpactScan.for_tool(
        reg, tool_name="python_decimal",
        tool_version="999.999.999",   # not the real version
    )
    assert scan_with_real.claim_ids == ()


def test_impact_scan_returns_empty_for_unknown_tool() -> None:
    reg = _populate_registry()
    scan = ImpactScan.for_tool(reg, tool_name="not_a_real_tool")
    assert scan.claim_ids == ()
    assert scan.record_count == 0


def test_impact_scan_to_dict_round_trips() -> None:
    reg = _populate_registry()
    scan = ImpactScan.for_tool(reg, tool_name="python_collections")
    d = scan.to_dict()
    for k in ("tool_name", "tool_version", "claim_ids", "record_count"):
        assert k in d


# ---------------------------------------------------------------------------
# ContaminationPropagation
# ---------------------------------------------------------------------------


def test_contamination_propagation_includes_direct_users() -> None:
    reg = _populate_registry()
    cp = ContaminationPropagation.for_tool(
        reg, tool_name="python_datetime",
    )
    # Cat-D ids TD1..TD4 use datetime.
    assert set(cp.contaminated_claim_ids) == {"TD1", "TD2", "TD3", "TD4"}


def test_contamination_propagation_with_downstream_chain() -> None:
    """When a downstream-dependency adjacency is supplied, every
    transitively-reachable child is added to ``downstream_claim_ids``."""
    reg = _populate_registry()
    # Suppose TA1's value is referenced by 'derived_x' which is in
    # turn referenced by 'final_y'. Contaminating python_decimal
    # propagates through the chain.
    deps = {"TA1": ["derived_x"], "derived_x": ["final_y"]}
    cp = ContaminationPropagation.for_tool(
        reg, tool_name="python_decimal",
        downstream_dependencies=deps,
    )
    assert "TA1" in cp.contaminated_claim_ids
    assert set(cp.downstream_claim_ids) == {"derived_x", "final_y"}


def test_contamination_propagation_to_dict_shape() -> None:
    reg = _populate_registry()
    cp = ContaminationPropagation.for_tool(reg, tool_name="set_theory")
    d = cp.to_dict()
    for k in ("tool_name", "tool_version",
              "contaminated_claim_ids", "downstream_claim_ids"):
        assert k in d


# ---------------------------------------------------------------------------
# ToolUsageRegistry append-only
# ---------------------------------------------------------------------------


def test_registry_append_only_grows_monotonically() -> None:
    reg = ToolUsageRegistry()
    assert len(reg) == 0
    proposal = ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="run_decimal",
        input_payload={"expression": "1+1"},
    )
    res = ToolGate().execute(proposal)
    assert res.provenance is not None
    reg.record("claim_x", res.provenance)
    assert len(reg) == 1
    reg.record("claim_x", res.provenance)
    assert len(reg) == 2  # same claim, second usage = new record
