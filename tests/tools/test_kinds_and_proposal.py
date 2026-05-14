"""Tests for v1.9 ToolKind enum + ToolUseProposal."""
from __future__ import annotations

from desi.tools import ALLOWED_TOOL_KINDS, ToolKind, ToolUseProposal


def test_tool_kind_enum_has_exactly_six_values() -> None:
    values = {k.value for k in ToolKind}
    assert values == {
        "python_decimal", "python_fractions", "python_datetime",
        "python_collections", "sympy", "set_theory",
    }


def test_allowlist_equals_full_enum() -> None:
    """The closed allowlist contains every ToolKind — no hidden gaps."""
    assert ALLOWED_TOOL_KINDS == frozenset(ToolKind)


def test_proposal_carries_all_six_required_fields() -> None:
    p = ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="run_decimal",
        input_payload={"expression": "1 + 1"},
        run_id="tr_test",
    )
    for f in ("tool_kind", "module_name", "function_name",
              "input_payload", "input_hash", "run_id"):
        assert hasattr(p, f), f
    assert p.input_hash.startswith("ih_")


def test_proposal_input_hash_is_deterministic() -> None:
    a = ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="run_decimal",
        input_payload={"expression": "2 + 3"},
    )
    b = ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="run_decimal",
        input_payload={"expression": "2 + 3"},
    )
    assert a.input_hash == b.input_hash


def test_proposal_input_hash_changes_with_payload() -> None:
    a = ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="run_decimal",
        input_payload={"expression": "2 + 3"},
    )
    b = ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="run_decimal",
        input_payload={"expression": "2 + 4"},
    )
    assert a.input_hash != b.input_hash


def test_proposal_to_dict_round_trips_fields() -> None:
    p = ToolUseProposal.build(
        tool_kind=ToolKind.SET_THEORY,
        module_name="desi.tools.runners",
        function_name="run_set_theory",
        input_payload={"operation": "intersection",
                       "a": ["1", "2"], "b": ["2", "3"]},
        run_id="tr_xyz",
    )
    d = p.to_dict()
    assert d["tool_kind"] == "set_theory"
    assert d["module_name"] == "desi.tools.runners"
    assert d["function_name"] == "run_set_theory"
    assert d["run_id"] == "tr_xyz"
