"""Aufgabe 5 — best-fit classifier for the new corpus.

Every chain is classified into one of the eight canonical
``MT_*`` classes or ``UNKNOWN``. No clustering is
performed; we apply the v5.0 closed cascade
``classify_sample_features`` to the features extracted by
the v5.0 ``extract_features`` pipeline.

Confidence is a cascade-anchored score:

* For an assigned ``MT_*`` class: a floor of 0.70 (the
  v5.0 cascade fired deterministically on binary feature
  triggers, so the rule-match itself is certain) plus a
  proximity bonus of up to 0.30 based on how close the
  chain's feature vector is to the canonical centroid for
  the assigned class (small classes' tight centroids do
  not penalise generalisation).
* For ``UNKNOWN``: ``d_min / d_max`` — high when every
  canonical centroid is roughly equidistant (the cascade
  emitted ``MT_OTHER`` and no canonical class would have
  been a clearly better fit).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..methodology_transfer.corpus import TransferChain
from ..methodology_transfer.feature_extraction import (
    extract_features,
)
from ..methodology_transfer.taxonomy import (
    TaxonomyClass, classify_sample_features,
)
from .canonical import (
    CanonicalReference, load_canonical_reference,
)
from .corpus import GeneralizationChain


_UNKNOWN = "UNKNOWN"
_OTHER = TaxonomyClass.MT_OTHER.value
_CASCADE_FLOOR = 0.75
_PROXIMITY_BONUS = 0.25
_TYPICAL_D = 15.0


@dataclass(frozen=True)
class ClassificationResult:
    chain_id: str
    domain: str
    ground_truth: str
    assigned_class: str       # MT_* or "UNKNOWN"
    confidence: float
    distance_to_assigned: float
    feature_vec: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "ground_truth": self.ground_truth,
            "assigned_class": self.assigned_class,
            "confidence": self.confidence,
            "distance_to_assigned":
                self.distance_to_assigned,
        }


def _l1(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b))


def _to_transfer_chain(
    c: GeneralizationChain,
) -> TransferChain:
    """Wrap a v5.2 chain in a v5.0 TransferChain envelope
    so the v5.0 feature pipeline can read it. The wrapper
    is purely for feature-extraction; no v5.0 corpus
    artifact is touched."""
    return TransferChain(
        chain_id=c.chain_id, domain=c.domain, text=c.text,
        ground_truth=c.ground_truth,
        rationale=c.rationale,
    )


def _confidence(
    feats: tuple[float, ...],
    assigned_class: str,
    ref: CanonicalReference,
) -> tuple[float, float]:
    """Returns ``(confidence, distance_to_assigned)``."""
    distances: dict[str, float] = {}
    for c in ref.classes:
        distances[c.name] = _l1(feats, c.centroid)
    d_max = max(distances.values())
    d_min = min(distances.values())
    if d_max <= 0.0:
        return 1.0, 0.0
    if assigned_class == _UNKNOWN:
        return round(d_min / d_max, 6), round(d_min, 6)
    d_a = distances[assigned_class]
    proximity = max(0.0, 1.0 - d_a / _TYPICAL_D)
    conf = _CASCADE_FLOOR + _PROXIMITY_BONUS * proximity
    return round(conf, 6), round(d_a, 6)


def classify_chain(
    chain: GeneralizationChain,
    ref: CanonicalReference | None = None,
) -> ClassificationResult:
    r = ref if ref is not None else load_canonical_reference()
    sample = extract_features(_to_transfer_chain(chain))
    raw = classify_sample_features(sample.features)
    assigned = _UNKNOWN if raw == _OTHER else raw
    conf, dist = _confidence(
        sample.features, assigned, r,
    )
    return ClassificationResult(
        chain_id=chain.chain_id, domain=chain.domain,
        ground_truth=chain.ground_truth,
        assigned_class=assigned,
        confidence=conf,
        distance_to_assigned=dist,
        feature_vec=sample.features,
    )


def classify_all(
    chains: tuple[GeneralizationChain, ...],
    ref: CanonicalReference | None = None,
) -> tuple[ClassificationResult, ...]:
    r = ref if ref is not None else load_canonical_reference()
    return tuple(classify_chain(c, r) for c in chains)


__all__ = [
    "ClassificationResult", "classify_all", "classify_chain",
]
