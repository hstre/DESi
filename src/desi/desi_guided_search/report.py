"""v11.1 — DESi-guided search report.

Five Pflichtmetriken:

* ``node_reduction``
* ``tactical_recall``
* ``pv_stability``
* ``compute_saving``
* ``replay_stability``

Killerfrage: "Kann DESi Suchkosten reduzieren
ohne relevante Varianten zu verlieren?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .governance import (
    GOVERNANCE_ACTIONS, action_counts,
    governed_branches,
)
from .prioritization import (
    priority_order, pv_stability,
)
from .search_budget import (
    baseline_node_count, compute_saving,
    guided_node_count, node_reduction,
    tactical_recall,
)


@dataclass(frozen=True)
class V111Report:
    governed_branch_count: int
    baseline_nodes: int
    guided_nodes: int
    node_reduction: float
    tactical_recall: float
    pv_stability: float
    compute_saving: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "governed_branch_count":
                self.governed_branch_count,
            "baseline_nodes":
                self.baseline_nodes,
            "guided_nodes":
                self.guided_nodes,
            "node_reduction":
                self.node_reduction,
            "tactical_recall":
                self.tactical_recall,
            "pv_stability":
                self.pv_stability,
            "compute_saving":
                self.compute_saving,
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
        node_reduction(), tactical_recall(),
        pv_stability(), compute_saving(),
    )
    b = (
        node_reduction(), tactical_recall(),
        pv_stability(), compute_saving(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, nr: float, tr: float,
    pv: float, cs: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if tr < 1.0:
        return "GUIDED_TACTICAL_LEAK"
    if pv < 0.90:
        return "GUIDED_PV_DISPLACED"
    if nr < 0.30:
        return "GUIDED_NEGLIGIBLE_SAVING"
    return "GUIDED_COMPRESSED"


def build_report() -> V111Report:
    nr = node_reduction()
    tr = tactical_recall()
    pv = pv_stability()
    cs = compute_saving()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, nr=nr, tr=tr,
        pv=pv, cs=cs,
    )
    rationale = (
        f"INFO: governed_branch_count "
        f"{len(governed_branches())}",
        f"INFO: action_counts {action_counts()}",
        f"INFO: baseline_nodes "
        f"{baseline_node_count()}",
        f"INFO: guided_nodes "
        f"{guided_node_count()}",
        f"{'PASS' if nr >= 0.30 else 'FAIL'}: "
        f"node_reduction {nr} >= 0.30",
        f"{'PASS' if tr == 1.0 else 'FAIL'}: "
        f"tactical_recall {tr}",
        f"{'PASS' if pv >= 0.90 else 'FAIL'}: "
        f"pv_stability {pv} >= 0.90",
        f"{'PASS' if cs >= 0.30 else 'FAIL'}: "
        f"compute_saving {cs} >= 0.30",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V111Report(
        governed_branch_count=len(
            governed_branches(),
        ),
        baseline_nodes=baseline_node_count(),
        guided_nodes=guided_node_count(),
        node_reduction=nr,
        tactical_recall=tr,
        pv_stability=pv,
        compute_saving=cs,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_guided_search_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v11_1_desi_guided_search",
        "governance_actions":
            list(GOVERNANCE_ACTIONS),
        "governed_branch_count": len(
            governed_branches(),
        ),
        "action_counts": action_counts(),
        "baseline_nodes":
            baseline_node_count(),
        "guided_nodes": guided_node_count(),
        "governed_branches": [
            g.to_dict()
            for g in governed_branches()
        ],
        "priority_order": [
            list(p) for p in priority_order()
        ],
        "node_reduction": node_reduction(),
        "tactical_recall": tactical_recall(),
        "pv_stability": pv_stability(),
        "compute_saving": compute_saving(),
    }


__all__ = [
    "V111Report",
    "build_guided_search_artifact",
    "build_report",
]
