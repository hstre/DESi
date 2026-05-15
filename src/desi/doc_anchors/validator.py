"""Validate anchors against their artefacts — Aufgaben 7 + 8.

Each anchor produces an :class:`AnchorVerdict` with a closed
five-value classification:

* ``VERIFIED``         — artefact + field resolve, expected matches
* ``MISSING_ARTIFACT`` — file does not exist on disk
* ``MISSING_FIELD``    — file parses, but the field is absent
* ``VALUE_MISMATCH``   — field resolves but value differs
* ``MALFORMED``        — anchor body could not be parsed
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .schema import ClaimAnchor


class AnchorVerdict(str, Enum):
    VERIFIED = "verified"
    MISSING_ARTIFACT = "missing_artifact"
    MISSING_FIELD = "missing_field"
    VALUE_MISMATCH = "value_mismatch"
    MALFORMED = "malformed"


@dataclass(frozen=True)
class AnchorOutcome:
    anchor: ClaimAnchor
    verdict: AnchorVerdict
    actual_value: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchor": self.anchor.to_dict(),
            "verdict": self.verdict.value,
            "actual_value": self.actual_value,
            "reason": self.reason,
        }


def _walk_field(obj: Any, path: str) -> tuple[bool, Any]:
    """Resolve a dotted JSON path. Returns ``(found, value)``.

    Supports two extensions:
      * ``len:KEY``       → length of ``obj[KEY]``
      * ``[N]``           → list index segment
    """
    current = obj
    for segment in path.split("."):
        if segment.startswith("len:"):
            inner = segment[4:]
            if not isinstance(current, dict) or inner not in current:
                return False, None
            return True, len(current[inner])
        # list index
        if segment.startswith("[") and segment.endswith("]"):
            try:
                idx = int(segment[1:-1])
            except ValueError:
                return False, None
            if not isinstance(current, list) or idx >= len(current):
                return False, None
            current = current[idx]
            continue
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        else:
            return False, None
    return True, current


def _value_matches(actual: Any, expected: str) -> bool:
    if isinstance(actual, bool):
        return str(actual).lower() == expected.lower()
    if isinstance(actual, (int, float)):
        try:
            return abs(float(actual) - float(expected)) < 1e-4
        except (TypeError, ValueError):
            return False
    if isinstance(actual, str):
        return actual == expected
    if isinstance(actual, list):
        return f"{len(actual)}" == expected
    return str(actual) == expected


def validate_anchor(
    anchor: ClaimAnchor,
    *,
    repo_root: pathlib.Path,
) -> AnchorOutcome:
    if not anchor.expected:
        return AnchorOutcome(
            anchor, AnchorVerdict.MALFORMED,
            reason="anchor missing expected= value",
        )
    art_path = repo_root / anchor.artifact
    if not art_path.exists():
        return AnchorOutcome(
            anchor, AnchorVerdict.MISSING_ARTIFACT,
            reason=f"{anchor.artifact} does not exist",
        )
    try:
        payload = json.loads(art_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return AnchorOutcome(
            anchor, AnchorVerdict.MALFORMED,
            reason=f"could not load artifact: {exc}",
        )
    found, value = _walk_field(payload, anchor.field)
    if not found:
        return AnchorOutcome(
            anchor, AnchorVerdict.MISSING_FIELD,
            reason=f"field {anchor.field!r} not found",
        )
    if not _value_matches(value, anchor.expected):
        return AnchorOutcome(
            anchor, AnchorVerdict.VALUE_MISMATCH,
            actual_value=str(value),
            reason=(
                f"{anchor.artifact}:{anchor.field} = {value!r}, "
                f"doc says {anchor.expected!r}"
            ),
        )
    return AnchorOutcome(
        anchor, AnchorVerdict.VERIFIED,
        actual_value=str(value),
    )


def validate_anchors(
    anchors: tuple[ClaimAnchor, ...],
    *,
    repo_root: pathlib.Path,
) -> tuple[AnchorOutcome, ...]:
    return tuple(validate_anchor(a, repo_root=repo_root) for a in anchors)


__all__ = [
    "AnchorOutcome",
    "AnchorVerdict",
    "validate_anchor",
    "validate_anchors",
]
