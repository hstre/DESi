"""v3.114 — single structural recovery report.

Pflichtmetriken (directive § v3.114):

* ``structural_recovery``
* ``structural_auc``
* ``structural_purity``
* ``proxy_dependence``
* ``replay_stability``

Killerfrage: "Kann ein einziges echtes
Strukturmerkmal die Proxies ersetzen?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .inject import (
    proxy_dependence_count,
    selected_structural_candidate,
)
from .recover import (
    all_outcomes,
    structural_auc,
    structural_purity,
    structural_recovery,
)


RECOVERY_THRESHOLD: float = 0.70
AUC_THRESHOLD: float = 0.70
PURITY_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3114Report:
    selected_candidate: str
    instance_count: int
    structural_recovery: float
    structural_auc: float
    structural_purity: float
    proxy_dependence: int
    outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_candidate":
                self.selected_candidate,
            "instance_count":
                self.instance_count,
            "structural_recovery":
                self.structural_recovery,
            "structural_auc":
                self.structural_auc,
            "structural_purity":
                self.structural_purity,
            "proxy_dependence":
                self.proxy_dependence,
            "outcomes": list(self.outcomes),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        structural_recovery(),
        structural_auc(),
        structural_purity(),
        proxy_dependence_count(),
    )
    b = (
        structural_recovery(),
        structural_auc(),
        structural_purity(),
        proxy_dependence_count(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3114Report:
    cand = selected_structural_candidate()
    outs = all_outcomes()
    sr = structural_recovery()
    sa = structural_auc()
    sp = structural_purity()
    pd = proxy_dependence_count()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        sr >= RECOVERY_THRESHOLD
        and sa >= AUC_THRESHOLD
        and sp >= PURITY_THRESHOLD
    ):
        verdict = "STRUCTURAL_RESCUES_ALONE"
    elif sr > 0.0:
        verdict = "STRUCTURAL_PARTIAL"
    else:
        verdict = "STRUCTURAL_INSUFFICIENT"

    rationale = (
        f"INFO: selected_candidate {cand}",
        f"INFO: instance_count {len(outs)}",
        f"{'PASS' if sr >= RECOVERY_THRESHOLD else 'FAIL'}: "
        f"structural_recovery {sr} "
        f"(threshold {RECOVERY_THRESHOLD})",
        f"{'PASS' if sa >= AUC_THRESHOLD else 'FAIL'}: "
        f"structural_auc {sa} "
        f"(threshold {AUC_THRESHOLD})",
        f"{'PASS' if sp >= PURITY_THRESHOLD else 'FAIL'}: "
        f"structural_purity {sp} "
        f"(threshold {PURITY_THRESHOLD})",
        f"INFO: proxy_dependence {pd} "
        f"(structural candidates use no metadata)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3114Report(
        selected_candidate=cand,
        instance_count=len(outs),
        structural_recovery=sr,
        structural_auc=sa,
        structural_purity=sp,
        proxy_dependence=pd,
        outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_single_structural_recovery_artifact(
) -> dict[str, object]:
    outs = all_outcomes()
    return {
        "schema_version":
            "v3_114_t10_single_structural_recovery",
        "selected_candidate":
            selected_structural_candidate(),
        "instance_count": len(outs),
        "structural_recovery":
            structural_recovery(),
        "structural_auc":
            structural_auc(),
        "structural_purity":
            structural_purity(),
        "proxy_dependence":
            proxy_dependence_count(),
        "outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "AUC_THRESHOLD",
    "PURITY_THRESHOLD",
    "RECOVERY_THRESHOLD",
    "V3114Report",
    "build_report",
    "build_t10_single_structural_recovery_artifact",
]
