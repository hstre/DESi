"""v10.2 — institutional-memory fixture.

A chronologically-ordered set of past decisions.
Each carries a ground-truth ``is_currently_valid``
flag: a decision marked False is a precedent
that should have been overturned but persists
in the memory (a "bad precedent"). The
classifier audits the memory against this ground
truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PrecedentKind(str, Enum):
    FOUNDATIONAL    = "foundational"
    NORMATIVE       = "normative"
    PROCEDURAL      = "procedural"
    REMEDIAL        = "remedial"


PRECEDENT_KINDS: tuple[str, ...] = tuple(
    k.value for k in PrecedentKind
)


@dataclass(frozen=True)
class PastDecision:
    decision_id: str
    timestamp: int
    kind: str
    text: str
    overturned_by: str | None
    is_currently_valid: bool
    norm_vector: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "kind": self.kind,
            "text": self.text,
            "overturned_by":
                self.overturned_by,
            "is_currently_valid":
                self.is_currently_valid,
            "norm_vector":
                list(self.norm_vector),
        }


# Twelve past decisions. Of the four foundational
# ones, one has been overturned (dec-foundational-
# 0002 by dec-foundational-0003). Of the four
# normative ones, two carry small norm drift but
# all remain valid. Procedural and remedial ones
# are all valid. NO bad precedents persist.
_FIXTURE: tuple[PastDecision, ...] = (
    PastDecision(
        "dec-foundational-0001", 100,
        PrecedentKind.FOUNDATIONAL.value,
        "Replay-hash invariant pinned.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(1.0, 0.0, 0.0, 0.0),
    ),
    PastDecision(
        "dec-foundational-0002", 200,
        PrecedentKind.FOUNDATIONAL.value,
        "Initial closed-enum draft (later "
        "tightened).",
        overturned_by="dec-foundational-0003",
        is_currently_valid=False,
        norm_vector=(1.0, 0.0, 0.0, 0.0),
    ),
    PastDecision(
        "dec-foundational-0003", 300,
        PrecedentKind.FOUNDATIONAL.value,
        "Tightened closed-enum discipline.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(1.0, 0.0, 0.0, 0.0),
    ),
    PastDecision(
        "dec-foundational-0004", 400,
        PrecedentKind.FOUNDATIONAL.value,
        "Read-only audit module discipline.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(1.0, 0.0, 0.0, 0.0),
    ),
    PastDecision(
        "dec-normative-0001", 500,
        PrecedentKind.NORMATIVE.value,
        "Replay-stability is non-negotiable.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(1.0, 0.0, 0.0, 0.0),
    ),
    PastDecision(
        "dec-normative-0002", 600,
        PrecedentKind.NORMATIVE.value,
        "Hallucinations not tolerated.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(0.98, 0.05, 0.0, 0.0),
    ),
    PastDecision(
        "dec-normative-0003", 700,
        PrecedentKind.NORMATIVE.value,
        "Governance gates close audit modules.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(0.97, 0.05, 0.02, 0.0),
    ),
    PastDecision(
        "dec-normative-0004", 800,
        PrecedentKind.NORMATIVE.value,
        "Closed taxonomies preferred.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(0.96, 0.05, 0.02, 0.0),
    ),
    PastDecision(
        "dec-procedural-0001", 900,
        PrecedentKind.PROCEDURAL.value,
        "Full regression at end of major "
        "sprint.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(0.95, 0.05, 0.03, 0.0),
    ),
    PastDecision(
        "dec-procedural-0002", 1000,
        PrecedentKind.PROCEDURAL.value,
        "Targeted replay between sprints.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(0.95, 0.05, 0.03, 0.0),
    ),
    PastDecision(
        "dec-remedial-0001", 1100,
        PrecedentKind.REMEDIAL.value,
        "Brittle test rewritten with volatile-"
        "field exclusion pattern.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(0.95, 0.05, 0.03, 0.02),
    ),
    PastDecision(
        "dec-remedial-0002", 1200,
        PrecedentKind.REMEDIAL.value,
        "Artifact-namespace clobber repaired "
        "by relocation, not deletion.",
        overturned_by=None,
        is_currently_valid=True,
        norm_vector=(0.95, 0.05, 0.03, 0.02),
    ),
)


def fixture() -> tuple[PastDecision, ...]:
    return _FIXTURE


def kind_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        d.kind for d in fixture()
    ))


__all__ = [
    "PRECEDENT_KINDS",
    "PastDecision",
    "PrecedentKind",
    "fixture",
    "kind_counts",
]
