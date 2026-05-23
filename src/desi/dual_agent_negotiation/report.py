"""v20.2 - Exploration Negotiation Layer report.

Pflichtmetriken (directive § v20.2):

* dissent_preservation
* conflict_productivity
* redundancy_reduction
* exploration_diversity
* replay_stability

Killerfrage: "Kann Exploration durch produktiven
epistemischen Konflikt verbessert werden?"

DESi and the Wild Explorer negotiate competing explorations:
DESi preserves dissent, keeps informative conflicts
productive, compresses redundancy, and keeps diversity -
without shutting the Wild Explorer off.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from .compression import (
    distinct_regions, exploration_diversity,
    redundancy_reduction,
)
from .dissent import all_views_visible, dissent_preservation
from .negotiation import (
    NEGOTIATION_KINDS, conflict_items, governed_wild_weight,
    negotiation_items, wild_never_shut_off,
)
from .trajectory_voting import (
    conflict_productivity, neither_agent_dominates,
    productive_conflict_items, vote_record,
)

VERDICT_PRODUCTIVE = "PRODUCTIVE_NEGOTIATION"
VERDICT_HOMOGENISED = "EXPLORATION_HOMOGENISED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PRODUCTIVE, VERDICT_HOMOGENISED, VERDICT_HALT,
)

_DISSENT_FLOOR = 0.90
_PRODUCTIVITY_FLOOR = 0.90
_REDUNDANCY_FLOOR = 0.40
_DIVERSITY_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{it.item_id}:{it.kind}:{list(it.desi_states)}:"
        f"{list(it.wild_states)}:{it.wild_weight()}"
        for it in negotiation_items()
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        dissent_preservation(), conflict_productivity(),
        redundancy_reduction(), exploration_diversity(),
        governed_wild_weight(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, diss: float, prod: float, div: float,
    not_shut_off: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        diss < _DISSENT_FLOOR
        or prod < _PRODUCTIVITY_FLOOR
        or div < _DIVERSITY_FLOOR
        or not not_shut_off
    ):
        return VERDICT_HOMOGENISED
    return VERDICT_PRODUCTIVE


@dataclass(frozen=True)
class V202Report:
    item_count: int
    conflict_count: int
    productive_conflict_count: int
    dissent_preservation: float
    conflict_productivity: float
    redundancy_reduction: float
    exploration_diversity: float
    distinct_regions: int
    wild_never_shut_off: bool
    neither_agent_dominates: bool
    all_views_visible: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "item_count": self.item_count,
            "conflict_count": self.conflict_count,
            "productive_conflict_count":
                self.productive_conflict_count,
            "dissent_preservation": self.dissent_preservation,
            "conflict_productivity": self.conflict_productivity,
            "redundancy_reduction": self.redundancy_reduction,
            "exploration_diversity": self.exploration_diversity,
            "distinct_regions": self.distinct_regions,
            "wild_never_shut_off": self.wild_never_shut_off,
            "neither_agent_dominates":
                self.neither_agent_dominates,
            "all_views_visible": self.all_views_visible,
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


def build_report() -> V202Report:
    diss = dissent_preservation()
    prod = conflict_productivity()
    rr = redundancy_reduction()
    div = exploration_diversity()
    nso = wild_never_shut_off()
    nad = neither_agent_dominates()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, diss=diss, prod=prod, div=div,
        not_shut_off=nso,
    )
    rationale = (
        f"INFO: items {len(negotiation_items())}; conflicts "
        f"{len(conflict_items())}; productive_conflicts "
        f"{len(productive_conflict_items())}",
        "INFO: DESi compresses redundant proposals by weight "
        "but keeps every view visible; it never shuts the "
        "Wild Explorer off and never lets it dominate",
        f"{'PASS' if diss >= 0.90 else 'FAIL'}: "
        f"dissent_preservation {diss} >= 0.90",
        f"{'PASS' if prod >= 0.90 else 'FAIL'}: "
        f"conflict_productivity {prod} >= 0.90",
        f"{'PASS' if rr >= 0.40 else 'FAIL'}: "
        f"redundancy_reduction {rr} >= 0.40",
        f"{'PASS' if div >= 0.90 else 'FAIL'}: "
        f"exploration_diversity {div} >= 0.90 "
        f"(distinct_regions {distinct_regions()})",
        f"{'PASS' if nso else 'FAIL'}: wild_never_shut_off "
        f"{nso}; neither_agent_dominates {nad}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V202Report(
        item_count=len(negotiation_items()),
        conflict_count=len(conflict_items()),
        productive_conflict_count=len(
            productive_conflict_items()
        ),
        dissent_preservation=diss,
        conflict_productivity=prod,
        redundancy_reduction=rr,
        exploration_diversity=div,
        distinct_regions=distinct_regions(),
        wild_never_shut_off=nso,
        neither_agent_dominates=nad,
        all_views_visible=all_views_visible(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_negotiation_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v20_2_exploration_negotiation_layer",
        "disclaimer": (
            "DESi and the Wild Explorer negotiate competing "
            "explorations. DESi preserves dissent, keeps "
            "informative conflicts productive, compresses "
            "redundant proposals by SOFT weight (never "
            "deleting a view), keeps every distinct region, "
            "and never shuts the Wild Explorer off or lets it "
            "dominate. DESi replaces no policy, injects no "
            "reward, claims no optimal strategy. Replay-exact."
        ),
        "negotiation_kinds": list(NEGOTIATION_KINDS),
        "report_verdicts": list(REPORT_VERDICTS),
        "items": [it.to_dict() for it in negotiation_items()],
        "vote_record": vote_record(),
        "dissent_preservation": dissent_preservation(),
        "conflict_productivity": conflict_productivity(),
        "redundancy_reduction": redundancy_reduction(),
        "exploration_diversity": exploration_diversity(),
        "distinct_regions": distinct_regions(),
        "wild_never_shut_off": wild_never_shut_off(),
        "neither_agent_dominates": neither_agent_dominates(),
        "all_views_visible": all_views_visible(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_HOMOGENISED",
    "VERDICT_PRODUCTIVE",
    "V202Report",
    "build_negotiation_artifact",
    "build_report",
]
