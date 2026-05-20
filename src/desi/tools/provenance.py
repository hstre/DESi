"""ToolProvenance — mandatory audit record for every tool result.

v1.9 directive: every tool result must carry full provenance
*before* it can attach to a claim. The provenance is what makes
the result replayable across processes, machines, and time. It
includes the tool name + version + module path + function name +
input/output hashes + dependency fingerprint + environment hash.

Two helpers compute deterministic environment / dependency
fingerprints from the running interpreter — they hash the Python
version, the platform, and the major/minor of any imported tool
module. These are used by the ToolGate to populate provenance
automatically.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _short_hash(payload: Any) -> str:
    """Deterministic 16-char sha256 over a JSON-encoded payload."""
    if isinstance(payload, (bytes, bytearray)):
        raw = bytes(payload)
    elif isinstance(payload, str):
        raw = payload.encode("utf-8")
    else:
        raw = json.dumps(
            payload, sort_keys=True, separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def environment_hash() -> str:
    """Deterministic hash of the running interpreter + platform.

    Two processes on the same Python build + platform produce
    identical hashes; a different Python build or OS produces a
    different hash. This is the v1.9 ``environment_hash`` field.
    """
    parts = (
        sys.version_info[:3],         # (3, 11, 15)
        sys.platform,                  # "linux"
        platform.machine(),            # "x86_64"
    )
    return "env_" + _short_hash(parts)


def dependency_fingerprint(*module_versions: tuple[str, str]) -> str:
    """Hash of (module_name, module_version) pairs.

    Tool runners pass the (name, version) of every external
    dependency they used. For pure-stdlib runners the input is just
    ``("python", sys.version)`` — and the fingerprint changes only
    when the Python interpreter does.
    """
    if not module_versions:
        module_versions = (("python", sys.version.split()[0]),)
    return "dep_" + _short_hash(sorted(module_versions))


@dataclass(frozen=True)
class ToolProvenance:
    """The mandatory provenance record for every tool execution.

    Frozen so it can be appended to the ledger / claim record
    without further copying. ``run_id`` ties one tool execution to
    the wider DESi run (a Memory ``Run.run_id``).
    """

    tool_name: str
    tool_version: str
    module_path: str
    function_name: str
    input_hash: str
    output_hash: str
    dependency_fingerprint: str
    environment_hash: str
    execution_time_ms: float
    run_id: str
    timestamp: datetime = None    # type: ignore

    def __post_init__(self) -> None:
        # Set a deterministic-when-omitted UTC timestamp.
        if self.timestamp is None:
            object.__setattr__(self, "timestamp",
                                datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "module_path": self.module_path,
            "function_name": self.function_name,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "dependency_fingerprint": self.dependency_fingerprint,
            "environment_hash": self.environment_hash,
            "execution_time_ms": self.execution_time_ms,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
        }


__all__ = [
    "ToolProvenance",
    "dependency_fingerprint",
    "environment_hash",
]
