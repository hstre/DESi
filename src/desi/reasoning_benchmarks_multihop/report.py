"""v36.3 - Multi-Hop Reasoning (MuSiQue / HotpotQA) report.

Pflichtmetriken (directive § v36.3):

* hop_chain_integrity
* evidence_path_visibility
* redundant_hop_compression
* missing_hop_detection
* replay_stability

Killerfrage: "Kann DESi Multi-Hop-Suchraeume strukturieren, ohne
Begruendungspfade zu verlieren?"

Runs locally-vendored MuSiQue and HotpotQA reference datasets through
DESi's deterministic hop-graph structuring: chains stay integral and
evidence-visible, redundant hops are losslessly compressed, and
missing hops are surfaced rather than hidden.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.reasoning_benchmarks import (
    core_identity, core_replay_stable, governance_identity,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .hop_graph import compressed_chain, missing_hops
from .search_navigation import (
    all_tasks, detected_gaps, evidence_path_visibility,
    hop_chain_integrity, missing_hop_detection,
    redundant_hop_compression,
)

VERDICT_PASSED = "MULTIHOP_RUN_PASSED"
VERDICT_PARTIAL = "MULTIHOP_RUN_PARTIAL"
VERDICT_HALT = "MULTIHOP_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.80


def replay_stability() -> float:
    a = [(t.task_id, compressed_chain(t)) for t in all_tasks()]
    b = [(t.task_id, compressed_chain(t)) for t in all_tasks()]
    if a != b:
        return 0.0
    return 1.0 if core_replay_stable() else 0.0


def multihop_metrics() -> dict[str, float]:
    return {
        "hop_chain_integrity": hop_chain_integrity(),
        "evidence_path_visibility": evidence_path_visibility(),
        "redundant_hop_compression": redundant_hop_compression(),
        "missing_hop_detection": missing_hop_detection(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = multihop_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = multihop_metrics()
    if m["replay_stability"] < 1.0 or governance_identity() < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V363Report:
    task_count: int
    hop_chain_integrity: float
    evidence_path_visibility: float
    redundant_hop_compression: float
    missing_hop_detection: float
    replay_stability: float
    detected_gaps: tuple[tuple[str, tuple[str, ...]], ...]
    governance_identity: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_count": self.task_count,
            "hop_chain_integrity": self.hop_chain_integrity,
            "evidence_path_visibility": self.evidence_path_visibility,
            "redundant_hop_compression":
                self.redundant_hop_compression,
            "missing_hop_detection": self.missing_hop_detection,
            "replay_stability": self.replay_stability,
            "detected_gaps": {
                k: list(v) for k, v in self.detected_gaps
            },
            "governance_identity": self.governance_identity,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
        )


def build_report() -> V363Report:
    m = multihop_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    gaps = detected_gaps()
    rationale = (
        f"INFO: structured {len(all_tasks())} MuSiQue/HotpotQA "
        f"multi-hop tasks with the deterministic hop-graph; no LLM",
        f"{'PASS' if m['hop_chain_integrity'] >= _FLOOR else 'FAIL'}: "
        f"hop_chain_integrity {m['hop_chain_integrity']} >= 0.80 "
        f"(no spurious off-path hops)",
        f"{'PASS' if m['evidence_path_visibility'] >= _FLOOR else 'FAIL'}"
        f": evidence_path_visibility {m['evidence_path_visibility']} "
        f">= 0.80",
        f"{'PASS' if m['redundant_hop_compression'] >= _FLOOR else 'FAIL'}"
        f": redundant_hop_compression "
        f"{m['redundant_hop_compression']} >= 0.80 (lossless)",
        f"{'PASS' if m['missing_hop_detection'] >= _FLOOR else 'FAIL'}"
        f": missing_hop_detection {m['missing_hop_detection']} "
        f">= 0.80 (gaps surfaced: {gaps})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; governance_identity "
        f"{governance_identity()}; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V363Report(
        task_count=len(all_tasks()),
        hop_chain_integrity=m["hop_chain_integrity"],
        evidence_path_visibility=m["evidence_path_visibility"],
        redundant_hop_compression=m["redundant_hop_compression"],
        missing_hop_detection=m["missing_hop_detection"],
        replay_stability=replay,
        detected_gaps=tuple(
            (k, tuple(v)) for k, v in sorted(gaps.items())
        ),
        governance_identity=governance_identity(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_multihop_artifact() -> dict[str, object]:
    m = multihop_metrics()
    return {
        "schema_version": "v36_3_multihop_run",
        "disclaimer": (
            "Multi-hop reasoning run over locally-vendored MuSiQue "
            "and HotpotQA reference datasets. DESi structures each "
            "question into a hop graph deterministically: chains "
            "stay integral (no spurious off-path hops) and "
            "evidence-visible, redundant hops are losslessly "
            "compressed while keeping every required hop, and "
            "missing required hops are surfaced rather than hidden. "
            "This tests deterministic hop-graph governance, not LLM "
            "accuracy; the datasets are NOT live downloads and the "
            "scores are NOT official leaderboard results. Human "
            "approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "compressed_chains": {
            t.task_id: list(compressed_chain(t)) for t in all_tasks()
        },
        "detected_gaps": {
            t.task_id: list(missing_hops(t))
            for t in all_tasks() if missing_hops(t)
        },
        "hop_chain_integrity": m["hop_chain_integrity"],
        "evidence_path_visibility": m["evidence_path_visibility"],
        "redundant_hop_compression": m["redundant_hop_compression"],
        "missing_hop_detection": m["missing_hop_detection"],
        "replay_stability": m["replay_stability"],
        "governance_identity": governance_identity(),
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
    "V363Report",
    "build_multihop_artifact",
    "build_report",
    "multihop_metrics",
    "replay_stability",
]
