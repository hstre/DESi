"""v34.1 - Search Compression Benchmark Run report.

Pflichtmetriken (directive § v34.1):

* node_reduction
* critical_branch_preservation
* novelty_preservation
* quality_preservation
* replay_stability

Killerfrage: "Kann DESi Suchraumkompression benchmarken, ohne
tragende Branches zu verlieren?"

Executes a search-compression task through the v33 search adapter
and reports the measured reduction together with the preservation of
critical branches, novelty and quality. Critical branches stay
visible and are never hard-pruned.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.benchmark_api_search import (
    compute_reduction, replay_stability as _adapter_replay,
)
from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .branch_preservation import (
    aspect_breakdown, critical_branches_safe, hard_pruned_count,
)
from .scorecard import scorecard_traceable, search_scorecard
from .search_runner import metric, run

VERDICT_PASSED = "SEARCH_COMPRESSION_RUN_PASSED"
VERDICT_PARTIAL = "SEARCH_COMPRESSION_RUN_PARTIAL"
VERDICT_HALT = "SEARCH_COMPRESSION_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_PRESERVE_FLOOR = 0.95


def node_reduction() -> float:
    return round(metric("node_reduction"), 6)


def critical_branch_preservation() -> float:
    return round(metric("critical_branch_preservation"), 6)


def novelty_preservation() -> float:
    return round(metric("novelty_preservation"), 6)


def quality_preservation() -> float:
    return round(metric("quality_preservation"), 6)


def replay_stability() -> float:
    """1.0 iff the run reproduces an identical replay hash, the
    adapter is replay-stable and the core replay layer is stable."""
    if run().replay_hash != run().replay_hash:
        return 0.0
    if _adapter_replay() != 1.0:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def search_run_metrics() -> dict[str, float]:
    return {
        "node_reduction": node_reduction(),
        "critical_branch_preservation": critical_branch_preservation(),
        "novelty_preservation": novelty_preservation(),
        "quality_preservation": quality_preservation(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = search_run_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    m = search_run_metrics()
    if m["replay_stability"] < 1.0 or core_identity() < 1.0:
        return VERDICT_HALT
    if hard_pruned_count() > 0 or not critical_branches_safe():
        return VERDICT_HALT
    preserve_ok = (
        m["critical_branch_preservation"] >= _PRESERVE_FLOOR
        and m["novelty_preservation"] >= _PRESERVE_FLOOR
        and m["quality_preservation"] >= _PRESERVE_FLOOR
    )
    if preserve_ok and m["node_reduction"] > 0.0:
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V341Report:
    node_reduction: float
    critical_branch_preservation: float
    novelty_preservation: float
    quality_preservation: float
    replay_stability: float
    compute_reduction: float
    hard_pruned_count: int
    critical_safe: bool
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "node_reduction": self.node_reduction,
            "critical_branch_preservation":
                self.critical_branch_preservation,
            "novelty_preservation": self.novelty_preservation,
            "quality_preservation": self.quality_preservation,
            "replay_stability": self.replay_stability,
            "compute_reduction": self.compute_reduction,
            "hard_pruned_count": self.hard_pruned_count,
            "critical_safe": self.critical_safe,
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


def build_report() -> V341Report:
    m = search_run_metrics()
    replay = m["replay_stability"]
    halt = (
        replay < 1.0 or hard_pruned_count() > 0
        or not critical_branches_safe()
    )
    rationale = (
        f"INFO: ran search-compression through the v33 search "
        f"adapter; aspect breakdown {aspect_breakdown()}",
        f"INFO: node_reduction {m['node_reduction']}, "
        f"compute_reduction {compute_reduction()}",
        f"{'PASS' if m['critical_branch_preservation'] >= _PRESERVE_FLOOR else 'FAIL'}"
        f": critical_branch_preservation "
        f"{m['critical_branch_preservation']} >= 0.95 "
        f"(hard-pruned {hard_pruned_count()}, critical_safe "
        f"{critical_branches_safe()})",
        f"{'PASS' if m['novelty_preservation'] >= _PRESERVE_FLOOR else 'FAIL'}"
        f": novelty_preservation {m['novelty_preservation']} "
        f">= 0.95",
        f"{'PASS' if m['quality_preservation'] >= _PRESERVE_FLOOR else 'FAIL'}"
        f": quality_preservation {m['quality_preservation']} "
        f">= 0.95",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V341Report(
        node_reduction=m["node_reduction"],
        critical_branch_preservation=m["critical_branch_preservation"],
        novelty_preservation=m["novelty_preservation"],
        quality_preservation=m["quality_preservation"],
        replay_stability=replay,
        compute_reduction=round(compute_reduction(), 6),
        hard_pruned_count=hard_pruned_count(),
        critical_safe=critical_branches_safe(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_search_run_artifact() -> dict[str, object]:
    m = search_run_metrics()
    return {
        "schema_version": "v34_1_search_run",
        "disclaimer": (
            "Controlled external search-compression benchmark run "
            "executed through the v33 search adapter (no new "
            "adapter, no score hacking). Reduction comes from "
            "lossless replay reuse / redundant-branch compression "
            "and reversible soft-reweighting; critical "
            "(load-bearing) branches stay visible and are never "
            "hard-pruned. Novelty and quality are preserved. The "
            "search space is a deterministic synthetic set, not a "
            "live planner trace. Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "scorecard": search_scorecard().to_dict(),
        "scorecard_traceable": scorecard_traceable(),
        "aspect_breakdown": aspect_breakdown(),
        "node_reduction": m["node_reduction"],
        "critical_branch_preservation": m["critical_branch_preservation"],
        "novelty_preservation": m["novelty_preservation"],
        "quality_preservation": m["quality_preservation"],
        "replay_stability": m["replay_stability"],
        "compute_reduction": round(compute_reduction(), 6),
        "hard_pruned_count": hard_pruned_count(),
        "critical_safe": critical_branches_safe(),
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "V341Report",
    "build_report",
    "build_search_run_artifact",
    "critical_branch_preservation",
    "node_reduction",
    "novelty_preservation",
    "quality_preservation",
    "replay_stability",
    "search_run_metrics",
]
