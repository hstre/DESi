"""Aufgabe 9 — novelty audit for UNKNOWN chains.

Every chain the classifier returned as ``UNKNOWN`` is
inspected and assigned a ``NoveltyKind``:

* ``TRUE_NOVELTY``        — confidence in UNKNOWN-ness is
  high (no canonical centroid is obviously close) AND no
  canonical cascade rule was within one feature of firing
  (i.e. the chain is a structurally new failure mode).
* ``CLASSIFIER_UNCERT``   — confidence in UNKNOWN-ness is
  moderate: at least one canonical class was nearly
  closest, the cascade just did not pick a winner.
* ``TAXONOMY_MISS``       — the chain looks like a v5.0
  failure mode but the cascade's threshold cut-off
  prevented assignment. Recoverable by a small relaxation
  of the cascade.

The audit metric is ``true_novelty_fraction`` — fraction
of UNKNOWN chains classified as ``TRUE_NOVELTY``.
"""
from __future__ import annotations

from dataclasses import dataclass

from .canonical import (
    CanonicalReference, load_canonical_reference,
)
from .classifier import ClassificationResult
from .enums import NoveltyKind


_TRUE_NOVELTY_CONFIDENCE = 0.55
_TAXONOMY_MISS_DELTA     = 1.5


@dataclass(frozen=True)
class NoveltyAuditEntry:
    chain_id: str
    domain: str
    novelty_kind: str
    confidence: float
    d_min: float
    nearest_canonical: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "novelty_kind": self.novelty_kind,
            "confidence": self.confidence,
            "d_min": self.d_min,
            "nearest_canonical": self.nearest_canonical,
        }


def _l1(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b))


def audit_unknown_chains(
    results: tuple[ClassificationResult, ...],
    ref: CanonicalReference | None = None,
) -> tuple[NoveltyAuditEntry, ...]:
    r = ref if ref is not None else load_canonical_reference()
    out: list[NoveltyAuditEntry] = []
    for res in results:
        if res.assigned_class != "UNKNOWN":
            continue
        distances = {
            c.name: _l1(res.feature_vec, c.centroid)
            for c in r.classes
        }
        nearest = min(distances, key=distances.get)
        d_min = distances[nearest]
        # The chain is a *taxonomy miss* if some canonical
        # centroid is very close (within delta) — the
        # cascade rule was nearly applicable.
        if d_min < _TAXONOMY_MISS_DELTA:
            kind = NoveltyKind.TAXONOMY_MISS.value
        elif res.confidence >= _TRUE_NOVELTY_CONFIDENCE:
            kind = NoveltyKind.TRUE_NOVELTY.value
        else:
            kind = NoveltyKind.CLASSIFIER_UNCERT.value
        out.append(NoveltyAuditEntry(
            chain_id=res.chain_id, domain=res.domain,
            novelty_kind=kind,
            confidence=res.confidence,
            d_min=round(d_min, 6),
            nearest_canonical=nearest,
        ))
    return tuple(out)


def true_novelty_fraction(
    results: tuple[ClassificationResult, ...],
    entries: tuple[NoveltyAuditEntry, ...],
) -> float:
    """Fraction of *all* classified chains tagged as
    TRUE_NOVELTY. Numerator counts only TRUE_NOVELTY
    entries; denominator is the size of the full
    classification set, so the metric stays directly
    comparable to ``unknown_fraction``."""
    if not results:
        return 0.0
    novel = sum(
        1 for e in entries
        if e.novelty_kind == NoveltyKind.TRUE_NOVELTY.value
    )
    return round(novel / len(results), 6)


__all__ = [
    "NoveltyAuditEntry", "audit_unknown_chains",
    "true_novelty_fraction",
]
