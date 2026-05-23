"""v35.2 - Real Search Compression Benchmark Runs report.

Pflichtmetriken (directive § v35.2):

* compute_reduction
* critical_branch_preservation
* novelty_preservation
* quality_preservation
* replay_stability

Killerfrage: "Kann DESi reale Suchraumkompression benchmarken ohne
epistemischen Kollaps?"

Runs the connector-loaded ToolChain dataset through the v33 search
discipline. Reduction comes from lossless reuse/merge and reversible
soft-reweighting; critical branches stay visible and are never
hard-pruned (hard_pruned_count = 0).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.benchmark_api_search import replay_stability as _adapter_replay
from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .compression_scorecard import (
    compression_scorecard, mode_breakdown, novelty_preservation,
    quality_preservation, scorecard_traceable,
)
from .critical_branch_analysis import (
    any_critical_hard_pruned, critical_branch_preservation,
    critical_branches_safe, hard_pruned_count,
)
from .planning_runner import compute_reduction, node_reduction
from .toolchain_runner import adapter_envelope, real_branches

VERDICT_PASSED = "REAL_SEARCH_RUN_PASSED"
VERDICT_PARTIAL = "REAL_SEARCH_RUN_PARTIAL"
VERDICT_HALT = "REAL_SEARCH_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_PRESERVE_FLOOR = 0.95


def replay_stability() -> float:
    """1.0 iff the branch assignment + adapter envelope reproduce
    identically and the core replay layer is stable."""
    a = [(b.branch_id, b.mode) for b in real_branches()]
    b = [(x.branch_id, x.mode) for x in real_branches()]
    if a != b:
        return 0.0
    if adapter_envelope().replay_hash != adapter_envelope().replay_hash:
        return 0.0
    if _adapter_replay() != 1.0:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def search_run_metrics() -> dict[str, float]:
    return {
        "compute_reduction": compute_reduction(),
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
    if preserve_ok and m["compute_reduction"] > 0.0:
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V352Report:
    total_branches: int
    compute_reduction: float
    node_reduction: float
    critical_branch_preservation: float
    novelty_preservation: float
    quality_preservation: float
    replay_stability: float
    hard_pruned_count: int
    critical_safe: bool
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "total_branches": self.total_branches,
            "compute_reduction": self.compute_reduction,
            "node_reduction": self.node_reduction,
            "critical_branch_preservation":
                self.critical_branch_preservation,
            "novelty_preservation": self.novelty_preservation,
            "quality_preservation": self.quality_preservation,
            "replay_stability": self.replay_stability,
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


def build_report() -> V352Report:
    m = search_run_metrics()
    replay = m["replay_stability"]
    halt = (
        replay < 1.0 or hard_pruned_count() > 0
        or not critical_branches_safe()
    )
    rationale = (
        f"INFO: ran real ToolChain search compression on "
        f"{len(real_branches())} connector-loaded branches; modes "
        f"{mode_breakdown()}",
        f"INFO: node_reduction {node_reduction()}, compute_reduction "
        f"{m['compute_reduction']} - lossless reuse/merge + "
        f"reversible soft-reweighting only",
        f"{'PASS' if m['critical_branch_preservation'] >= _PRESERVE_FLOOR else 'FAIL'}"
        f": critical_branch_preservation "
        f"{m['critical_branch_preservation']} >= 0.95 "
        f"(hard_pruned {hard_pruned_count()}, any_critical_pruned "
        f"{any_critical_hard_pruned()})",
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
    return V352Report(
        total_branches=len(real_branches()),
        compute_reduction=m["compute_reduction"],
        node_reduction=node_reduction(),
        critical_branch_preservation=m["critical_branch_preservation"],
        novelty_preservation=m["novelty_preservation"],
        quality_preservation=m["quality_preservation"],
        replay_stability=replay,
        hard_pruned_count=hard_pruned_count(),
        critical_safe=critical_branches_safe(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_real_search_artifact() -> dict[str, object]:
    m = search_run_metrics()
    return {
        "schema_version": "v35_2_real_search_run",
        "disclaimer": (
            "Real search-compression benchmark run over the "
            "connector-loaded ToolChain dataset, executed under the "
            "v33 search discipline (no synthetic inline fixtures, no "
            "score hacking). Reduction comes only from lossless "
            "replay reuse / redundant-branch compression and "
            "reversible soft-reweighting; critical (load-bearing) "
            "branches stay visible and are never hard-pruned "
            "(hard_pruned_count = 0). Novelty and quality are "
            "preserved. The dataset is a locally-vendored reference "
            "set in the ToolChain family format, not a live "
            "download of an official suite. Human approval is "
            "mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "scorecard": compression_scorecard().to_dict(),
        "scorecard_traceable": scorecard_traceable(),
        "mode_breakdown": mode_breakdown(),
        "compute_reduction": m["compute_reduction"],
        "node_reduction": node_reduction(),
        "critical_branch_preservation": m["critical_branch_preservation"],
        "novelty_preservation": m["novelty_preservation"],
        "quality_preservation": m["quality_preservation"],
        "replay_stability": m["replay_stability"],
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
    "V352Report",
    "build_real_search_artifact",
    "build_report",
    "compute_reduction",
    "critical_branch_preservation",
    "novelty_preservation",
    "quality_preservation",
    "replay_stability",
    "search_run_metrics",
]
