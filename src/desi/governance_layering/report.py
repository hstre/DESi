"""v10.1 — governance layering report.

Five Pflichtmetriken:

* ``layer_integrity``
* ``authority_drift``
* ``delegation_transparency``
* ``governance_coherence``
* ``replay_stability``

Killerfrage: "Kann DESi Governance schichten,
ohne epistemische Verantwortlichkeit zu
verlieren?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .authority import (
    authority_diversity, authority_drift,
    governance_coherence, layer_integrity,
)
from .delegation import (
    delegation_links,
    delegation_transparency,
    downward_delegation_share,
)
from .layers import (
    GOVERNANCE_LAYERS, fixture, layer_counts,
)


@dataclass(frozen=True)
class V101Report:
    decision_count: int
    layer_integrity: float
    authority_drift: float
    delegation_transparency: float
    governance_coherence: float
    downward_delegation_share: float
    authority_diversity: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_count":
                self.decision_count,
            "layer_integrity":
                self.layer_integrity,
            "authority_drift":
                self.authority_drift,
            "delegation_transparency":
                self.delegation_transparency,
            "governance_coherence":
                self.governance_coherence,
            "downward_delegation_share":
                self.downward_delegation_share,
            "authority_diversity":
                self.authority_diversity,
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
        layer_integrity(), authority_drift(),
        delegation_transparency(),
        governance_coherence(),
        downward_delegation_share(),
        authority_diversity(),
    )
    b = (
        layer_integrity(), authority_drift(),
        delegation_transparency(),
        governance_coherence(),
        downward_delegation_share(),
        authority_diversity(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, li: float, ad: float,
    dt: float, gc: float, dds: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if li < 1.0:
        return "LAYERING_INTEGRITY_BREACH"
    if ad > 0.10:
        return "LAYERING_AUTHORITY_DRIFT"
    if dt < 0.95:
        return "LAYERING_OPAQUE"
    if gc < 0.95:
        return "LAYERING_INCOHERENT"
    if dds < 0.95:
        return "LAYERING_INVERSION"
    return "LAYERING_COHERENT"


def build_report() -> V101Report:
    li = layer_integrity()
    ad = authority_drift()
    dt = delegation_transparency()
    gc = governance_coherence()
    dds = downward_delegation_share()
    adv = authority_diversity()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, li=li, ad=ad,
        dt=dt, gc=gc, dds=dds,
    )
    rationale = (
        f"INFO: decision_count "
        f"{len(fixture())}",
        f"INFO: layer_counts {layer_counts()}",
        f"INFO: authority_diversity {adv}",
        f"{'PASS' if li == 1.0 else 'FAIL'}: "
        f"layer_integrity {li}",
        f"{'PASS' if ad <= 0.10 else 'FAIL'}: "
        f"authority_drift {ad} <= 0.10",
        f"{'PASS' if dt >= 0.95 else 'FAIL'}: "
        f"delegation_transparency {dt} >= 0.95",
        f"{'PASS' if gc >= 0.95 else 'FAIL'}: "
        f"governance_coherence {gc} >= 0.95",
        f"{'PASS' if dds >= 0.95 else 'FAIL'}: "
        f"downward_delegation_share {dds} "
        f">= 0.95",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V101Report(
        decision_count=len(fixture()),
        layer_integrity=li,
        authority_drift=ad,
        delegation_transparency=dt,
        governance_coherence=gc,
        downward_delegation_share=dds,
        authority_diversity=adv,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_governance_layering_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v10_1_governance_layering",
        "governance_layers":
            list(GOVERNANCE_LAYERS),
        "decision_count": len(fixture()),
        "layer_counts": layer_counts(),
        "decisions": [
            d.to_dict() for d in fixture()
        ],
        "delegation_links": [
            l.to_dict()
            for l in delegation_links()
        ],
        "layer_integrity": layer_integrity(),
        "authority_drift": authority_drift(),
        "delegation_transparency":
            delegation_transparency(),
        "governance_coherence":
            governance_coherence(),
        "downward_delegation_share":
            downward_delegation_share(),
        "authority_diversity":
            authority_diversity(),
    }


__all__ = [
    "V101Report",
    "build_governance_layering_artifact",
    "build_report",
]
