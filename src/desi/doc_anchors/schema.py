"""Claim-anchor schema — Aufgabe 1.

Anchor surface form (single-line, whitespace-tolerant):

    [claim-anchor: artifact=<path>, field=<json-path>, expected=<value>]

Keys are case-sensitive. The parser allows optional whitespace
around ``,`` and ``=``. ``expected`` may be a quoted or unquoted
token; quotes are stripped during parsing.

The legacy-exemption marker for v0.x / v1.x prose documents:

    [legacy-unanchored]

Both markers are inert in the rendered Markdown but visible to the
validator.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClaimAnchor:
    """One parsed anchor with byte-precise source location."""

    artifact: str
    field: str
    expected: str
    doc_path: str
    line_number: int
    raw: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "field": self.field,
            "expected": self.expected,
            "doc_path": self.doc_path,
            "line_number": self.line_number,
        }


@dataclass(frozen=True)
class LegacyExemption:
    """One ``[legacy-unanchored]`` marker."""

    doc_path: str
    line_number: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_path": self.doc_path,
            "line_number": self.line_number,
        }


ANCHOR_PREFIX: str = "[claim-anchor:"
LEGACY_MARKER: str = "[legacy-unanchored]"


__all__ = [
    "ANCHOR_PREFIX",
    "ClaimAnchor",
    "LEGACY_MARKER",
    "LegacyExemption",
]
