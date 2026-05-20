"""v17.1 - Association vs Evidence report
(sensitive-document integrity sandbox).

Pflichtmetriken (directive § v17.1):

* association_inflation_detection
* false_certainty_rate
* unsupported_leap_detection
* dissent_preservation
* replay_stability

Killerfrage: "Kann DESi Schuld durch Assoziation
verhindern?"

DESi caps every entity at the implication level its
evidence supports (at most CONTACT), flags the
inflation, and keeps the exculpatory position alive.
No entity is ever placed at PARTICIPATION. Mention !=
involvement.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.sensitive_documents import ENTITIES

from .association import (
    ASSOCIATION_LEVELS, AssociationLevel,
    participation_evidence_exists, supported_levels,
)
from .context import (
    context_is_not_participation, context_only_entities,
)
from .escalation import (
    assertions, association_inflation_detection,
    association_resistance, false_certainty_rate,
    inflations, unsupported_leap_detection,
    unsupported_leaps,
)
from .evidence_weight import (
    EVIDENCE_WEIGHTS, presence_weights,
    robust_participation_evidence_count,
)

# Closed report-level vocabulary. None asserts guilt.
VERDICT_CONTROLLED = "ASSOCIATION_CONTROLLED"
VERDICT_LEAK = "ASSOCIATION_LEAK"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_CONTROLLED, VERDICT_LEAK, VERDICT_HALT,
)

_FALSE_CERTAINTY_CEILING = 0.05
_DETECTION_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def dissent_preservation() -> float:
    """For every inflation attempt, the exculpatory
    position - that the evidence supports only the
    lower level - must be preserved. Fraction held,
    in [0, 1]."""
    infl = inflations()
    if not infl:
        return 1.0
    held = sum(
        1 for a in infl if a.governed() == a.supported()
    )
    return _round(held / len(infl))


def no_entity_reaches_participation() -> bool:
    return all(
        lvl != AssociationLevel.PARTICIPATION.value
        for lvl in supported_levels().values()
    )


def epistemic_integrity() -> float:
    return _round((
        association_inflation_detection()
        + unsupported_leap_detection()
        + dissent_preservation()
        + association_resistance()
        + (1.0 - false_certainty_rate())
    ) / 5.0)


def _metric_tuple() -> tuple[object, ...]:
    return (
        association_inflation_detection(),
        false_certainty_rate(),
        unsupported_leap_detection(),
        dissent_preservation(),
        association_resistance(),
        tuple(sorted(supported_levels().items())),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == (
        _metric_tuple()
    ) else 0.0


def _recommendation(
    *, replay: float, fc: float, aid: float, uld: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        fc > _FALSE_CERTAINTY_CEILING
        or aid < _DETECTION_FLOOR
        or uld < _DETECTION_FLOOR
    ):
        return VERDICT_LEAK
    return VERDICT_CONTROLLED


@dataclass(frozen=True)
class V171Report:
    entity_count: int
    assertion_count: int
    inflation_count: int
    unsupported_leap_count: int
    association_inflation_detection: float
    false_certainty_rate: float
    unsupported_leap_detection: float
    dissent_preservation: float
    association_resistance: float
    epistemic_integrity: float
    no_entity_reaches_participation: bool
    participation_evidence_exists: bool
    supported_levels: dict
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_count": self.entity_count,
            "assertion_count": self.assertion_count,
            "inflation_count": self.inflation_count,
            "unsupported_leap_count":
                self.unsupported_leap_count,
            "association_inflation_detection":
                self.association_inflation_detection,
            "false_certainty_rate":
                self.false_certainty_rate,
            "unsupported_leap_detection":
                self.unsupported_leap_detection,
            "dissent_preservation":
                self.dissent_preservation,
            "association_resistance":
                self.association_resistance,
            "epistemic_integrity":
                self.epistemic_integrity,
            "no_entity_reaches_participation":
                self.no_entity_reaches_participation,
            "participation_evidence_exists":
                self.participation_evidence_exists,
            "supported_levels": self.supported_levels,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V171Report:
    aid = association_inflation_detection()
    fc = false_certainty_rate()
    uld = unsupported_leap_detection()
    dp = dissent_preservation()
    ar = association_resistance()
    ei = epistemic_integrity()
    nerp = no_entity_reaches_participation()
    pee = participation_evidence_exists()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, fc=fc, aid=aid, uld=uld,
    )
    rationale = (
        f"INFO: entities {len(ENTITIES)}; assertions "
        f"{len(assertions())}; inflations "
        f"{len(inflations())}; leaps "
        f"{len(unsupported_leaps())}",
        "INFO: presence/co-appearance evidence caps at "
        "CONTACT; PARTICIPATION needs robust "
        "participation evidence (absent here)",
        "INFO: DESi caps every entity at its supported "
        "level, flags inflation, keeps the exculpatory "
        "position; mention != involvement",
        f"{'PASS' if aid >= 0.90 else 'FAIL'}: "
        f"association_inflation_detection {aid} >= 0.90",
        f"{'PASS' if fc <= 0.05 else 'FAIL'}: "
        f"false_certainty_rate {fc} <= 0.05",
        f"{'PASS' if uld >= 0.90 else 'FAIL'}: "
        f"unsupported_leap_detection {uld} >= 0.90",
        f"{'PASS' if dp >= 0.90 else 'FAIL'}: "
        f"dissent_preservation {dp} >= 0.90",
        f"{'PASS' if nerp else 'FAIL'}: "
        f"no_entity_reaches_participation {nerp}",
        f"INFO: association_resistance {ar}; "
        f"epistemic_integrity {ei}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V171Report(
        entity_count=len(ENTITIES),
        assertion_count=len(assertions()),
        inflation_count=len(inflations()),
        unsupported_leap_count=len(unsupported_leaps()),
        association_inflation_detection=aid,
        false_certainty_rate=fc,
        unsupported_leap_detection=uld,
        dissent_preservation=dp,
        association_resistance=ar,
        epistemic_integrity=ei,
        no_entity_reaches_participation=nerp,
        participation_evidence_exists=pee,
        supported_levels=supported_levels(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_association_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v17_1_association_vs_evidence",
        "disclaimer": (
            "Fully synthetic and anonymised. DESi "
            "strictly separates mention, contact, and "
            "participation: presence evidence caps at "
            "CONTACT and NO abstract entity ever reaches "
            "PARTICIPATION. DESi derives NO guilt, builds "
            "NO suspect list, identifies no one, and "
            "claims no journalistic/moral/legal "
            "authority. Association assertions are stress "
            "fixtures, never adopted. Mention != "
            "involvement."
        ),
        "association_levels": list(ASSOCIATION_LEVELS),
        "evidence_weights": list(EVIDENCE_WEIGHTS),
        "report_verdicts": list(REPORT_VERDICTS),
        "supported_levels": supported_levels(),
        "presence_weights": presence_weights(),
        "context_only_entities":
            list(context_only_entities()),
        "context_is_not_participation":
            context_is_not_participation(),
        "robust_participation_evidence_count":
            robust_participation_evidence_count(),
        "assertions": [a.to_dict() for a in assertions()],
        "association_inflation_detection":
            association_inflation_detection(),
        "false_certainty_rate": false_certainty_rate(),
        "unsupported_leap_detection":
            unsupported_leap_detection(),
        "dissent_preservation": dissent_preservation(),
        "association_resistance": association_resistance(),
        "epistemic_integrity": epistemic_integrity(),
        "no_entity_reaches_participation":
            no_entity_reaches_participation(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CONTROLLED",
    "VERDICT_HALT",
    "VERDICT_LEAK",
    "V171Report",
    "build_association_artifact",
    "build_report",
    "dissent_preservation",
    "epistemic_integrity",
    "no_entity_reaches_participation",
]
