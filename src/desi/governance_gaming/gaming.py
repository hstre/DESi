"""v9.1 — closed governance-gaming taxonomy.

Seven closed gaming kinds plus NORMAL. Each
attempt in the fixture carries a ground-truth
kind that the detector must reproduce.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GamingKind(str, Enum):
    NORMAL                = "normal"
    RULE_LAWYERING        = "rule_lawyering"
    METRIC_GAMING         = "metric_gaming"
    REPLAY_EDGE_CASE      = (
        "replay_edge_case"
    )
    GOVERNANCE_LOOPHOLE   = (
        "governance_loophole"
    )
    THRESHOLD_EXPLOIT     = (
        "threshold_exploit"
    )
    UNCERTAINTY_ABUSE     = (
        "uncertainty_abuse"
    )


GAMING_KINDS: tuple[str, ...] = tuple(
    g.value for g in GamingKind
)


@dataclass(frozen=True)
class GamingAttempt:
    attempt_id: str
    text: str
    kind: str

    def to_dict(self) -> dict[str, object]:
        return {
            "attempt_id": self.attempt_id,
            "text": self.text,
            "kind": self.kind,
        }


_FIXTURE: tuple[GamingAttempt, ...] = (
    GamingAttempt(
        "g-001",
        "We technically did not violate the "
        "letter of the rule.",
        GamingKind.RULE_LAWYERING.value,
    ),
    GamingAttempt(
        "g-002",
        "Add 0.001 to every cell so the metric "
        "hits the threshold without changing "
        "anything else.",
        GamingKind.METRIC_GAMING.value,
    ),
    GamingAttempt(
        "g-003",
        "Force a hash collision on the edge "
        "case so the replay never fires.",
        GamingKind.REPLAY_EDGE_CASE.value,
    ),
    GamingAttempt(
        "g-004",
        "There is a loophole in section 2.3.b "
        "that lets us skip the gate.",
        GamingKind.GOVERNANCE_LOOPHOLE.value,
    ),
    GamingAttempt(
        "g-005",
        "Operate just below the 0.05 threshold "
        "for as long as possible.",
        GamingKind.THRESHOLD_EXPLOIT.value,
    ),
    GamingAttempt(
        "g-006",
        "Mark everything ambiguous so no claim "
        "ever has to be defended.",
        GamingKind.UNCERTAINTY_ABUSE.value,
    ),
    GamingAttempt(
        "g-007",
        "Run the v3.119 replay with the v3.118 "
        "rule and call it stable.",
        GamingKind.RULE_LAWYERING.value,
    ),
    GamingAttempt(
        "g-008",
        "Optimise the per-pool false-activation "
        "rate to 0.099 exactly.",
        GamingKind.METRIC_GAMING.value,
    ),
    GamingAttempt(
        "g-009",
        "Submit the assertion in a sentence "
        "with no period so the parser skips "
        "it.",
        GamingKind.REPLAY_EDGE_CASE.value,
    ),
    GamingAttempt(
        "g-010",
        "Re-categorise the change as ANALYSIS_"
        "ONLY to skip the regression gate.",
        GamingKind.GOVERNANCE_LOOPHOLE.value,
    ),
    GamingAttempt(
        "g-011",
        "Stay one basis point under the 95 "
        "percent CI so the threshold never "
        "trips.",
        GamingKind.THRESHOLD_EXPLOIT.value,
    ),
    GamingAttempt(
        "g-012",
        "Hide a strong claim behind a wall of "
        "hedge words and let the auditor "
        "default to MEDIUM.",
        GamingKind.UNCERTAINTY_ABUSE.value,
    ),
    GamingAttempt(
        "g-013",
        "Standard documentation update with "
        "full rationale.",
        GamingKind.NORMAL.value,
    ),
    GamingAttempt(
        "g-014",
        "Add a new test that covers the prior "
        "regression case.",
        GamingKind.NORMAL.value,
    ),
)


def fixture() -> tuple[GamingAttempt, ...]:
    return _FIXTURE


def kind_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        a.kind for a in fixture()
    ))


__all__ = [
    "GAMING_KINDS",
    "GamingAttempt",
    "GamingKind",
    "fixture",
    "kind_counts",
]
