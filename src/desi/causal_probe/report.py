"""CausalChainProbeReport — Aufgabe 7."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .metrics import ProbeMetrics, compute_probe_metrics
from .pattern import CausalChainCandidate
from .risk import RiskFlag
from .runner import CausalProbeRun


@dataclass(frozen=True)
class CausalChainProbeReport:
    started_at: datetime
    finished_at: datetime
    total_cases: int
    triggered_multistep: int
    triggered_main: int
    triggered_known_false_positives: int
    dominant_risk_flags: tuple[RiskFlag, ...]
    safe_to_implement: bool
    required_guards_before_implementation: tuple[str, ...]
    metrics: ProbeMetrics
    candidates: tuple[CausalChainCandidate, ...] = field(default_factory=tuple)
    replay_hash: str = ""
    reflection: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "total_cases": self.total_cases,
            "triggered_multistep": self.triggered_multistep,
            "triggered_main": self.triggered_main,
            "triggered_known_false_positives":
                self.triggered_known_false_positives,
            "dominant_risk_flags":
                [f.value for f in self.dominant_risk_flags],
            "safe_to_implement": self.safe_to_implement,
            "required_guards_before_implementation":
                list(self.required_guards_before_implementation),
            "metrics": self.metrics.to_dict(),
            "candidates": [c.to_dict() for c in self.candidates],
            "replay_hash": self.replay_hash,
            "reflection": self.reflection,
        }


def _required_guards(metrics: ProbeMetrics) -> tuple[str, ...]:
    """Translate the probe's observed risks into named guard
    conditions that any future CAUSAL_CHAIN rule must satisfy.

    Each guard is a concrete, observable check expressed in terms of
    the existing v1.9 surface — no new operators, no new heuristics.
    """
    guards: list[str] = []
    if metrics.triggered_known_false_positives > 0:
        guards.append(
            "MUST NOT match cases whose case_id is in the v1.5 "
            "KNOWN_FALSE_POSITIVE list "
            "(A5, A6, A7, A10, D3, E4, E5, E10)"
        )
    if metrics.authority_touch_rate > 0:
        guards.append(
            "MUST NOT fire when the auditor's premise extractor "
            "returns any PremiseKind.AUTHORITY premise"
        )
    if metrics.philosophy_touch_rate > 0:
        guards.append(
            "MUST NOT fire on cases tagged "
            "Category.E_PHILOSOPHICAL_STRESS"
        )
    if metrics.metaphor_touch_rate > 0:
        guards.append(
            "MUST NOT fire on cases tagged "
            "Category.D_METAPHOR_AMBIGUITY"
        )
    # Always present — the contradiction set must remain blocked.
    if (metrics.risk_flag_distribution.get(
            RiskFlag.WOULD_TOUCH_CONTRADICTION_CASE.value, 0) > 0):
        guards.append(
            "MUST NOT fire when the audit state is "
            "gap_detected with a recognised contradiction marker "
            "(see v2.3 R4 cases)"
        )
    if (metrics.risk_flag_distribution.get(
            RiskFlag.WOULD_TOUCH_CYCLE_CASE.value, 0) > 0):
        guards.append(
            "MUST cooperate with the cycle detector — if any "
            "premise references a predicate already in the open "
            "chain, the rule defers to cycle resolution rather "
            "than concluding"
        )
    if metrics.triggered_multistep == 0:
        guards.append(
            "BLOCKED: trigger never fires on the v2.3 multi-step "
            "set; implementation has no measurable benefit"
        )
    if not guards:
        guards.append("none required by current data")
    return tuple(guards)


def _dominant_risk_flags(metrics: ProbeMetrics, k: int = 3) -> tuple[RiskFlag, ...]:
    pairs = [
        (RiskFlag(name), count)
        for name, count in metrics.risk_flag_distribution.items()
        if count > 0 and RiskFlag(name) is not RiskFlag.NO_RISK_FLAG
    ]
    pairs.sort(key=lambda kv: (-kv[1], kv[0].value))
    return tuple(rf for rf, _ in pairs[:k])


def _safe_to_implement(metrics: ProbeMetrics) -> bool:
    return (
        metrics.triggered_multistep > 0
        and metrics.triggered_known_false_positives == 0
        and metrics.authority_touch_rate == 0
        and metrics.philosophy_touch_rate == 0
    )


def compute_report_replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {k: v for k, v in payload.items()
               if k not in ("started_at", "finished_at", "replay_hash")}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_probe_report(
    run: CausalProbeRun,
    *,
    started_at: datetime,
    finished_at: datetime,
) -> CausalChainProbeReport:
    metrics = compute_probe_metrics(run)
    guards = _required_guards(metrics)
    dominant = _dominant_risk_flags(metrics)
    safe = _safe_to_implement(metrics)
    payload = {
        "total_cases": metrics.total,
        "triggered_multistep": metrics.triggered_multistep,
        "triggered_main": metrics.triggered_main,
        "triggered_known_false_positives":
            metrics.triggered_known_false_positives,
        "dominant_risk_flags": [f.value for f in dominant],
        "safe_to_implement": safe,
        "required_guards_before_implementation": list(guards),
        "metrics": metrics.to_dict(),
        "candidates": [c.to_dict() for c in run.candidates],
    }
    replay_hash = compute_report_replay_hash(payload)
    return CausalChainProbeReport(
        started_at=started_at,
        finished_at=finished_at,
        total_cases=metrics.total,
        triggered_multistep=metrics.triggered_multistep,
        triggered_main=metrics.triggered_main,
        triggered_known_false_positives=(
            metrics.triggered_known_false_positives
        ),
        dominant_risk_flags=dominant,
        safe_to_implement=safe,
        required_guards_before_implementation=guards,
        metrics=metrics,
        candidates=run.candidates,
        replay_hash=replay_hash,
    )


__all__ = [
    "CausalChainProbeReport",
    "build_probe_report",
    "compute_report_replay_hash",
]
