"""Parser for ``[claim-anchor: ...]`` and ``[legacy-unanchored]``.

Single-line, whitespace-insensitive, case-sensitive keys.
"""
from __future__ import annotations

import re
from typing import Iterable

from .schema import (
    ANCHOR_PREFIX,
    ClaimAnchor,
    LEGACY_MARKER,
    LegacyExemption,
)


# Matches a full ``[claim-anchor: ...]`` block on a single line.
# We intentionally do NOT support multi-line anchors — they'd defeat
# v3.0's same-line referenced_artifact detection.
_ANCHOR_BLOCK = re.compile(
    r"\[claim-anchor:\s*(?P<body>[^\]]*?)\s*\]"
)


def _split_kv(body: str) -> dict[str, str]:
    """Split ``a=b, c=d`` into ``{'a': 'b', 'c': 'd'}``.

    Values may be unquoted; if they are quoted with either ``"`` or
    ``'`` the quotes are stripped.
    """
    out: dict[str, str] = {}
    for part in body.split(","):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip().strip("\"'")
        if not k:
            continue
        out[k] = v
    return out


def parse_anchors(
    doc_path: str, text: str,
) -> tuple[ClaimAnchor, ...]:
    """Return every well-formed ``ClaimAnchor`` in ``text``."""
    out: list[ClaimAnchor] = []
    for n, line in enumerate(text.splitlines(), start=1):
        if ANCHOR_PREFIX not in line:
            continue
        for m in _ANCHOR_BLOCK.finditer(line):
            kv = _split_kv(m.group("body"))
            artifact = kv.get("artifact", "")
            field = kv.get("field", "")
            expected = kv.get("expected", "")
            if not (artifact and field):
                # Malformed anchor; skip silently — the validator
                # has separate "missing fields" detection.
                continue
            out.append(ClaimAnchor(
                artifact=artifact,
                field=field,
                expected=expected,
                doc_path=doc_path,
                line_number=n,
                raw=m.group(0),
            ))
    return tuple(out)


def parse_legacy_markers(
    doc_path: str, text: str,
) -> tuple[LegacyExemption, ...]:
    out: list[LegacyExemption] = []
    for n, line in enumerate(text.splitlines(), start=1):
        if LEGACY_MARKER in line:
            out.append(LegacyExemption(
                doc_path=doc_path, line_number=n,
            ))
    return tuple(out)


__all__ = ["parse_anchors", "parse_legacy_markers"]
