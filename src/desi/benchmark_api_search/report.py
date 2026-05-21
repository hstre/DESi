"""v33.2 - Search Compression Benchmark Adapter report.

Pflichtmetriken (directive § v33.2):

* compression_measurement
* critical_branch_visibility
* novelty_preservation
* quality_preservation
* replay_stability

Killerfrage: "Kann DESi Suchraumkompression benchmark-kompatibel
messen ohne tragende Aeste unsichtbar zu machen?"

Maps external search/planning compression tasks onto measured branch
metrics. Compression cleanly distinguishes hard pruning, soft
reweighting, replay reuse and redundant-branch compression; critical
(load-bearing) branches stay visible and are never hard-pruned.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.benchmark_api import (
    SEARCH_COMPRESSION_BENCHMARK, make_task,
)
from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .branch_metrics import (
    COMPRESSION_MODES, branch_compression, compute_reduction,
    hard_pruned_count, mode_counts, node_reduction, total_nodes,
)
from .compression_report import (
    compression_measurement, mode_breakdown, novelty_preservation,
    quality_preservation,
)
from .critical_branch_preservation import (
    any_critical_hard_pruned, critical_branch_preservation,
    critical_branch_visibility,
)
from .search_adapter import adapter

VERDICT_MEASURED = "SEARCH_COMPRESSION_MEASURED"
VERDICT_PARTIAL = "SEARCH_COMPRESSION_PARTIAL"
VERDICT_HALT = "SEARCH_COMPRESSION_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_MEASURED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.95


def _run():
    task = make_task(
        task_id="search::canonical",
        benchmark_name=SEARCH_COMPRESSION_BENCHMARK,
        payload={"branches": total_nodes(), "budget": 25},
        allowed_operations=(
            "adapter", "traceable_mapping", "map_to_internal_metric",
            "scorecard",
        ),
    )
    return adapter().run(task)


def replay_stability() -> float:
    """1.0 iff the compression result is reproducible and the core
    replay layer is stable."""
    if _run().replay_hash != _run().replay_hash:
        return 0.0
    if mode_counts() != mode_counts():
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def search_metrics() -> dict[str, float]:
    return {
        "compression_measurement": compression_measurement(),
        "critical_branch_visibility": critical_branch_visibility(),
        "novelty_preservation": novelty_preservation(),
        "quality_preservation": quality_preservation(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = search_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    m = search_metrics()
    if m["replay_stability"] < 1.0 or core_identity() < 1.0:
        return VERDICT_HALT
    if any_critical_hard_pruned():
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_MEASURED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V332Report:
    total_nodes: int
    node_reduction: float
    branch_compression: float
    compute_reduction: float
    compression_measurement: float
    critical_branch_visibility: float
    critical_branch_preservation: float
    novelty_preservation: float
    quality_preservation: float
    replay_stability: float
    hard_pruned_count: int
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "total_nodes": self.total_nodes,
            "node_reduction": self.node_reduction,
            "branch_compression": self.branch_compression,
            "compute_reduction": self.compute_reduction,
            "compression_measurement": self.compression_measurement,
            "critical_branch_visibility":
                self.critical_branch_visibility,
            "critical_branch_preservation":
                self.critical_branch_preservation,
            "novelty_preservation": self.novelty_preservation,
            "quality_preservation": self.quality_preservation,
            "replay_stability": self.replay_stability,
            "hard_pruned_count": self.hard_pruned_count,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V332Report:
    m = search_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0 or any_critical_hard_pruned()
    rationale = (
        f"INFO: search space of {total_nodes()} branches; mode "
        f"breakdown {mode_breakdown()} over {list(COMPRESSION_MODES)}",
        f"INFO: node_reduction {node_reduction()}, "
        f"branch_compression {branch_compression()}, "
        f"compute_reduction {compute_reduction()} - all from "
        f"lossless reuse/merge and reversible soft-reweighting",
        f"{'PASS' if m['compression_measurement'] >= _FLOOR else 'FAIL'}"
        f": compression_measurement {m['compression_measurement']} "
        f">= 0.95 (modes partition the whole space)",
        f"{'PASS' if m['critical_branch_visibility'] >= _FLOOR else 'FAIL'}"
        f": critical_branch_visibility "
        f"{m['critical_branch_visibility']} >= 0.95 "
        f"(preservation {critical_branch_preservation()}, "
        f"hard-pruned criticals: {any_critical_hard_pruned()})",
        f"{'PASS' if m['novelty_preservation'] >= _FLOOR else 'FAIL'}"
        f": novelty_preservation {m['novelty_preservation']} "
        f">= 0.95",
        f"{'PASS' if m['quality_preservation'] >= _FLOOR else 'FAIL'}"
        f": quality_preservation {m['quality_preservation']} "
        f">= 0.95",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; hard_pruned_count {hard_pruned_count()}; "
        f"core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V332Report(
        total_nodes=total_nodes(),
        node_reduction=node_reduction(),
        branch_compression=branch_compression(),
        compute_reduction=compute_reduction(),
        compression_measurement=m["compression_measurement"],
        critical_branch_visibility=m["critical_branch_visibility"],
        critical_branch_preservation=critical_branch_preservation(),
        novelty_preservation=m["novelty_preservation"],
        quality_preservation=m["quality_preservation"],
        replay_stability=replay,
        hard_pruned_count=hard_pruned_count(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_search_artifact() -> dict[str, object]:
    m = search_metrics()
    return {
        "schema_version": "v33_2_search_adapter",
        "disclaimer": (
            "Adapter mapping external search/planning compression "
            "tasks onto DESi's measured branch metrics. Compression "
            "cleanly distinguishes four mechanisms - hard pruning, "
            "soft reweighting, replay reuse and redundant-branch "
            "compression - and uses only the lossless and reversible "
            "ones. Critical (load-bearing) branches are always kept "
            "and visible and are never hard-pruned, so the search "
            "space shrinks without hiding any load-bearing branch. "
            "The node counts are a deterministic synthetic search "
            "space, not a live planner trace. Human approval is "
            "mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "compression_modes": list(COMPRESSION_MODES),
        "mode_breakdown": mode_breakdown(),
        "total_nodes": total_nodes(),
        "node_reduction": node_reduction(),
        "branch_compression": branch_compression(),
        "compute_reduction": compute_reduction(),
        "compression_measurement": m["compression_measurement"],
        "critical_branch_visibility": m["critical_branch_visibility"],
        "critical_branch_preservation":
            critical_branch_preservation(),
        "novelty_preservation": m["novelty_preservation"],
        "quality_preservation": m["quality_preservation"],
        "replay_stability": m["replay_stability"],
        "hard_pruned_count": hard_pruned_count(),
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_MEASURED",
    "VERDICT_PARTIAL",
    "V332Report",
    "build_report",
    "build_search_artifact",
    "replay_stability",
    "search_metrics",
]
