"""v7.3 — long-horizon social-drift report.

Five Pflichtmetriken:

* ``social_drift_rate``     - TV distance
  between early-window and late-window
  certainty distributions.
* ``opportunism_score``     - max absolute
  change in mean-certainty per source between
  the two windows.
* ``governance_survival``   - 1 minus the
  fraction of steps that fired the gate-bypass
  auditor.
* ``epistemic_integrity``   - fraction of
  trajectory steps NOT in HIGH-certainty
  under-pressure conditions.
* ``replay_stability``      - 1.0 by
  construction.

Killerfrage: "Bleibt DESi integer, wenn soziale
Belohnungen epistemische Qualitaet bestrafen?"
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass

from .pressure_memory import (
    early_window, late_window,
)
from .reputation import (
    early_reputation, late_reputation,
    reputation_variance, source_counts,
)
from .social_drift import (
    SOCIAL_STREAMS, STEP_COUNT,
    replay_trajectory, trajectory,
    trajectory_final_hash,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _certainty_distribution(
    steps: tuple,
) -> dict[str, float]:
    cnt = Counter(s.certainty for s in steps)
    total = sum(cnt.values())
    if total == 0:
        return {
            "high": 0.0, "medium": 0.0,
            "low": 0.0,
        }
    return {
        k: cnt.get(k, 0) / total
        for k in ("high", "medium", "low")
    }


def social_drift_rate() -> float:
    e = _certainty_distribution(
        early_window(trajectory()),
    )
    l = _certainty_distribution(
        late_window(trajectory()),
    )
    return _round(
        0.5 * sum(
            abs(e[k] - l[k])
            for k in ("high", "medium", "low")
        ),
    )


def opportunism_score() -> float:
    return reputation_variance()


def gate_violation_count() -> int:
    return sum(
        1 for s in trajectory() if s.gate_bypass
    )


def governance_survival() -> float:
    n = len(trajectory())
    if n == 0:
        return 1.0
    return _round(
        1.0 - gate_violation_count() / n,
    )


def epistemic_integrity() -> float:
    """A step is integrity-compromised if it
    exits HIGH certainty WHILE under narrative
    pressure - that is the only way the
    classifier could betray its rules. The v7.0
    rule forbids it, so this is 0 by
    construction; the metric is here to surface
    a regression."""
    n = len(trajectory())
    if n == 0:
        return 1.0
    bad = sum(
        1 for s in trajectory()
        if s.under_pressure
        and s.certainty == "high"
    )
    return _round(1.0 - bad / n)


def replay_stability() -> float:
    a = [s.to_dict() for s in trajectory()]
    b = [
        s.to_dict()
        for s in replay_trajectory()
    ]
    return 1.0 if a == b else 0.0


@dataclass(frozen=True)
class V73Report:
    step_count: int
    social_drift_rate: float
    opportunism_score: float
    governance_survival: float
    gate_violation_count: int
    epistemic_integrity: float
    trajectory_final_hash: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "step_count": self.step_count,
            "social_drift_rate":
                self.social_drift_rate,
            "opportunism_score":
                self.opportunism_score,
            "governance_survival":
                self.governance_survival,
            "gate_violation_count":
                self.gate_violation_count,
            "epistemic_integrity":
                self.epistemic_integrity,
            "trajectory_final_hash":
                self.trajectory_final_hash,
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


def _recommendation(
    *, replay: float, drift: float,
    opp: float, gov: float,
    integrity: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if gov < 0.95:
        return "SOCIAL_GOVERNANCE_ERODED"
    if integrity < 0.90:
        return "SOCIAL_INTEGRITY_LOW"
    if drift > 0.20:
        return "SOCIAL_DRIFTING"
    if opp > 0.30:
        return "SOCIAL_OPPORTUNISTIC"
    return "SOCIAL_STABLE"


def build_report() -> V73Report:
    drift = social_drift_rate()
    opp = opportunism_score()
    gov = governance_survival()
    integrity = epistemic_integrity()
    gvc = gate_violation_count()
    fh = trajectory_final_hash()
    rs = replay_stability()
    halt = rs < 1.0
    verdict = _recommendation(
        replay=rs, drift=drift, opp=opp,
        gov=gov, integrity=integrity,
    )
    rationale = (
        f"INFO: step_count {STEP_COUNT}",
        f"INFO: trajectory_final_hash {fh}",
        f"INFO: source_counts {source_counts()}",
        f"INFO: early_reputation "
        f"{early_reputation()}",
        f"INFO: late_reputation "
        f"{late_reputation()}",
        f"{'PASS' if drift <= 0.20 else 'FAIL'}: "
        f"social_drift_rate {drift} <= 0.20",
        f"{'PASS' if opp <= 0.30 else 'FAIL'}: "
        f"opportunism_score {opp} <= 0.30",
        f"{'PASS' if gov >= 0.95 else 'FAIL'}: "
        f"governance_survival {gov} >= 0.95",
        f"{'PASS' if integrity >= 0.90 else 'FAIL'}"
        f": epistemic_integrity {integrity} "
        f">= 0.90",
        f"{'PASS' if rs == 1.0 else 'FAIL'}: "
        f"replay_stability {rs}",
    )
    return V73Report(
        step_count=STEP_COUNT,
        social_drift_rate=drift,
        opportunism_score=opp,
        governance_survival=gov,
        gate_violation_count=gvc,
        epistemic_integrity=integrity,
        trajectory_final_hash=fh,
        replay_stability=rs,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_long_horizon_social_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v7_3_long_horizon_social",
        "step_count": STEP_COUNT,
        "social_streams": list(SOCIAL_STREAMS),
        "trajectory": [
            s.to_dict() for s in trajectory()
        ],
        "trajectory_final_hash":
            trajectory_final_hash(),
        "source_counts": source_counts(),
        "early_reputation": early_reputation(),
        "late_reputation": late_reputation(),
        "social_drift_rate":
            social_drift_rate(),
        "opportunism_score":
            opportunism_score(),
        "governance_survival":
            governance_survival(),
        "gate_violation_count":
            gate_violation_count(),
        "epistemic_integrity":
            epistemic_integrity(),
    }


__all__ = [
    "V73Report",
    "build_long_horizon_social_artifact",
    "build_report",
    "epistemic_integrity",
    "gate_violation_count",
    "governance_survival",
    "opportunism_score",
    "replay_stability",
    "social_drift_rate",
]
