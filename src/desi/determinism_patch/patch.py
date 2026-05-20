"""v3.96c - the deterministic patch.

The patch itself lives at
``src/desi/epistemic_trajectory/extractor.py``
line 236 (after the ``_stable_frame_id`` helper
was added at the top of the file). This module
documents the patch as a structured object so the
audit report can reference it without touching
the patched file.

Patch shape:

    BEFORE:
        frame_id=float(hash(s.get("operator", "")) % 9)

    AFTER:
        frame_id=float(_stable_frame_id(
            s.get("operator", ""),
        ))

    HELPER:
        from hashlib import sha256

        def _stable_frame_id(operator: str) -> int:
            digest = sha256(
                operator.encode("utf-8"),
            ).digest()
            return int.from_bytes(
                digest[:8], "big",
            ) % 9
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    _stable_frame_id,
)


@dataclass(frozen=True)
class PatchSpec:
    path: str
    line_number: int
    fix_kind: str
    helper_added: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "line_number": self.line_number,
            "fix_kind": self.fix_kind,
            "helper_added": self.helper_added,
        }


PATCH: PatchSpec = PatchSpec(
    path="src/desi/epistemic_trajectory/extractor.py",
    line_number=236,
    fix_kind="stable_hash",
    helper_added="_stable_frame_id",
)


def patch_helper() -> object:
    """Return the helper function applied by the
    patch. Used by tests to assert determinism
    directly without round-tripping through a
    subprocess."""
    return _stable_frame_id


__all__ = [
    "PATCH", "PatchSpec", "patch_helper",
]
