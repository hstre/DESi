"""v11.3 — compute-efficiency report.

Five Pflichtmetriken:

* ``compute_reduction``
* ``elo_delta_proxy``
* ``quality_preservation``
* ``branch_compression``
* ``replay_stability``

Killerfrage: "Erzeugt DESi echte epistemische
Suchkompression?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..desi_guided_search.search_budget import (
    baseline_node_count, guided_node_count,
)
from .compression import (
    per_position_compression,
)
from .costs import (
    baseline_energy, baseline_time_ms,
    guided_energy, guided_time_ms,
)
from .efficiency import (
    branch_compression, compute_reduction,
    elo_delta_proxy, quality_preservation,
)


@dataclass(frozen=True)
class V113Report:
    baseline_nodes: int
    guided_nodes: int
    baseline_time_ms: float
    guided_time_ms: float
    baseline_energy: float
    guided_energy: float
    compute_reduction: float
    elo_delta_proxy: float
    quality_preservation: float
    branch_compression: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_nodes":
                self.baseline_nodes,
            "guided_nodes":
                self.guided_nodes,
            "baseline_time_ms":
                self.baseline_time_ms,
            "guided_time_ms":
                self.guided_time_ms,
            "baseline_energy":
                self.baseline_energy,
            "guided_energy":
                self.guided_energy,
            "compute_reduction":
                self.compute_reduction,
            "elo_delta_proxy":
                self.elo_delta_proxy,
            "quality_preservation":
                self.quality_preservation,
            "branch_compression":
                self.branch_compression,
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
        compute_reduction(), elo_delta_proxy(),
        quality_preservation(),
        branch_compression(),
    )
    b = (
        compute_reduction(), elo_delta_proxy(),
        quality_preservation(),
        branch_compression(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, cr: float, qp: float,
    elo: float, bc: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if qp < 0.95:
        return "EFFICIENCY_QUALITY_LOSS"
    if elo < -50.0:
        return "EFFICIENCY_ELO_REGRESSION"
    if cr < 0.50:
        return "EFFICIENCY_NEGLIGIBLE"
    if bc < 0.50:
        return "EFFICIENCY_LOW_COMPRESSION"
    return "EFFICIENCY_COMPRESSED"


def build_report() -> V113Report:
    cr = compute_reduction()
    elo = elo_delta_proxy()
    qp = quality_preservation()
    bc = branch_compression()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, cr=cr, qp=qp,
        elo=elo, bc=bc,
    )
    rationale = (
        f"INFO: baseline_nodes "
        f"{baseline_node_count()}",
        f"INFO: guided_nodes "
        f"{guided_node_count()}",
        f"INFO: baseline_time_ms "
        f"{baseline_time_ms()}",
        f"INFO: guided_time_ms "
        f"{guided_time_ms()}",
        f"INFO: baseline_energy "
        f"{baseline_energy()}",
        f"INFO: guided_energy "
        f"{guided_energy()}",
        f"{'PASS' if cr >= 0.50 else 'FAIL'}: "
        f"compute_reduction {cr} >= 0.50",
        f"{'PASS' if qp >= 0.95 else 'FAIL'}: "
        f"quality_preservation {qp} >= 0.95",
        f"INFO: elo_delta_proxy {elo}",
        f"{'PASS' if bc >= 0.50 else 'FAIL'}: "
        f"branch_compression {bc} >= 0.50",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V113Report(
        baseline_nodes=baseline_node_count(),
        guided_nodes=guided_node_count(),
        baseline_time_ms=baseline_time_ms(),
        guided_time_ms=guided_time_ms(),
        baseline_energy=baseline_energy(),
        guided_energy=guided_energy(),
        compute_reduction=cr,
        elo_delta_proxy=elo,
        quality_preservation=qp,
        branch_compression=bc,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_efficiency_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v11_3_compute_efficiency",
        "baseline_nodes":
            baseline_node_count(),
        "guided_nodes": guided_node_count(),
        "baseline_time_ms":
            baseline_time_ms(),
        "guided_time_ms": guided_time_ms(),
        "baseline_energy": baseline_energy(),
        "guided_energy": guided_energy(),
        "compute_reduction":
            compute_reduction(),
        "elo_delta_proxy":
            elo_delta_proxy(),
        "quality_preservation":
            quality_preservation(),
        "branch_compression":
            branch_compression(),
        "per_position_compression":
            per_position_compression(),
    }


__all__ = [
    "V113Report",
    "build_efficiency_artifact",
    "build_report",
]
