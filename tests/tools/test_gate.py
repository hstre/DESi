"""Tests for v1.9 ToolGate — six pre-execution safety checks."""
from __future__ import annotations

import pytest

from desi.memory.claim import ClaimState
from desi.tools import (
    HARD_TIMEOUT_SECONDS,
    MAX_INPUT_BYTES,
    ToolGate,
    ToolKind,
    ToolUseProposal,
)
from desi.tools.gate import FailureReason


def _ok_decimal_proposal():
    return ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="run_decimal",
        input_payload={"expression": "2 + 2"},
    )


# ---------------------------------------------------------------------------
# Constants are pinned
# ---------------------------------------------------------------------------


def test_hard_timeout_is_two_seconds() -> None:
    assert HARD_TIMEOUT_SECONDS == 2.0


def test_max_input_bytes_is_four_kb() -> None:
    assert MAX_INPUT_BYTES == 4096


# ---------------------------------------------------------------------------
# Successful path returns TOOL_SUPPORTED + provenance
# ---------------------------------------------------------------------------


def test_successful_decimal_call_returns_tool_supported() -> None:
    res = ToolGate().execute(_ok_decimal_proposal())
    assert res.state is ClaimState.TOOL_SUPPORTED
    assert res.output["value"] == "4"
    assert res.provenance is not None
    assert res.failure_reason == ""


def test_provenance_carries_all_required_fields() -> None:
    res = ToolGate().execute(_ok_decimal_proposal())
    p = res.provenance
    for f in ("tool_name", "tool_version", "module_path",
              "function_name", "input_hash", "output_hash",
              "dependency_fingerprint", "environment_hash",
              "execution_time_ms", "run_id"):
        assert hasattr(p, f), f
    assert p.input_hash.startswith("ih_")
    assert p.output_hash.startswith("oh_")
    assert p.dependency_fingerprint.startswith("dep_")
    assert p.environment_hash.startswith("env_")


# ---------------------------------------------------------------------------
# Safety checks — closed-list failures
# ---------------------------------------------------------------------------


def test_registry_mismatch_fails_closed() -> None:
    """Caller cannot redirect the runner via a different function name."""
    p = ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="malicious_function",
        input_payload={"expression": "1+1"},
    )
    res = ToolGate().execute(p)
    assert res.state is ClaimState.TOOL_FAILED
    assert res.failure_reason == FailureReason.REGISTRY_MISMATCH


def test_input_too_large_fails_closed() -> None:
    huge = "1+" * 4000 + "1"
    p = ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="run_decimal",
        input_payload={"expression": huge},
    )
    res = ToolGate().execute(p)
    assert res.state is ClaimState.TOOL_FAILED
    assert res.failure_reason == FailureReason.INPUT_TOO_LARGE


def test_runner_error_fails_closed() -> None:
    """Calling decimal with a non-arithmetic expression → RUNNER_ERROR."""
    p = ToolUseProposal.build(
        tool_kind=ToolKind.PYTHON_DECIMAL,
        module_name="desi.tools.runners",
        function_name="run_decimal",
        input_payload={"expression": "open('etc/passwd')"},
    )
    res = ToolGate().execute(p)
    assert res.state is ClaimState.TOOL_FAILED
    assert res.failure_reason == FailureReason.RUNNER_ERROR


def test_sympy_fails_with_dependency_missing(monkeypatch) -> None:
    """sympy is not installed in the v1.9 environment; the gate must
    convert the ModuleNotFoundError into a typed DEPENDENCY_MISSING
    failure (not RUNNER_ERROR)."""
    try:
        import sympy as _   # noqa: F401
        pytest.skip("sympy is installed in this environment")
    except ModuleNotFoundError:
        pass
    p = ToolUseProposal.build(
        tool_kind=ToolKind.SYMPY,
        module_name="desi.tools.runners",
        function_name="run_sympy",
        input_payload={"operation": "solve", "lhs": "x", "rhs": "1"},
    )
    res = ToolGate().execute(p)
    assert res.state is ClaimState.TOOL_FAILED
    assert res.failure_reason == FailureReason.DEPENDENCY_MISSING


# ---------------------------------------------------------------------------
# A successful tool result is TOOL_SUPPORTED, never LOGICALLY_SUPPORTED
# ---------------------------------------------------------------------------


def test_successful_tool_never_returns_logically_supported() -> None:
    """The directive's hard contract: tool results are *evidence*,
    never authority. ClaimState.LOGICALLY_SUPPORTED is forbidden."""
    res = ToolGate().execute(_ok_decimal_proposal())
    assert res.state is not ClaimState.LOGICALLY_SUPPORTED
    assert res.state is ClaimState.TOOL_SUPPORTED


# ---------------------------------------------------------------------------
# Two runs of the same proposal produce identical hashes
# ---------------------------------------------------------------------------


def test_two_executions_same_input_yield_identical_hashes() -> None:
    a = ToolGate().execute(_ok_decimal_proposal())
    b = ToolGate().execute(_ok_decimal_proposal())
    assert a.provenance.input_hash == b.provenance.input_hash
    assert a.provenance.output_hash == b.provenance.output_hash
    assert (a.provenance.dependency_fingerprint
            == b.provenance.dependency_fingerprint)
    assert (a.provenance.environment_hash
            == b.provenance.environment_hash)
