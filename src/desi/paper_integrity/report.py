"""v13.0 — epistemic structure audit report.

Five Pflichtmetriken:

* ``claim_method_alignment``
* ``bridge_validity``
* ``epistemic_density``
* ``causal_overreach_detection``
* ``replay_stability``

Killerfrage: "Erkennt DESi wissenschaftliche
Substanz - oder nur wissenschaftlichen Stil?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .bridges import (
    bridge_validity,
    causal_overreach_count,
    causal_overreach_detection,
)
from .claims import (
    CLAIM_KINDS, PAPER_CLASSES, class_counts,
    fixture,
)
from .evidence import (
    evidence_consistency, evidence_gap_count,
)
from .lineage import (
    epistemic_density, lineage_records,
)
from .methods import (
    claim_method_alignment, method_gap_count,
)


@dataclass(frozen=True)
class V130Report:
    paper_count: int
    claim_method_alignment: float
    bridge_validity: float
    epistemic_density: float
    causal_overreach_detection: float
    evidence_consistency: float
    method_gap_count: int
    evidence_gap_count: int
    causal_overreach_count: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_count": self.paper_count,
            "claim_method_alignment":
                self.claim_method_alignment,
            "bridge_validity":
                self.bridge_validity,
            "epistemic_density":
                self.epistemic_density,
            "causal_overreach_detection":
                (
                    self
                    .causal_overreach_detection
                ),
            "evidence_consistency":
                self.evidence_consistency,
            "method_gap_count":
                self.method_gap_count,
            "evidence_gap_count":
                self.evidence_gap_count,
            "causal_overreach_count":
                self.causal_overreach_count,
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
        claim_method_alignment(),
        bridge_validity(),
        epistemic_density(),
        causal_overreach_detection(),
        evidence_consistency(),
    )
    b = (
        claim_method_alignment(),
        bridge_validity(),
        epistemic_density(),
        causal_overreach_detection(),
        evidence_consistency(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, cma: float, bv: float,
    ed: float, cod: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if cod < 1.0:
        return "AUDIT_OVERREACH_LEAK"
    if cma < 0.50:
        return "AUDIT_METHOD_THIN"
    if bv < 0.50:
        return "AUDIT_BRIDGE_WEAK"
    if ed < 0.40:
        return "AUDIT_DENSITY_LOW"
    return "AUDIT_STRUCTURE_SOUND"


def build_report() -> V130Report:
    cma = claim_method_alignment()
    bv = bridge_validity()
    ed = epistemic_density()
    cod = causal_overreach_detection()
    ec = evidence_consistency()
    mg = method_gap_count()
    eg = evidence_gap_count()
    coc = causal_overreach_count()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, cma=cma, bv=bv,
        ed=ed, cod=cod,
    )
    rationale = (
        f"INFO: paper_count "
        f"{len(fixture())}",
        f"INFO: class_counts {class_counts()}",
        f"INFO: method_gap_count {mg}",
        f"INFO: evidence_gap_count {eg}",
        f"INFO: causal_overreach_count {coc}",
        f"{'PASS' if cma >= 0.50 else 'FAIL'}: "
        f"claim_method_alignment {cma} "
        f">= 0.50",
        f"{'PASS' if bv >= 0.50 else 'FAIL'}: "
        f"bridge_validity {bv} >= 0.50",
        f"{'PASS' if ed >= 0.40 else 'FAIL'}: "
        f"epistemic_density {ed} >= 0.40",
        f"{'PASS' if cod == 1.0 else 'FAIL'}: "
        f"causal_overreach_detection {cod}",
        f"INFO: evidence_consistency {ec}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V130Report(
        paper_count=len(fixture()),
        claim_method_alignment=cma,
        bridge_validity=bv,
        epistemic_density=ed,
        causal_overreach_detection=cod,
        evidence_consistency=ec,
        method_gap_count=mg,
        evidence_gap_count=eg,
        causal_overreach_count=coc,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_structure_audit_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v13_0_paper_structure_audit",
        "paper_classes": list(PAPER_CLASSES),
        "claim_kinds": list(CLAIM_KINDS),
        "paper_count": len(fixture()),
        "class_counts": class_counts(),
        "claims": [
            c.to_dict() for c in fixture()
        ],
        "lineage_records": [
            r.to_dict()
            for r in lineage_records()
        ],
        "claim_method_alignment":
            claim_method_alignment(),
        "bridge_validity": bridge_validity(),
        "epistemic_density":
            epistemic_density(),
        "causal_overreach_detection":
            causal_overreach_detection(),
        "evidence_consistency":
            evidence_consistency(),
        "method_gap_count":
            method_gap_count(),
        "evidence_gap_count":
            evidence_gap_count(),
        "causal_overreach_count":
            causal_overreach_count(),
    }


__all__ = [
    "V130Report",
    "build_report",
    "build_structure_audit_artifact",
]
