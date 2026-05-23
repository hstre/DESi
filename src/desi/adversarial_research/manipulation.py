"""v13.2 — closed taxonomy of research-
manipulation kinds plus a synthetic fixture
of manipulated and honest claims.

The directive's six closed kinds:

* SELECTIVE_REPORTING
* HIDDEN_NULL_RESULT
* CONFIDENCE_INFLATION
* BENCHMARK_CHERRY_PICK
* CAUSAL_EXAGGERATION
* METHODOLOGICAL_LAUNDERING

Plus HONEST as the residual.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ManipulationKind(str, Enum):
    HONEST                    = "honest"
    SELECTIVE_REPORTING       = (
        "selective_reporting"
    )
    HIDDEN_NULL_RESULT        = (
        "hidden_null_result"
    )
    CONFIDENCE_INFLATION      = (
        "confidence_inflation"
    )
    BENCHMARK_CHERRY_PICK     = (
        "benchmark_cherry_pick"
    )
    CAUSAL_EXAGGERATION       = (
        "causal_exaggeration"
    )
    METHODOLOGICAL_LAUNDERING = (
        "methodological_laundering"
    )


MANIPULATION_KINDS: tuple[str, ...] = tuple(
    m.value for m in ManipulationKind
)


@dataclass(frozen=True)
class ManipulatedClaim:
    claim_id: str
    text: str
    kind: str
    confidence_claimed: float
    confidence_warranted: float

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "kind": self.kind,
            "confidence_claimed":
                self.confidence_claimed,
            "confidence_warranted":
                self.confidence_warranted,
        }


_FIXTURE: tuple[ManipulatedClaim, ...] = (
    ManipulatedClaim(
        "mc-honest-001",
        "Pre-registered RCT reports a 4 "
        "percent reduction (95% CI: 2-6).",
        ManipulationKind.HONEST.value,
        confidence_claimed=0.80,
        confidence_warranted=0.80,
    ),
    ManipulatedClaim(
        "mc-honest-002",
        "Replication confirms the primary "
        "outcome; null results published "
        "alongside.",
        ManipulationKind.HONEST.value,
        confidence_claimed=0.85,
        confidence_warranted=0.85,
    ),
    ManipulatedClaim(
        "mc-sel-001",
        "We report only the subgroup where "
        "our method wins; other subgroups "
        "omitted.",
        (
            ManipulationKind
            .SELECTIVE_REPORTING.value
        ),
        confidence_claimed=0.90,
        confidence_warranted=0.40,
    ),
    ManipulatedClaim(
        "mc-null-001",
        "Our primary endpoint shows a "
        "significant effect (secondary null "
        "results not shown).",
        (
            ManipulationKind
            .HIDDEN_NULL_RESULT.value
        ),
        confidence_claimed=0.85,
        confidence_warranted=0.35,
    ),
    ManipulatedClaim(
        "mc-conf-001",
        "This is conclusively proven by our "
        "p<0.05 result on a single trial.",
        (
            ManipulationKind
            .CONFIDENCE_INFLATION.value
        ),
        confidence_claimed=0.99,
        confidence_warranted=0.45,
    ),
    ManipulatedClaim(
        "mc-bench-001",
        "Our model wins on the cherry-picked "
        "benchmark suite where conditions are "
        "favourable.",
        (
            ManipulationKind
            .BENCHMARK_CHERRY_PICK.value
        ),
        confidence_claimed=0.90,
        confidence_warranted=0.30,
    ),
    ManipulatedClaim(
        "mc-causal-001",
        "Observational correlation therefore "
        "implies causation in this population.",
        (
            ManipulationKind
            .CAUSAL_EXAGGERATION.value
        ),
        confidence_claimed=0.95,
        confidence_warranted=0.20,
    ),
    ManipulatedClaim(
        "mc-laundry-001",
        "Methodology was retro-fitted after "
        "results to match conclusions; "
        "renamed as 'principled framework'.",
        (
            ManipulationKind
            .METHODOLOGICAL_LAUNDERING.value
        ),
        confidence_claimed=0.95,
        confidence_warranted=0.10,
    ),
)


_MARKERS: tuple[tuple[str, str], ...] = (
    ("only the subgroup",
     ManipulationKind.SELECTIVE_REPORTING.value),
    ("null results not shown",
     ManipulationKind.HIDDEN_NULL_RESULT.value),
    ("conclusively proven by our p",
     ManipulationKind.CONFIDENCE_INFLATION.value),
    ("cherry-picked benchmark",
     ManipulationKind.BENCHMARK_CHERRY_PICK.value),
    ("correlation therefore implies "
     "causation",
     ManipulationKind.CAUSAL_EXAGGERATION.value),
    ("retro-fitted",
     (
         ManipulationKind
         .METHODOLOGICAL_LAUNDERING.value
     )),
    ("renamed as 'principled framework'",
     (
         ManipulationKind
         .METHODOLOGICAL_LAUNDERING.value
     )),
)


def detect_kind(
    text: str,
) -> ManipulationKind:
    low = text.lower()
    for marker, kind in _MARKERS:
        if marker in low:
            return ManipulationKind(kind)
    return ManipulationKind.HONEST


def fixture() -> tuple[ManipulatedClaim, ...]:
    return _FIXTURE


def kind_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        c.kind for c in fixture()
    ))


__all__ = [
    "MANIPULATION_KINDS",
    "ManipulatedClaim",
    "ManipulationKind",
    "detect_kind",
    "fixture",
    "kind_counts",
]
