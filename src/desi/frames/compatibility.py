"""FrameCompatibilityCheck — Aufgabe 4.

For every :class:`FrameKind`, declare a closed set of allowed
downstream pipelines and a closed set of blocked ones. The check
is **pre-audit**: it decides which pipeline may even *attempt* to
judge the claim. It never decides truth.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .kinds import FrameKind


@dataclass(frozen=True)
class FrameCompatibilityCheck:
    compatible: bool
    allowed_pipeline: tuple[str, ...]
    blocked_pipeline: tuple[str, ...]
    reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "allowed_pipeline": list(self.allowed_pipeline),
            "blocked_pipeline": list(self.blocked_pipeline),
            "reason": self.reason,
            "replay_hash": self.replay_hash,
        }


# Closed per-frame pipeline tables. The set of pipeline tokens is
# itself closed (see _ALL_PIPELINES) so we can validate every entry.
_ALL_PIPELINES: frozenset[str] = frozenset({
    "tool_gate", "logical_audit", "consilium",
    "causal_chain", "syllogism", "identity_audit",
    "metaphor_audit", "thermodynamic_inference",
    "literal_physical_inference", "authority_boost",
    "linguistic_proof", "bridge",
})


_TABLE: dict[FrameKind, tuple[tuple[str, ...], tuple[str, ...]]] = {
    FrameKind.THERMODYNAMIC: (
        ("tool_gate", "logical_audit"),
        ("metaphor_audit",),
    ),
    FrameKind.INFORMATION_THEORETIC: (
        ("tool_gate", "logical_audit"),
        ("thermodynamic_inference",),
    ),
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY: (
        ("identity_audit", "logical_audit"),
        ("causal_chain",),
    ),
    FrameKind.METAPHORICAL: (
        ("metaphor_audit", "consilium"),
        ("literal_physical_inference", "tool_gate"),
    ),
    FrameKind.FORMAL_LOGIC: (
        ("logical_audit", "syllogism", "causal_chain"),
        ("authority_boost",),
    ),
    FrameKind.EMPIRICAL_CAUSAL: (
        ("causal_chain", "consilium"),
        ("syllogism",),
    ),
    FrameKind.AUTHORITY_SPEECH: (
        ("logical_audit",),
        ("authority_boost", "tool_gate", "causal_chain"),
    ),
    FrameKind.TOOL_COMPUTABLE: (
        ("tool_gate",),
        ("linguistic_proof", "consilium"),
    ),
    FrameKind.FRAME_UNDECLARED: (
        (),
        ("tool_gate", "logical_audit", "consilium",
         "causal_chain", "syllogism", "identity_audit",
         "metaphor_audit", "bridge"),
    ),
}


def _compatibility_replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {k: v for k, v in payload.items() if k != "replay_hash"}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def check_compatibility(
    *,
    declared_frame: FrameKind,
    requested_pipeline: str | None = None,
) -> FrameCompatibilityCheck:
    """Return the allowed / blocked sets for ``declared_frame``.

    If ``requested_pipeline`` is supplied, ``compatible`` reflects
    whether that specific pipeline appears in the allowed list.
    """
    allowed, blocked = _TABLE[declared_frame]
    if declared_frame is FrameKind.FRAME_UNDECLARED:
        reason = (
            "frame undeclared — no pipeline may promote this claim"
        )
        compatible = False
    elif requested_pipeline is None:
        reason = f"frame={declared_frame.value} → {len(allowed)} allowed"
        compatible = True
    elif requested_pipeline in allowed:
        reason = (
            f"requested pipeline {requested_pipeline!r} "
            f"is allowed under {declared_frame.value}"
        )
        compatible = True
    elif requested_pipeline in blocked:
        reason = (
            f"requested pipeline {requested_pipeline!r} "
            f"is blocked under {declared_frame.value}"
        )
        compatible = False
    else:
        reason = (
            f"requested pipeline {requested_pipeline!r} "
            f"is neither allowed nor blocked under "
            f"{declared_frame.value} — defaulting to blocked"
        )
        compatible = False
    payload = {
        "compatible": compatible,
        "allowed_pipeline": list(allowed),
        "blocked_pipeline": list(blocked),
        "reason": reason,
    }
    return FrameCompatibilityCheck(
        compatible=compatible,
        allowed_pipeline=allowed,
        blocked_pipeline=blocked,
        reason=reason,
        replay_hash=_compatibility_replay_hash(payload),
    )


def allowed_pipelines(frame: FrameKind) -> tuple[str, ...]:
    return _TABLE[frame][0]


def blocked_pipelines(frame: FrameKind) -> tuple[str, ...]:
    return _TABLE[frame][1]


__all__ = [
    "FrameCompatibilityCheck",
    "allowed_pipelines",
    "blocked_pipelines",
    "check_compatibility",
]
