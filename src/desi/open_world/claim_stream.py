"""v5.1 — frame / conflict classification over
the open-world claim stream.

Frame types and conflict kinds are closed enums.
Classification is purely text-pattern-based and
deterministic. A claim that fits no frame
contributes to a blindness pool; a pair of
claims with conflicting frames contributes to a
conflict type.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .sources import (
    CLAIM_SOURCES, ClaimSource, source_claims,
)


class FrameType(str, Enum):
    DEFINITIONAL   = "definitional"
    CAUSAL         = "causal"
    EVALUATIVE     = "evaluative"
    PREDICTIVE     = "predictive"
    NORMATIVE      = "normative"
    REPORT         = "report"
    BUG_REPORT     = "bug_report"
    UNKNOWN        = "unknown"


FRAME_TYPES: tuple[str, ...] = tuple(
    f.value for f in FrameType
)


class ConflictKind(str, Enum):
    CONTRADICTION  = "contradiction"
    MODAL_CLASH    = "modal_clash"
    TEMPORAL_CLASH = "temporal_clash"
    DOMAIN_CLASH   = "domain_clash"


CONFLICT_KINDS: tuple[str, ...] = tuple(
    c.value for c in ConflictKind
)


@dataclass(frozen=True)
class Claim:
    claim_id: str
    source: str
    text: str
    frame: str

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "source": self.source,
            "text": self.text,
            "frame": self.frame,
        }


def classify_frame(text: str) -> FrameType:
    """Pure text-pattern classifier. The order
    matters: more-specific markers are checked
    first so an adversarial conjunction beats a
    plain definition.
    """
    low = text.lower()
    if (
        "both at once" in low
        or "trust me bro" in low
    ):
        return FrameType.UNKNOWN
    if "bug:" in low:
        return FrameType.BUG_REPORT
    if (
        "feature request" in low
        or "cannot reproduce" in low
    ):
        return FrameType.BUG_REPORT
    if (
        "is a concept" in low
        or "refers to" in low
        or "in the standard definition" in low
    ):
        return FrameType.DEFINITIONAL
    if (
        "we show that" in low
        or "we prove that" in low
        or "empirical evidence" in low
    ):
        return FrameType.CAUSAL
    if (
        "this paper argues" in low
        or "policy implications" in low
    ):
        return FrameType.EVALUATIVE
    if (
        "predicts" in low
        or "within five years" in low
        or "by 2030" in low
    ):
        return FrameType.PREDICTIVE
    if (
        "morally required" in low
        or "should be" in low
    ):
        return FrameType.NORMATIVE
    if (
        "sources confirm" in low
        or "breaking:" in low
        or "experts say" in low
    ):
        return FrameType.REPORT
    return FrameType.UNKNOWN


def _conflict_signal(text: str) -> tuple[
    bool, bool, bool,
]:
    """Return (has_modal, has_temporal,
    has_domain) markers."""
    low = text.lower()
    modal = any(
        m in low for m in (
            "always", "cannot", "necessary",
            "required", "should",
        )
    )
    temporal = any(
        t in low for t in (
            "until", "within", "by 2030",
            "before", "after",
        )
    )
    domain = any(
        d in low for d in (
            "policy", "scientific",
            "production", "ci",
            "ci.",
        )
    )
    return modal, temporal, domain


def detect_conflict(
    a: Claim, b: Claim,
) -> ConflictKind | None:
    """Pairwise conflict detector. Pairs of
    UNKNOWN-frame claims do NOT count as
    conflicts; they count as blindness."""
    if a.frame == FrameType.UNKNOWN.value:
        return None
    if b.frame == FrameType.UNKNOWN.value:
        return None
    if a.frame == b.frame:
        return None
    am, at, ad = _conflict_signal(a.text)
    bm, bt, bd = _conflict_signal(b.text)
    if am and bm:
        return ConflictKind.MODAL_CLASH
    if at and bt:
        return ConflictKind.TEMPORAL_CLASH
    if ad and bd:
        return ConflictKind.DOMAIN_CLASH
    if {a.frame, b.frame} == {
        FrameType.DEFINITIONAL.value,
        FrameType.NORMATIVE.value,
    }:
        return ConflictKind.CONTRADICTION
    if {a.frame, b.frame} == {
        FrameType.CAUSAL.value,
        FrameType.REPORT.value,
    }:
        return ConflictKind.CONTRADICTION
    return None


@dataclass(frozen=True)
class BlindnessPool:
    pool_id: str
    source: str
    claim_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "pool_id": self.pool_id,
            "source": self.source,
            "claim_ids": list(self.claim_ids),
        }


@lru_cache(maxsize=1)
def stream_claims() -> tuple[Claim, ...]:
    """Closed claim stream: 6 sources x 5 claims
    each, seed=0. Frozen across all replays."""
    out: list[Claim] = []
    seed = 0
    count_per_source = 5
    for src_name in CLAIM_SOURCES:
        src = ClaimSource(src_name)
        for i, text in enumerate(
            source_claims(
                src, seed, count_per_source,
            ),
        ):
            cid = f"{src.value}:{i:02d}"
            out.append(Claim(
                claim_id=cid, source=src.value,
                text=text,
                frame=classify_frame(text).value,
            ))
    return tuple(out)


@lru_cache(maxsize=1)
def all_conflicts() -> tuple[
    tuple[str, str, str], ...,
]:
    """Pairwise conflicts across the stream.
    Returns tuples of (claim_a_id, claim_b_id,
    conflict_kind). Sorted for determinism."""
    claims = stream_claims()
    out: list[tuple[str, str, str]] = []
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            kind = detect_conflict(
                claims[i], claims[j],
            )
            if kind is not None:
                out.append((
                    claims[i].claim_id,
                    claims[j].claim_id,
                    kind.value,
                ))
    out.sort()
    return tuple(out)


@lru_cache(maxsize=1)
def blindness_pools() -> tuple[
    BlindnessPool, ...,
]:
    """Cluster UNKNOWN-frame claims by source.
    A pool is emitted only when a source produces
    >= 2 unknown-frame claims (so a one-off
    glitch doesn't count as structural
    blindness)."""
    claims = stream_claims()
    grouped: dict[str, list[str]] = {}
    for c in claims:
        if c.frame == FrameType.UNKNOWN.value:
            grouped.setdefault(
                c.source, [],
            ).append(c.claim_id)
    out: list[BlindnessPool] = []
    for src in sorted(grouped.keys()):
        ids = tuple(sorted(grouped[src]))
        if len(ids) >= 2:
            out.append(BlindnessPool(
                pool_id=f"blind:{src}",
                source=src, claim_ids=ids,
            ))
    return tuple(out)


def frame_counts() -> dict[str, int]:
    cnt = Counter(c.frame for c in stream_claims())
    return {k: cnt[k] for k in sorted(cnt)}


def conflict_kind_counts() -> dict[str, int]:
    cnt = Counter(
        kind for _, _, kind in all_conflicts()
    )
    return {k: cnt[k] for k in sorted(cnt)}


def source_counts() -> dict[str, int]:
    cnt = Counter(c.source for c in stream_claims())
    return {k: cnt[k] for k in sorted(cnt)}


__all__ = [
    "BlindnessPool",
    "CONFLICT_KINDS",
    "Claim",
    "ConflictKind",
    "FRAME_TYPES",
    "FrameType",
    "all_conflicts",
    "blindness_pools",
    "classify_frame",
    "conflict_kind_counts",
    "detect_conflict",
    "frame_counts",
    "source_counts",
    "stream_claims",
]
