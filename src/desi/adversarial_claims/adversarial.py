"""v6.1 — closed adversarial-trap taxonomy
plus a synthetic fixture of trapped claims.

The taxonomy is intentionally narrow so the
detector can be a pattern matcher with no PRNG
and no model state. Each ``TrappedClaim`` in the
fixture carries its ground-truth ``trap`` value;
the detector must reproduce that label."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TrapKind(str, Enum):
    NORMAL                       = "normal"
    RHETORICAL_OVERREACH         = (
        "rhetorical_overreach"
    )
    STATISTICAL_TRICK            = (
        "statistical_trick"
    )
    CIRCULAR_REASONING           = (
        "circular_reasoning"
    )
    AUTHORITY_APPEAL             = (
        "authority_appeal"
    )
    CHERRY_PICKING               = (
        "cherry_picking"
    )
    CAUSATION_CORRELATION_CONFUSION = (
        "causation_correlation_confusion"
    )
    HIDDEN_PREMISE               = (
        "hidden_premise"
    )


TRAP_KINDS: tuple[str, ...] = tuple(
    t.value for t in TrapKind
)


# Order matters: more-specific markers must come
# first so AUTHORITY_APPEAL beats RHETORICAL_
# OVERREACH on "trust me bro: this proves X".
_TRAP_MARKERS: tuple[tuple[str, str], ...] = (
    ("trust me bro",
     TrapKind.AUTHORITY_APPEAL.value),
    ("100 percent effective",
     TrapKind.STATISTICAL_TRICK.value),
    ("100% effective",
     TrapKind.STATISTICAL_TRICK.value),
    ("in the subset where",
     TrapKind.CHERRY_PICKING.value),
    ("in the cherry-picked",
     TrapKind.CHERRY_PICKING.value),
    ("correlates with",
     TrapKind.CAUSATION_CORRELATION_CONFUSION
     .value),
    ("therefore x causes",
     TrapKind.CAUSATION_CORRELATION_CONFUSION
     .value),
    ("obviously",
     TrapKind.HIDDEN_PREMISE.value),
    ("because of itself",
     TrapKind.CIRCULAR_REASONING.value),
    ("circular by design",
     TrapKind.CIRCULAR_REASONING.value),
    ("this proves general intelligence",
     TrapKind.RHETORICAL_OVERREACH.value),
    ("solve all problems",
     TrapKind.RHETORICAL_OVERREACH.value),
)


def detect_trap(text: str) -> TrapKind:
    low = text.lower()
    for marker, kind in _TRAP_MARKERS:
        if marker in low:
            return TrapKind(kind)
    return TrapKind.NORMAL


@dataclass(frozen=True)
class TrappedClaim:
    claim_id: str
    text: str
    trap: str
    ambiguous: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "trap": self.trap,
            "ambiguous": self.ambiguous,
        }


_FIXTURE: tuple[TrappedClaim, ...] = (
    TrappedClaim(
        claim_id="adv-001",
        text=(
            "The new model is 100 percent "
            "effective on the validation set."
        ),
        trap=TrapKind.STATISTICAL_TRICK.value,
        ambiguous=False,
    ),
    TrappedClaim(
        claim_id="adv-002",
        text=(
            "Trust me bro: this proves general "
            "intelligence."
        ),
        trap=TrapKind.AUTHORITY_APPEAL.value,
        ambiguous=False,
    ),
    TrappedClaim(
        claim_id="adv-003",
        text=(
            "Vaccine uptake correlates with "
            "income; therefore X causes Y."
        ),
        trap=(
            TrapKind
            .CAUSATION_CORRELATION_CONFUSION
            .value
        ),
        ambiguous=False,
    ),
    TrappedClaim(
        claim_id="adv-004",
        text=(
            "Obviously the regulator should "
            "act now."
        ),
        trap=TrapKind.HIDDEN_PREMISE.value,
        ambiguous=False,
    ),
    TrappedClaim(
        claim_id="adv-005",
        text=(
            "In the subset where the model "
            "works, accuracy is 99 percent."
        ),
        trap=TrapKind.CHERRY_PICKING.value,
        ambiguous=False,
    ),
    TrappedClaim(
        claim_id="adv-006",
        text=(
            "The mechanism is valid because of "
            "itself - the math is circular by "
            "design."
        ),
        trap=TrapKind.CIRCULAR_REASONING.value,
        ambiguous=False,
    ),
    TrappedClaim(
        claim_id="adv-007",
        text=(
            "This proves general intelligence."
        ),
        trap=(
            TrapKind.RHETORICAL_OVERREACH.value
        ),
        ambiguous=False,
    ),
    TrappedClaim(
        claim_id="adv-008",
        text=(
            "Studies show that many factors "
            "are often involved."
        ),
        trap=TrapKind.NORMAL.value,
        ambiguous=True,
    ),
    TrappedClaim(
        claim_id="adv-009",
        text=(
            "In some cases the effect is "
            "recently observed."
        ),
        trap=TrapKind.NORMAL.value,
        ambiguous=True,
    ),
    TrappedClaim(
        claim_id="adv-010",
        text=(
            "The intervention reduced mortality "
            "by 4 percent (95% CI: 2 to 6)."
        ),
        trap=TrapKind.NORMAL.value,
        ambiguous=False,
    ),
    TrappedClaim(
        claim_id="adv-011",
        text=(
            "The model converges under sparse "
            "supervision."
        ),
        trap=TrapKind.NORMAL.value,
        ambiguous=False,
    ),
    TrappedClaim(
        claim_id="adv-012",
        text=(
            "Recently, studies show many "
            "models often solve all problems."
        ),
        trap=(
            TrapKind.RHETORICAL_OVERREACH.value
        ),
        ambiguous=True,
    ),
)


def trapped_claims() -> tuple[
    TrappedClaim, ...,
]:
    return _FIXTURE


def trap_counts() -> dict[str, int]:
    from collections import Counter
    return dict(
        Counter(c.trap for c in trapped_claims())
    )


__all__ = [
    "TRAP_KINDS",
    "TrapKind",
    "TrappedClaim",
    "detect_trap",
    "trap_counts",
    "trapped_claims",
]
