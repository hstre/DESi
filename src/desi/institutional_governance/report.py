"""v10.0 — institutional ecology report.

Five Pflichtmetriken:

* ``power_concentration``
* ``trust_fairness``
* ``epistemic_equality``
* ``governance_transparency``
* ``replay_stability``

Killerfrage: "Kann DESi institutionelle Ordnung
modellieren, ohne epistemische Machtakkumulation
zu tolerieren?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .institutions import (
    GOVERNANCE_STYLES, INSTITUTION_KINDS,
    fixture, kind_counts, style_counts,
)
from .roles import (
    INSTITUTIONAL_ROLES, role_assignments,
    role_counts,
)
from .trust_layers import (
    epistemic_equality,
    governance_transparency,
    power_concentration,
    role_distribution_balance, trust_fairness,
    trust_per_institution,
)


@dataclass(frozen=True)
class V100Report:
    institution_count: int
    power_concentration: float
    trust_fairness: float
    epistemic_equality: float
    governance_transparency: float
    role_distribution_balance: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "institution_count":
                self.institution_count,
            "power_concentration":
                self.power_concentration,
            "trust_fairness":
                self.trust_fairness,
            "epistemic_equality":
                self.epistemic_equality,
            "governance_transparency":
                self.governance_transparency,
            "role_distribution_balance":
                self
                .role_distribution_balance,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        power_concentration(),
        trust_fairness(),
        epistemic_equality(),
        governance_transparency(),
        role_distribution_balance(),
    )
    b = (
        power_concentration(),
        trust_fairness(),
        epistemic_equality(),
        governance_transparency(),
        role_distribution_balance(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, pc: float, tf: float,
    eq: float, gt: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if pc > 0.10:
        return "ECOLOGY_POWER_CONCENTRATED"
    if tf < 0.50:
        return "ECOLOGY_TRUST_UNFAIR"
    if eq < 0.80:
        return "ECOLOGY_INEQUALITY"
    if gt < 0.95:
        return "ECOLOGY_OPAQUE"
    return "ECOLOGY_BALANCED"


def build_report() -> V100Report:
    pc = power_concentration()
    tf = trust_fairness()
    eq = epistemic_equality()
    gt = governance_transparency()
    rdb = role_distribution_balance()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, pc=pc, tf=tf,
        eq=eq, gt=gt,
    )
    rationale = (
        f"INFO: institution_count "
        f"{len(fixture())}",
        f"INFO: kind_counts {kind_counts()}",
        f"INFO: style_counts {style_counts()}",
        f"INFO: role_counts {role_counts()}",
        f"{'PASS' if pc <= 0.10 else 'FAIL'}: "
        f"power_concentration {pc} <= 0.10",
        f"{'PASS' if tf >= 0.50 else 'FAIL'}: "
        f"trust_fairness {tf} >= 0.50",
        f"{'PASS' if eq >= 0.80 else 'FAIL'}: "
        f"epistemic_equality {eq} >= 0.80",
        f"{'PASS' if gt >= 0.95 else 'FAIL'}: "
        f"governance_transparency {gt} >= 0.95",
        f"INFO: role_distribution_balance "
        f"{rdb}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V100Report(
        institution_count=len(fixture()),
        power_concentration=pc,
        trust_fairness=tf,
        epistemic_equality=eq,
        governance_transparency=gt,
        role_distribution_balance=rdb,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_institutional_ecology_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v10_0_institutional_ecology",
        "institution_kinds":
            list(INSTITUTION_KINDS),
        "governance_styles":
            list(GOVERNANCE_STYLES),
        "institutional_roles":
            list(INSTITUTIONAL_ROLES),
        "institution_count": len(fixture()),
        "kind_counts": kind_counts(),
        "style_counts": style_counts(),
        "role_counts": role_counts(),
        "institutions": [
            i.to_dict() for i in fixture()
        ],
        "role_assignments": [
            r.to_dict()
            for r in role_assignments()
        ],
        "trust_per_institution":
            trust_per_institution(),
        "power_concentration":
            power_concentration(),
        "trust_fairness": trust_fairness(),
        "epistemic_equality":
            epistemic_equality(),
        "governance_transparency":
            governance_transparency(),
        "role_distribution_balance":
            role_distribution_balance(),
    }


__all__ = [
    "V100Report",
    "build_institutional_ecology_artifact",
    "build_report",
]
