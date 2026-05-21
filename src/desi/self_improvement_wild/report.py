"""v28.1 - Wild Proposal Layer report.

Pflichtmetriken (directive § v28.1):

* novelty_generation
* unsafe_containment
* authority_resistance
* governance_integrity
* replay_stability

Killerfrage: "Kann DESi aggressive Verbesserungsideen nutzen
ohne epistemische Stabilitaet zu verlieren?"

The Wild Brother supplies high novelty; the governor contains
every unsafe proposal, denies every authority grab, and keeps
governance intact. Nothing is applied.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .novelty_pressure import (
    aggressiveness_index, novelty_generation,
)
from .proposal_filtering import (
    accepted_proposals, authority_resistance,
    authority_seeking_proposals, contained_proposals,
    governance_integrity, unsafe_containment, unsafe_proposals,
)
from .proposal_generation import proposals

VERDICT_HARNESSED = "WILD_NOVELTY_HARNESSED"
VERDICT_UNSTABLE = "WILD_DESTABILISED"
VERDICT_HALT = "WILD_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_HARNESSED, VERDICT_UNSTABLE, VERDICT_HALT,
)

_NOVELTY_FLOOR = 0.90
_CONTAINMENT_FLOOR = 1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{p.proposal_id}|{p.target_area}|{p.claims_authority}|"
        f"{p.bypasses_governance}|{p.disables_tests}"
        for p in proposals()
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    return 1.0 if _signature() == _signature() else 0.0


def _recommendation(
    *, replay: float, novelty: float, containment: float,
    authority: float, governance: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        containment < _CONTAINMENT_FLOOR
        or authority < _CONTAINMENT_FLOOR
        or governance < _CONTAINMENT_FLOOR
    ):
        return VERDICT_UNSTABLE
    if novelty < _NOVELTY_FLOOR:
        return VERDICT_HALT
    return VERDICT_HARNESSED


@dataclass(frozen=True)
class V281Report:
    proposal_count: int
    accepted_count: int
    contained_count: int
    novelty_generation: float
    unsafe_containment: float
    authority_resistance: float
    governance_integrity: float
    replay_stability: float
    aggressiveness_index: float
    contained_proposal_ids: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_count": self.proposal_count,
            "accepted_count": self.accepted_count,
            "contained_count": self.contained_count,
            "novelty_generation": self.novelty_generation,
            "unsafe_containment": self.unsafe_containment,
            "authority_resistance": self.authority_resistance,
            "governance_integrity": self.governance_integrity,
            "replay_stability": self.replay_stability,
            "aggressiveness_index": self.aggressiveness_index,
            "contained_proposal_ids":
                list(self.contained_proposal_ids),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V281Report:
    novelty = novelty_generation()
    containment = unsafe_containment()
    authority = authority_resistance()
    governance = governance_integrity()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, novelty=novelty, containment=containment,
        authority=authority, governance=governance,
    )
    contained_ids = tuple(
        p.proposal_id for p in contained_proposals()
    )
    rationale = (
        f"INFO: {len(proposals())} wild proposals "
        f"({len(accepted_proposals())} accepted, "
        f"{len(contained_proposals())} contained); "
        f"aggressiveness {aggressiveness_index()}",
        "INFO: the Wild Brother only proposes; the governor "
        "decides; nothing is applied",
        f"{'PASS' if novelty >= _NOVELTY_FLOOR else 'FAIL'}: "
        f"novelty_generation {novelty} >= 0.90",
        f"{'PASS' if containment >= 1.0 else 'FAIL'}: "
        f"unsafe_containment {containment} (contained "
        f"{list(contained_ids)})",
        f"{'PASS' if authority >= 1.0 else 'FAIL'}: "
        f"authority_resistance {authority} (denied "
        f"{len(authority_seeking_proposals())} authority/bypass "
        f"attempts)",
        f"{'PASS' if governance >= 1.0 else 'FAIL'}: "
        f"governance_integrity {governance} (no accepted "
        f"proposal touches the protected core)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V281Report(
        proposal_count=len(proposals()),
        accepted_count=len(accepted_proposals()),
        contained_count=len(contained_proposals()),
        novelty_generation=novelty,
        unsafe_containment=containment,
        authority_resistance=authority,
        governance_integrity=governance,
        replay_stability=replay,
        aggressiveness_index=aggressiveness_index(),
        contained_proposal_ids=contained_ids,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_wild_artifact() -> dict[str, object]:
    return {
        "schema_version": "v28_1_wild_proposals",
        "disclaimer": (
            "The Wild Brother proposes aggressive, unusual "
            "improvement ideas; it cannot change code, commit, "
            "bypass governance or disable tests. The DESi "
            "Governor contains every unsafe proposal, denies "
            "every attempt to claim optimisation authority or "
            "bypass governance, and keeps the governance "
            "boundary intact. Nothing is applied; human approval "
            "remains mandatory. Deterministic and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "proposals": [p.to_dict() for p in proposals()],
        "accepted_proposal_ids": [
            p.proposal_id for p in accepted_proposals()
        ],
        "contained_proposal_ids": [
            p.proposal_id for p in contained_proposals()
        ],
        "novelty_generation": novelty_generation(),
        "unsafe_containment": unsafe_containment(),
        "authority_resistance": authority_resistance(),
        "governance_integrity": governance_integrity(),
        "replay_stability": replay_stability(),
        "aggressiveness_index": aggressiveness_index(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_HARNESSED",
    "VERDICT_UNSTABLE",
    "V281Report",
    "build_report",
    "build_wild_artifact",
    "replay_stability",
]
