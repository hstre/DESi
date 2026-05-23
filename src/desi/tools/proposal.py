"""ToolUseProposal — the audit-trail-bearing request from parser to gate.

A proposal is just *a request*. It carries the tool kind, the
chosen module / function, and a typed input payload. The gate
either runs it (returning a result with full provenance) or
rejects it (TOOL_FAILED with reason). Nothing about the proposal
upgrades a claim by itself.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .kinds import ToolKind
from .provenance import _short_hash


def make_run_id() -> str:
    return "tr_" + uuid.uuid4().hex[:12]


@dataclass(frozen=True)
class ToolUseProposal:
    """A request for the gate to run a specific tool with specific input.

    All five mandatory fields per the v1.9 directive: tool_kind,
    module_name, function_name, input_payload, input_hash, run_id.
    """

    tool_kind: ToolKind
    module_name: str
    function_name: str
    input_payload: dict[str, Any]
    input_hash: str
    run_id: str
    rationale: str = ""

    @classmethod
    def build(
        cls,
        *,
        tool_kind: ToolKind,
        module_name: str,
        function_name: str,
        input_payload: dict[str, Any],
        run_id: str | None = None,
        rationale: str = "",
    ) -> "ToolUseProposal":
        """Build a proposal with a deterministic input_hash."""
        return cls(
            tool_kind=tool_kind,
            module_name=module_name,
            function_name=function_name,
            input_payload=dict(input_payload),
            input_hash="ih_" + _short_hash(input_payload),
            run_id=run_id or make_run_id(),
            rationale=rationale,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_kind": self.tool_kind.value,
            "module_name": self.module_name,
            "function_name": self.function_name,
            "input_payload": dict(self.input_payload),
            "input_hash": self.input_hash,
            "run_id": self.run_id,
            "rationale": self.rationale,
        }


__all__ = [
    "ToolUseProposal",
    "make_run_id",
]
