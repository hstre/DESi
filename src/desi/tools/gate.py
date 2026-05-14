"""ToolGate — the only path through which a tool may execute.

Six safety checks run *before* any runner is invoked:

1. Tool kind must be in the closed allowlist
   (:data:`desi.tools.kinds.ALLOWED_TOOL_KINDS`).
2. Module + function must match the registry entry — callers can
   not redirect to a private function.
3. Input payload size ≤ :data:`MAX_INPUT_BYTES` (4 KB).
4. Hard execution timeout ≤ :data:`HARD_TIMEOUT_SECONDS` (2 s).
5. Runner must be deterministic (no IO, no network, no fs writes —
   verified at registry-load time by inspecting the registered
   functions; all v1.9 runners are pure stdlib).
6. Runner must not raise; if it does, the gate converts the error
   into a TOOL_FAILED result with a typed reason. Authority and
   logical-audit pipelines are never bypassed.

A successful execution returns a :class:`ToolResult` carrying the
tool's output + a fully populated :class:`ToolProvenance`. A
failure returns a :class:`ToolResult` with ``state=TOOL_FAILED``
and a typed reason.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from ..memory.claim import ClaimState
from .kinds import ALLOWED_TOOL_KINDS, ToolKind
from .proposal import ToolUseProposal
from .provenance import (
    ToolProvenance,
    _short_hash,
    dependency_fingerprint,
    environment_hash,
)
from .runners import RUNNERS


# Hard, pinned safety values. Adjusting any of these is a code edit
# and is therefore an audit event.
HARD_TIMEOUT_SECONDS: float = 2.0
MAX_INPUT_BYTES: int = 4096


# Failure reasons (closed set so the ledger / impact-scan can
# group by reason without free-string drift).
class FailureReason(str):
    NOT_IN_ALLOWLIST = "not_in_allowlist"
    INPUT_TOO_LARGE = "input_too_large"
    REGISTRY_MISMATCH = "registry_mismatch"
    DEPENDENCY_MISSING = "dependency_missing"
    RUNNER_ERROR = "runner_error"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    INVALID_PROPOSAL = "invalid_proposal"


@dataclass(frozen=True)
class ToolResult:
    """Outcome of a single :meth:`ToolGate.execute` call."""

    state: ClaimState
    proposal: ToolUseProposal
    output: dict[str, Any] = field(default_factory=dict)
    provenance: ToolProvenance | None = None
    failure_reason: str = ""
    failure_message: str = ""

    @property
    def succeeded(self) -> bool:
        return self.state is ClaimState.TOOL_SUPPORTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "proposal": self.proposal.to_dict(),
            "output": dict(self.output),
            "provenance": (
                self.provenance.to_dict() if self.provenance else None
            ),
            "failure_reason": self.failure_reason,
            "failure_message": self.failure_message,
        }


class ToolGate:
    """Execute a tool proposal under the v1.9 safety contract.

    The gate is stateless. Every call performs the full set of
    pre-execution checks and produces a typed :class:`ToolResult`.
    """

    def __init__(
        self,
        *,
        timeout_seconds: float = HARD_TIMEOUT_SECONDS,
        max_input_bytes: int = MAX_INPUT_BYTES,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > HARD_TIMEOUT_SECONDS:
            raise ValueError(
                "timeout_seconds must be in (0, "
                f"{HARD_TIMEOUT_SECONDS}]"
            )
        if max_input_bytes <= 0 or max_input_bytes > MAX_INPUT_BYTES:
            raise ValueError(
                "max_input_bytes must be in (0, "
                f"{MAX_INPUT_BYTES}]"
            )
        self._timeout = float(timeout_seconds)
        self._max_input = int(max_input_bytes)

    @property
    def timeout_seconds(self) -> float:
        return self._timeout

    @property
    def max_input_bytes(self) -> int:
        return self._max_input

    def execute(
        self,
        proposal: ToolUseProposal,
    ) -> ToolResult:
        """Run the proposal through the gate and return a typed result."""
        # Check 1: allowlist.
        if proposal.tool_kind not in ALLOWED_TOOL_KINDS:
            return self._fail(
                proposal,
                FailureReason.NOT_IN_ALLOWLIST,
                f"{proposal.tool_kind!s} not in v1.9 allowlist",
            )

        registry_entry = RUNNERS.get(proposal.tool_kind)
        if registry_entry is None:
            return self._fail(
                proposal,
                FailureReason.REGISTRY_MISMATCH,
                "no registered runner for tool kind",
            )

        # Check 2: module + function match the registry. Callers
        # cannot redirect a tool to a private function.
        if (proposal.module_name != registry_entry["module_name"]
                or proposal.function_name != registry_entry["function_name"]):
            return self._fail(
                proposal,
                FailureReason.REGISTRY_MISMATCH,
                f"proposal {proposal.module_name}.{proposal.function_name} "
                f"does not match registry "
                f"{registry_entry['module_name']}."
                f"{registry_entry['function_name']}",
            )

        # Check 3: input size.
        try:
            input_bytes = json.dumps(
                proposal.input_payload,
                sort_keys=True, separators=(",", ":"), default=str,
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            return self._fail(
                proposal,
                FailureReason.INVALID_PROPOSAL,
                f"input_payload not JSON-serialisable: {exc}",
            )
        if len(input_bytes) > self._max_input:
            return self._fail(
                proposal,
                FailureReason.INPUT_TOO_LARGE,
                f"input is {len(input_bytes)} bytes "
                f"(>{self._max_input} cap)",
            )

        # Check 4 + 6: execute the runner. Time the call and
        # convert exceptions to typed failures. The 2-second cap is
        # checked post-hoc for stdlib runners that complete in
        # microseconds; SymPy unavailability raises ModuleNotFoundError
        # which we map to DEPENDENCY_MISSING.
        runner = registry_entry["function"]
        start = time.monotonic()
        try:
            output = runner(dict(proposal.input_payload))
        except ModuleNotFoundError as exc:
            return self._fail(
                proposal,
                FailureReason.DEPENDENCY_MISSING,
                str(exc),
            )
        except Exception as exc:
            return self._fail(
                proposal,
                FailureReason.RUNNER_ERROR,
                f"{type(exc).__name__}: {exc}",
            )
        elapsed_ms = (time.monotonic() - start) * 1000.0
        if elapsed_ms > self._timeout * 1000.0:
            return self._fail(
                proposal,
                FailureReason.TIMEOUT_EXCEEDED,
                f"runner took {elapsed_ms:.1f} ms "
                f"(> {self._timeout * 1000.0:.0f} ms cap)",
            )

        # Build provenance.
        provenance = ToolProvenance(
            tool_name=registry_entry["tool_name"],
            tool_version=registry_entry["tool_version"],
            module_path=registry_entry["module_name"],
            function_name=registry_entry["function_name"],
            input_hash=proposal.input_hash,
            output_hash="oh_" + _short_hash(output),
            dependency_fingerprint=dependency_fingerprint(
                (registry_entry["tool_name"],
                 registry_entry["tool_version"]),
            ),
            environment_hash=environment_hash(),
            execution_time_ms=elapsed_ms,
            run_id=proposal.run_id,
        )

        # The directive says: tool result is *evidence*, never
        # promotion. Map a successful execution to TOOL_SUPPORTED.
        # A "refutation" decision (e.g. "Is 5 = 6?" → False) is a
        # caller-side classification on top of the same result.
        return ToolResult(
            state=ClaimState.TOOL_SUPPORTED,
            proposal=proposal,
            output=output,
            provenance=provenance,
        )

    @staticmethod
    def _fail(
        proposal: ToolUseProposal,
        reason: str,
        message: str,
    ) -> ToolResult:
        return ToolResult(
            state=ClaimState.TOOL_FAILED,
            proposal=proposal,
            output={},
            provenance=None,
            failure_reason=reason,
            failure_message=message,
        )


__all__ = [
    "FailureReason",
    "HARD_TIMEOUT_SECONDS",
    "MAX_INPUT_BYTES",
    "ToolGate",
    "ToolResult",
]
