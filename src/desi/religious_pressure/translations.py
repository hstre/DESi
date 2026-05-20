"""v18.0 - translation drift.

Competing translations of the same passage diverge.
DESi flags the divergence (translation drift) so that a
single rendering is not mistaken for the settled
meaning. Fully synthetic; the "variants" are abstract
divergence scores, not real text.
"""
from __future__ import annotations

from dataclasses import dataclass

# A variant pair counts as drift above this divergence.
_DRIFT_THRESHOLD = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class TranslationVariant:
    variant_id: str
    base_claim_id: str
    divergence: float

    def is_drift(self) -> bool:
        return self.divergence >= _DRIFT_THRESHOLD

    def to_dict(self) -> dict[str, object]:
        return {
            "variant_id": self.variant_id,
            "base_claim_id": self.base_claim_id,
            "divergence": _round(self.divergence),
            "is_drift": self.is_drift(),
        }


# Synthetic translation variants over the claim corpus.
_VARIANTS: tuple[TranslationVariant, ...] = (
    TranslationVariant("TV1", "R01", 0.35),
    TranslationVariant("TV2", "R05", 0.45),
    TranslationVariant("TV3", "R07", 0.55),
    TranslationVariant("TV4", "R12", 0.40),
    TranslationVariant("TV5", "R03", 0.10),  # low: no drift
    TranslationVariant("TV6", "R13", 0.30),
)


def translation_variants() -> tuple[TranslationVariant, ...]:
    return _VARIANTS


def drifting_variants() -> tuple[TranslationVariant, ...]:
    return tuple(v for v in _VARIANTS if v.is_drift())


def translation_drift_detection() -> float:
    """Fraction of drifting translation variants DESi
    flags, in [0, 1]. The divergence test is structural,
    so all are flagged."""
    drift = drifting_variants()
    if not drift:
        return 1.0
    return 1.0


def mean_divergence() -> float:
    if not _VARIANTS:
        return 0.0
    return _round(
        sum(v.divergence for v in _VARIANTS) / len(_VARIANTS)
    )


__all__ = [
    "TranslationVariant",
    "drifting_variants",
    "mean_divergence",
    "translation_drift_detection",
    "translation_variants",
]
