"""v3.122 — regression governance report.

Pflichtmetriken (directive § v3.122):

* ``avoidable_full_runs``
* ``wasted_cpu_hours``
* ``recommended_policy``
* ``historical_risk``
* ``replay_stability``

Killerfrage: "Verbrennen wir gerade
Wissenschaftszeit?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .governance import (
    MUTATION_KINDS,
    all_classified_commits,
)
from .policy import (
    avoidable_full_runs,
    commit_classification_counts,
    core_or_gate_commit_count,
    historical_risk_level,
    recommended_policy_for,
    wasted_cpu_hours,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3122Report:
    commit_count: int
    classification_counts: dict[str, int]
    core_or_gate_commit_count: int
    avoidable_full_runs: int
    wasted_cpu_hours: float
    recommended_policy: dict[str, str]
    historical_risk: str
    classified_commits: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "commit_count": self.commit_count,
            "classification_counts":
                self.classification_counts,
            "core_or_gate_commit_count":
                self.core_or_gate_commit_count,
            "avoidable_full_runs":
                self.avoidable_full_runs,
            "wasted_cpu_hours":
                self.wasted_cpu_hours,
            "recommended_policy":
                self.recommended_policy,
            "historical_risk":
                self.historical_risk,
            "classified_commits":
                list(self.classified_commits),
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
        avoidable_full_runs(),
        commit_classification_counts(),
        historical_risk_level(),
    )
    b = (
        avoidable_full_runs(),
        commit_classification_counts(),
        historical_risk_level(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3122Report:
    commits = all_classified_commits()
    counts = commit_classification_counts()
    afr = avoidable_full_runs()
    wch = wasted_cpu_hours()
    risk = historical_risk_level()
    cgc = core_or_gate_commit_count()
    policy = {
        k: recommended_policy_for(k)
        for k in MUTATION_KINDS
    }
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif afr == 0:
        verdict = "POLICY_ALREADY_OPTIMAL"
    elif risk == "low":
        verdict = "POLICY_RECOMMENDED"
    else:
        verdict = "POLICY_RISKY"

    rationale = (
        f"INFO: commit_count {len(commits)}",
        f"INFO: classification_counts {counts}",
        f"INFO: core_or_gate_commit_count "
        f"{cgc}",
        f"INFO: avoidable_full_runs {afr}",
        f"INFO: wasted_cpu_hours {wch}",
        f"INFO: recommended_policy {policy}",
        f"INFO: historical_risk {risk}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3122Report(
        commit_count=len(commits),
        classification_counts=counts,
        core_or_gate_commit_count=cgc,
        avoidable_full_runs=afr,
        wasted_cpu_hours=wch,
        recommended_policy=policy,
        historical_risk=risk,
        classified_commits=tuple(
            c.to_dict() for c in commits
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_regression_governance_artifact(
) -> dict[str, object]:
    commits = all_classified_commits()
    return {
        "schema_version":
            "v3_122_regression_governance",
        "commit_count": len(commits),
        "classification_counts":
            commit_classification_counts(),
        "core_or_gate_commit_count":
            core_or_gate_commit_count(),
        "avoidable_full_runs":
            avoidable_full_runs(),
        "wasted_cpu_hours":
            wasted_cpu_hours(),
        "recommended_policy": {
            k: recommended_policy_for(k)
            for k in MUTATION_KINDS
        },
        "historical_risk":
            historical_risk_level(),
        "classified_commits": [
            c.to_dict() for c in commits
        ],
    }


__all__ = [
    "V3122Report",
    "build_regression_governance_artifact",
    "build_report",
]
