"""Replay each claim against the ``artifacts/`` tree — Aufgabe 3."""
from __future__ import annotations

import json
import pathlib
from typing import Any

from .claim import (
    ClaimKind,
    ClaimVerdict,
    ExplicitClaim,
    ReplayedClaim,
)


def _collect_artifact_texts(
    artifact_root: pathlib.Path,
) -> tuple[str, dict[str, Any]]:
    """Return (concatenated_text_blob, per_path_json_payload).

    The blob is used for fast substring containment checks; the
    payload dict is used to walk specific JSON values when a claim
    references a specific artifact path.
    """
    blob_parts: list[str] = []
    by_path: dict[str, Any] = {}
    for p in sorted(artifact_root.rglob("*.json")):
        raw = p.read_text(encoding="utf-8")
        blob_parts.append(raw)
        rel = p.relative_to(artifact_root.parent).as_posix()
        try:
            by_path[rel] = json.loads(raw)
        except json.JSONDecodeError:
            by_path[rel] = None
    return "\n".join(blob_parts), by_path


def _walk_keys(obj: Any, key: str) -> list[Any]:
    """Find every value at any depth whose key equals ``key``."""
    out: list[Any] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                out.append(v)
            out.extend(_walk_keys(v, key))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(_walk_keys(item, key))
    return out


def _replay_hash_claim(
    claim: ExplicitClaim,
    blob: str,
    by_path: dict[str, Any],
) -> ReplayedClaim:
    hexv = claim.value
    if hexv not in blob:
        return ReplayedClaim(
            claim, ClaimVerdict.MISSING_ARTIFACT,
            reason=f"hex {hexv} not present in artifacts/",
        )
    # If the claim references a specific artifact, compare its
    # relevant hash field for an exact match.
    if claim.referenced_artifact:
        rel = claim.referenced_artifact
        payload = by_path.get(rel)
        if payload is None:
            return ReplayedClaim(
                claim, ClaimVerdict.MISSING_ARTIFACT,
                reason=f"referenced {rel!r} missing",
            )
        # Search for any field whose name matches the claim's key.
        if claim.key:
            values = _walk_keys(payload, claim.key)
            if values and not any(v == hexv for v in values):
                return ReplayedClaim(
                    claim, ClaimVerdict.HASH_MISMATCH,
                    reason=(
                        f"{rel}:{claim.key} = "
                        f"{values[0]!r}, doc says {hexv!r}"
                    ),
                )
    return ReplayedClaim(claim, ClaimVerdict.VERIFIED)


def _replay_phase_claim(
    claim: ExplicitClaim,
    blob: str,
    by_path: dict[str, Any],
) -> ReplayedClaim:
    # When a referenced artifact is given, it takes precedence — a
    # phase mismatch there must surface as VALUE_MISMATCH even if
    # the value happens to appear elsewhere in artifacts/.
    if claim.referenced_artifact:
        payload = by_path.get(claim.referenced_artifact)
        if isinstance(payload, dict) and "phase" in payload:
            if payload["phase"] != claim.value:
                return ReplayedClaim(
                    claim, ClaimVerdict.VALUE_MISMATCH,
                    reason=(
                        f"{claim.referenced_artifact}:phase = "
                        f"{payload['phase']!r}, doc says "
                        f"{claim.value!r}"
                    ),
                )
            return ReplayedClaim(claim, ClaimVerdict.VERIFIED)
    if claim.value not in blob:
        return ReplayedClaim(
            claim, ClaimVerdict.MISSING_ARTIFACT,
            reason=f"phase {claim.value!r} absent from artifacts/",
        )
    return ReplayedClaim(claim, ClaimVerdict.VERIFIED)


def _replay_numeric_claim(
    claim: ExplicitClaim,
    blob: str,
    by_path: dict[str, Any],
) -> ReplayedClaim:
    if not claim.key:
        return ReplayedClaim(
            claim, ClaimVerdict.AMBIGUOUS_REFERENCE,
            reason="no key extracted",
        )
    try:
        doc_value = float(claim.value)
    except ValueError:
        return ReplayedClaim(
            claim, ClaimVerdict.AMBIGUOUS_REFERENCE,
            reason="value is not a float",
        )
    # Prefer the referenced artifact if available.
    if claim.referenced_artifact:
        payload = by_path.get(claim.referenced_artifact)
        if payload is not None:
            values = _walk_keys(payload, claim.key)
            if not values:
                return ReplayedClaim(
                    claim, ClaimVerdict.AMBIGUOUS_REFERENCE,
                    reason=(
                        f"{claim.referenced_artifact} has no "
                        f"key {claim.key!r}"
                    ),
                )
            if any(_approx_equal(v, doc_value) for v in values):
                return ReplayedClaim(claim, ClaimVerdict.VERIFIED)
            return ReplayedClaim(
                claim, ClaimVerdict.VALUE_MISMATCH,
                reason=(
                    f"{claim.referenced_artifact}:{claim.key} = "
                    f"{values[0]!r}, doc says {doc_value!r}"
                ),
            )
    # No referenced artifact: search globally for any matching field.
    matched_in: list[str] = []
    for path, payload in by_path.items():
        if payload is None:
            continue
        values = _walk_keys(payload, claim.key)
        if values and any(_approx_equal(v, doc_value) for v in values):
            matched_in.append(path)
    if matched_in:
        return ReplayedClaim(
            claim, ClaimVerdict.VERIFIED,
            reason=f"matched in {matched_in[0]}",
        )
    return ReplayedClaim(
        claim, ClaimVerdict.AMBIGUOUS_REFERENCE,
        reason=f"no artifact had key {claim.key!r} = {doc_value!r}",
    )


def _replay_count_claim(
    claim: ExplicitClaim,
    blob: str,
    by_path: dict[str, Any],
) -> ReplayedClaim:
    # Ratios like "30/30" are hard to anchor without context.
    if claim.value in blob:
        return ReplayedClaim(claim, ClaimVerdict.VERIFIED)
    return ReplayedClaim(
        claim, ClaimVerdict.AMBIGUOUS_REFERENCE,
        reason=f"ratio {claim.value!r} not found verbatim",
    )


def _approx_equal(a: Any, b: float) -> bool:
    try:
        return abs(float(a) - b) < 1e-4
    except (TypeError, ValueError):
        return False


def replay_claims(
    claims: tuple[ExplicitClaim, ...],
    *,
    artifact_root: pathlib.Path,
) -> tuple[ReplayedClaim, ...]:
    blob, by_path = _collect_artifact_texts(artifact_root)
    out: list[ReplayedClaim] = []
    for c in claims:
        if c.kind is ClaimKind.HASH:
            out.append(_replay_hash_claim(c, blob, by_path))
        elif c.kind is ClaimKind.PHASE:
            out.append(_replay_phase_claim(c, blob, by_path))
        elif c.kind is ClaimKind.NUMERIC:
            out.append(_replay_numeric_claim(c, blob, by_path))
        elif c.kind is ClaimKind.COUNT:
            out.append(_replay_count_claim(c, blob, by_path))
        else:
            out.append(ReplayedClaim(
                c, ClaimVerdict.AMBIGUOUS_REFERENCE,
                reason="unknown claim kind",
            ))
    return tuple(out)


__all__ = ["replay_claims"]
