"""v6.0 — frame diversity, leap detection, bridge
audit. The audit composes the extractor's output
into per-paper grades and corpus-level
distributions."""
from __future__ import annotations

import math
from collections import Counter
from functools import lru_cache

from ..open_world.claim_stream import (
    FRAME_TYPES, FrameType, classify_frame,
)
from .claim_extractor import (
    ExtractedKind, all_scores,
    corpus_extractions,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def frame_distribution() -> dict[str, int]:
    cnt: Counter[str] = Counter()
    for _, units in corpus_extractions():
        for u in units:
            if u.kind != (
                ExtractedKind.CLAIM.value
            ):
                continue
            cnt[
                classify_frame(u.sentence).value
            ] += 1
    return {k: cnt[k] for k in sorted(cnt)}


def frame_diversity() -> float:
    """Normalised Shannon entropy over the
    frame-type distribution of extracted claims.
    Zero means all claims are one frame; 1.0
    means uniform across the closed frame enum.
    """
    counts = frame_distribution()
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    max_h = math.log2(len(FRAME_TYPES))
    if max_h <= 0:
        return 0.0
    return _round(h / max_h)


def claim_extraction_accuracy() -> float:
    """Mean F-score across papers, weighted
    equally per paper. Each paper contributes:

        2 * P * R / (P + R)

    where P = stated_hit / max(extracted_claims,
    1) and R = stated_hit / stated_total."""
    scores = all_scores()
    if not scores:
        return 0.0
    f_scores = []
    extr = {
        s.paper_id: sum(
            1 for u in units
            if u.kind == (
                ExtractedKind.CLAIM.value
            )
        )
        for s, (_, units) in zip(
            scores,
            [
                (s.paper_id, units)
                for s, (_, units) in zip(
                    scores,
                    corpus_extractions(),
                )
            ],
        )
    }
    for s in scores:
        if s.stated_total == 0:
            continue
        recall = s.stated_hit / s.stated_total
        extracted_claims = extr.get(
            s.paper_id, 0,
        )
        if extracted_claims == 0:
            precision = 0.0
        else:
            precision = (
                s.stated_hit
                / extracted_claims
            )
        if (precision + recall) == 0:
            f_scores.append(0.0)
        else:
            f_scores.append(
                2 * precision * recall
                / (precision + recall),
            )
    if not f_scores:
        return 0.0
    return _round(
        sum(f_scores) / len(f_scores),
    )


def unsupported_leap_detection() -> float:
    """Recall on the ground-truth leap set."""
    scores = all_scores()
    total = sum(s.leap_total for s in scores)
    hit = sum(s.leap_hit for s in scores)
    if total == 0:
        return 1.0
    return _round(hit / total)


def bridge_audit_coverage() -> float:
    """Recall on the ground-truth bridge
    licence set."""
    scores = all_scores()
    total = sum(s.bridge_total for s in scores)
    hit = sum(s.bridge_hit for s in scores)
    if total == 0:
        return 1.0
    return _round(hit / total)


@lru_cache(maxsize=1)
def blindness_pools_added() -> int:
    """An UNKNOWN-frame extracted claim is a
    blindness candidate; we count distinct
    papers whose extracted claims contain at
    least one UNKNOWN-frame entry as new
    blindness pools."""
    out = set()
    for p, units in corpus_extractions():
        for u in units:
            if u.kind != (
                ExtractedKind.CLAIM.value
            ):
                continue
            if classify_frame(
                u.sentence,
            ) == FrameType.UNKNOWN:
                out.add(p.paper_id)
                break
    return len(out)


__all__ = [
    "blindness_pools_added",
    "bridge_audit_coverage",
    "claim_extraction_accuracy",
    "frame_distribution",
    "frame_diversity",
    "unsupported_leap_detection",
]
