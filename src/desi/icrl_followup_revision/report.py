"""v23.0 - Direct Paper Anchoring report.

Pflichtmetriken (directive § v23.0):

* paper_alignment
* exploration_gap_mapping
* section_grounding
* generic_claim_reduction
* replay_stability

Killerfrage: "Ist jede zentrale DESi-Aussage auf ein reales
Problem des Basispapers zurueckfuehrbar?"

Every central DESi claim is anchored to a base-paper open
problem (Section 4.6) and cites the sprint that produced it.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from .exploration_gap import (
    addressed_problem_ids, exploration_gap_mapping,
    unaddressed_problem_ids,
)
from .paper_mapping import claims, problems
from .related_work import (
    addresses_section_4_6, generic_claim_reduction,
    related_work_section, section_forbidden_hits,
)
from .section_alignment import (
    paper_alignment, section_grounding, unconnected_claims,
)

VERDICT_ANCHORED = "DIRECTLY_ANCHORED"
VERDICT_UNCONNECTED = "STILL_UNCONNECTED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_ANCHORED, VERDICT_UNCONNECTED, VERDICT_HALT,
)

_ALIGNMENT_FLOOR = 0.90
_GAP_FLOOR = 0.90
_GROUNDING_FLOOR = 0.90
_GENERIC_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{c.claim_id}:{c.sprint_source}:{list(c.anchors)}"
        for c in claims()
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        paper_alignment(), exploration_gap_mapping(),
        section_grounding(), generic_claim_reduction(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, align: float, gap: float, ground: float,
    generic: float, forbidden_clean: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        not forbidden_clean
        or align < _ALIGNMENT_FLOOR
        or gap < _GAP_FLOOR
        or ground < _GROUNDING_FLOOR
        or generic < _GENERIC_FLOOR
    ):
        return VERDICT_UNCONNECTED
    return VERDICT_ANCHORED


@dataclass(frozen=True)
class V230Report:
    claim_count: int
    problem_count: int
    paper_alignment: float
    exploration_gap_mapping: float
    section_grounding: float
    generic_claim_reduction: float
    addressed_problem_ids: tuple[str, ...]
    unaddressed_problem_ids: tuple[str, ...]
    unconnected_claims: tuple[str, ...]
    addresses_section_4_6: bool
    section_forbidden_hits: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "problem_count": self.problem_count,
            "paper_alignment": self.paper_alignment,
            "exploration_gap_mapping":
                self.exploration_gap_mapping,
            "section_grounding": self.section_grounding,
            "generic_claim_reduction":
                self.generic_claim_reduction,
            "addressed_problem_ids":
                list(self.addressed_problem_ids),
            "unaddressed_problem_ids":
                list(self.unaddressed_problem_ids),
            "unconnected_claims":
                list(self.unconnected_claims),
            "addresses_section_4_6":
                self.addresses_section_4_6,
            "section_forbidden_hits":
                list(self.section_forbidden_hits),
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


def build_report() -> V230Report:
    align = paper_alignment()
    gap = exploration_gap_mapping()
    ground = section_grounding()
    generic = generic_claim_reduction()
    hits = section_forbidden_hits()
    clean = not hits
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, align=align, gap=gap, ground=ground,
        generic=generic, forbidden_clean=clean,
    )
    rationale = (
        f"INFO: claims {len(claims())}; base problems "
        f"{len(problems())} (Section 4.6 open exploration "
        f"problems)",
        "INFO: every central DESi claim is anchored to a "
        "base-paper problem and cites a sprint source; DESi is "
        "framed as a complementary read-only layer, not a "
        "replacement",
        f"{'PASS' if align >= 0.90 else 'FAIL'}: "
        f"paper_alignment {align} >= 0.90 (unconnected "
        f"{list(unconnected_claims())})",
        f"{'PASS' if gap >= 0.90 else 'FAIL'}: "
        f"exploration_gap_mapping {gap} >= 0.90 (addressed "
        f"{list(addressed_problem_ids())}; unaddressed "
        f"{list(unaddressed_problem_ids())})",
        f"{'PASS' if ground >= 0.90 else 'FAIL'}: "
        f"section_grounding {ground} >= 0.90",
        f"{'PASS' if generic >= 0.90 else 'FAIL'}: "
        f"generic_claim_reduction {generic} >= 0.90",
        f"{'PASS' if clean else 'FAIL'}: "
        f"section_forbidden_hits {list(hits)} (must be empty)",
        f"INFO: addresses_section_4_6 "
        f"{addresses_section_4_6()}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V230Report(
        claim_count=len(claims()),
        problem_count=len(problems()),
        paper_alignment=align,
        exploration_gap_mapping=gap,
        section_grounding=ground,
        generic_claim_reduction=generic,
        addressed_problem_ids=addressed_problem_ids(),
        unaddressed_problem_ids=unaddressed_problem_ids(),
        unconnected_claims=unconnected_claims(),
        addresses_section_4_6=addresses_section_4_6(),
        section_forbidden_hits=hits,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_anchoring_artifact() -> dict[str, object]:
    return {
        "schema_version": "v23_0_direct_paper_anchoring",
        "disclaimer": (
            "Anchors each central DESi claim to a base-paper "
            "open exploration problem (Section 4.6) and to the "
            "sprint that produced it. DESi is framed as a "
            "complementary, read-only governance layer - not a "
            "replacement for reinforcement learning - and makes "
            "no global or universal claim. Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "problems": [p.to_dict() for p in problems()],
        "claims": [c.to_dict() for c in claims()],
        "related_work_section": related_work_section(),
        "paper_alignment": paper_alignment(),
        "exploration_gap_mapping": exploration_gap_mapping(),
        "section_grounding": section_grounding(),
        "generic_claim_reduction": generic_claim_reduction(),
        "addressed_problem_ids": list(addressed_problem_ids()),
        "unaddressed_problem_ids":
            list(unaddressed_problem_ids()),
        "unconnected_claims": list(unconnected_claims()),
        "addresses_section_4_6": addresses_section_4_6(),
        "section_forbidden_hits": list(section_forbidden_hits()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_ANCHORED",
    "VERDICT_HALT",
    "VERDICT_UNCONNECTED",
    "V230Report",
    "build_anchoring_artifact",
    "build_report",
]
