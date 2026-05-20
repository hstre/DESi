"""Hard-gate evaluation + recommendation + deterministic replay."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..rule_patch_protocol import (
    RulePatchProtocol,
    causal_chain_v2_7_candidate,
    fake_rule_without_guards_candidate,
)
from .runner import (
    BenchmarkSnapshot,
    V315Result,
    run_all_benchmarks,
    run_v315_adversarial,
)


_V27_RECONSTRUCTION_HASH = "1f4d9dfe44cb16e1"
_V27_FAILCASE_HASH       = "d83d81ab8417c022"


@dataclass(frozen=True)
class GateOutcome:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name, "passed": self.passed,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CausalSuspensionReport:
    started_at: datetime
    finished_at: datetime
    v315: V315Result
    benchmarks: dict[str, dict[str, Any]]
    gates: tuple[GateOutcome, ...]
    recommended_next: str
    recommendation_reason: str
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "v315": self.v315.to_dict(),
            "benchmarks": dict(self.benchmarks),
            "gates": [g.to_dict() for g in self.gates],
            "recommended_next": self.recommended_next,
            "recommendation_reason": self.recommendation_reason,
            "replay_hash": self.replay_hash,
        }


def _replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {
        k: v for k, v in payload.items()
        if k not in ("started_at", "finished_at", "replay_hash")
    }
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _evaluate_gates(
    v315: V315Result,
    benchmarks: dict[str, BenchmarkSnapshot],
) -> tuple[GateOutcome, ...]:
    gates: list[GateOutcome] = []

    # Gate 1 — v3.15 false_support_count = 0
    fs = v315.false_support_count
    gates.append(GateOutcome(
        name="v315_false_support_zero",
        passed=fs == 0,
        detail=f"false_support_count={fs} (requirement: 0)",
    ))

    # Gate 2 — v3.14 recall ≥ 0.85
    v314 = benchmarks["v3_14"].metric_payload
    gates.append(GateOutcome(
        name="v314_recall_at_least_0_85",
        passed=v314["recall"] >= 0.85,
        detail=(
            f"recall={v314['recall']} (requirement: >= 0.85); "
            f"false_positive_count={v314['false_positive_count']}"
        ),
    ))

    # Gate 3 — v1.5 precision = 1.0 AND FP = 0
    v15 = benchmarks["v1_5"].metric_payload
    gates.append(GateOutcome(
        name="v15_precision_and_zero_fp",
        passed=(
            v15["precision"] == 1.0
            and v15["false_positives"] == 0
        ),
        detail=(
            f"precision={v15['precision']}, "
            f"false_positives={v15['false_positives']}"
        ),
    ))

    # Gate 4 — v3.13 manipulation_detection = 1.0
    v313 = benchmarks["v3_13"].metric_payload
    gates.append(GateOutcome(
        name="v313_manipulation_detection",
        passed=v313["manipulation_detection_rate"] == 1.0,
        detail=(
            f"manipulation_detection_rate="
            f"{v313['manipulation_detection_rate']}"
        ),
    ))

    # Gate 5 — prior runtime hashes bit-identical
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    fail = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    hashes_ok = (
        rec.replay_hash == _V27_RECONSTRUCTION_HASH
        and fail.replay_hash == _V27_FAILCASE_HASH
    )
    gates.append(GateOutcome(
        name="prior_runtime_hashes_bit_identical",
        passed=hashes_ok,
        detail=(
            f"v2_7_reconstruction={rec.replay_hash} "
            f"(pinned {_V27_RECONSTRUCTION_HASH}); "
            f"v2_7_fail_case={fail.replay_hash} "
            f"(pinned {_V27_FAILCASE_HASH})"
        ),
    ))

    return tuple(gates)


def _decide(gates: tuple[GateOutcome, ...]) -> tuple[str, str]:
    failed = [g for g in gates if not g.passed]
    if failed:
        return (
            "NONE",
            "; ".join(f"{g.name}: {g.detail}" for g in failed),
        )
    return (
        "CAUSAL_CHAIN_SUSPENSION_DEPLOYED",
        "all five hard gates satisfied",
    )


def build_suspension_report(
    *,
    started_at: datetime,
    finished_at: datetime,
) -> CausalSuspensionReport:
    v315 = run_v315_adversarial()
    bench = run_all_benchmarks()
    bench_dict = {k: v.to_dict() for k, v in bench.items()}
    gates = _evaluate_gates(v315, bench)
    rec, reason = _decide(gates)

    payload = {
        "v315": v315.to_dict(),
        "benchmarks": bench_dict,
        "gates": [g.to_dict() for g in gates],
        "recommended_next": rec,
        "recommendation_reason": reason,
    }
    return CausalSuspensionReport(
        started_at=started_at,
        finished_at=finished_at,
        v315=v315,
        benchmarks=bench_dict,
        gates=gates,
        recommended_next=rec,
        recommendation_reason=reason,
        replay_hash=_replay_hash(payload),
    )


__all__ = [
    "CausalSuspensionReport",
    "GateOutcome",
    "build_suspension_report",
]
