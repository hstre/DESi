"""v12.2 — closed false-pattern taxonomy.

Five closed pattern shapes, with a ground-truth
``is_genuine`` flag per case. The detector
flags non-genuine patterns from text features.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache


class FalsePatternKind(str, Enum):
    NUMEROLOGICAL       = "numerological"
    SMALL_SAMPLE        = "small_sample"
    SPURIOUS_CLUSTER    = "spurious_cluster"
    OVERFIT_REGULARITY  = (
        "overfit_regularity"
    )
    GENUINE             = "genuine"


FALSE_PATTERN_KINDS: tuple[str, ...] = tuple(
    p.value for p in FalsePatternKind
)


@dataclass(frozen=True)
class PatternClaim:
    claim_id: str
    text: str
    ground_truth_kind: str
    is_genuine: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "ground_truth_kind":
                self.ground_truth_kind,
            "is_genuine": self.is_genuine,
        }


_FIXTURE: tuple[PatternClaim, ...] = (
    PatternClaim(
        "pat-num-001",
        "Every 17th prime carries a special "
        "structural meaning - the numerology "
        "is striking.",
        FalsePatternKind.NUMEROLOGICAL.value,
        is_genuine=False,
    ),
    PatternClaim(
        "pat-num-002",
        "Primes ending in 7 have a sacred "
        "geometry; this is suggestive.",
        FalsePatternKind.NUMEROLOGICAL.value,
        is_genuine=False,
    ),
    PatternClaim(
        "pat-small-001",
        "We tested 5 even numbers and the "
        "pattern holds; therefore it must "
        "generalise.",
        FalsePatternKind.SMALL_SAMPLE.value,
        is_genuine=False,
    ),
    PatternClaim(
        "pat-small-002",
        "Three datapoints confirm the trend "
        "with overwhelming evidence.",
        FalsePatternKind.SMALL_SAMPLE.value,
        is_genuine=False,
    ),
    PatternClaim(
        "pat-spur-001",
        "Primes near 100 cluster - a spurious "
        "regularity that vanishes at scale.",
        (
            FalsePatternKind
            .SPURIOUS_CLUSTER.value
        ),
        is_genuine=False,
    ),
    PatternClaim(
        "pat-spur-002",
        "There is a statistical bump at "
        "n = 256 that suggests structure - "
        "this is most likely an artifact.",
        (
            FalsePatternKind
            .SPURIOUS_CLUSTER.value
        ),
        is_genuine=False,
    ),
    PatternClaim(
        "pat-over-001",
        "Fitting a 10th-degree polynomial to "
        "8 datapoints reproduces them exactly - "
        "overfitting masquerading as a law.",
        (
            FalsePatternKind
            .OVERFIT_REGULARITY.value
        ),
        is_genuine=False,
    ),
    PatternClaim(
        "pat-over-002",
        "A bespoke heuristic with 15 free "
        "parameters explains 15 cases - this "
        "is overfit.",
        (
            FalsePatternKind
            .OVERFIT_REGULARITY.value
        ),
        is_genuine=False,
    ),
    PatternClaim(
        "pat-gen-001",
        "The set of primes is infinite "
        "(Euclid, proven).",
        FalsePatternKind.GENUINE.value,
        is_genuine=True,
    ),
    PatternClaim(
        "pat-gen-002",
        "Every even number greater than 2 "
        "decomposes into 4 = 2 + 2, "
        "6 = 3 + 3, 8 = 3 + 5 (computationally "
        "verified for small cases).",
        FalsePatternKind.GENUINE.value,
        is_genuine=True,
    ),
)


_NUMEROLOGY_MARKERS: tuple[str, ...] = (
    "sacred geometry",
    "numerology",
    "special structural meaning",
)


_SMALL_SAMPLE_MARKERS: tuple[str, ...] = (
    "we tested 5",
    "tested 3",
    "tested 4",
    "three datapoints",
    "five datapoints",
    "therefore it must generalise",
    "overwhelming evidence",
)


_SPURIOUS_MARKERS: tuple[str, ...] = (
    "near 100 cluster",
    "statistical bump",
    "most likely an artifact",
    "vanishes at scale",
)


_OVERFIT_MARKERS: tuple[str, ...] = (
    "10th-degree polynomial",
    "free parameters explains",
    "overfit",
    "overfitting masquerading",
)


_GENUINE_MARKERS: tuple[str, ...] = (
    "euclid, proven",
    "computationally verified for small cases",
)


def _matches(
    text: str, markers: tuple[str, ...],
) -> bool:
    low = text.lower()
    return any(m in low for m in markers)


def detect_kind(text: str) -> FalsePatternKind:
    """Closed-rule cascade with the most-
    specific markers first."""
    if _matches(text, _GENUINE_MARKERS):
        return FalsePatternKind.GENUINE
    if _matches(text, _NUMEROLOGY_MARKERS):
        return FalsePatternKind.NUMEROLOGICAL
    if _matches(text, _SMALL_SAMPLE_MARKERS):
        return FalsePatternKind.SMALL_SAMPLE
    if _matches(text, _SPURIOUS_MARKERS):
        return FalsePatternKind.SPURIOUS_CLUSTER
    if _matches(text, _OVERFIT_MARKERS):
        return (
            FalsePatternKind.OVERFIT_REGULARITY
        )
    return FalsePatternKind.GENUINE


@dataclass(frozen=True)
class ClassifiedPattern:
    claim_id: str
    detected_kind: str
    ground_truth_kind: str
    is_genuine_truth: bool
    flagged_as_false: bool
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "detected_kind":
                self.detected_kind,
            "ground_truth_kind":
                self.ground_truth_kind,
            "is_genuine_truth":
                self.is_genuine_truth,
            "flagged_as_false":
                self.flagged_as_false,
            "correct": self.correct,
        }


@lru_cache(maxsize=1)
def classified_patterns() -> tuple[
    ClassifiedPattern, ...,
]:
    out: list[ClassifiedPattern] = []
    for c in _FIXTURE:
        detected = detect_kind(c.text).value
        flagged = detected != (
            FalsePatternKind.GENUINE.value
        )
        out.append(ClassifiedPattern(
            claim_id=c.claim_id,
            detected_kind=detected,
            ground_truth_kind=(
                c.ground_truth_kind
            ),
            is_genuine_truth=c.is_genuine,
            flagged_as_false=flagged,
            correct=(
                detected == c.ground_truth_kind
            ),
        ))
    return tuple(out)


def fixture() -> tuple[PatternClaim, ...]:
    return _FIXTURE


def kind_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        c.ground_truth_kind for c in fixture()
    ))


__all__ = [
    "ClassifiedPattern",
    "FALSE_PATTERN_KINDS",
    "FalsePatternKind",
    "PatternClaim",
    "classified_patterns",
    "detect_kind",
    "fixture",
    "kind_counts",
]
