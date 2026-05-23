"""v32.2 - Blind Evolution Evaluation report.

Pflichtmetriken (directive § v32.2):

* blindness_integrity
* bias_resistance
* artifact_identity
* governance_identity
* replay_stability

Killerfrage: "Ist die mutierte Version auch unter Blindbedingungen
besser?"

The two versions are compared under neutral anonymous labels. The
evaluator scores only by the measured metric (recompute count) and
never sees which version is the mutated one; there is no
version-aware scoring, no mutation favouritism and no branch bias.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.frozen_baseline import governance_identity
from desi.frozen_benchmark import artifact_identity
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .bias_control import bias_resistance, blindness_integrity
from .blind_runner import replay_stability, run_blind
from .evaluation import blind_winner, blind_winner_is_mutated, margin

BLIND_EVALUATION = True

VERDICT_BLIND_BETTER = "MUTATED_BETTER_UNDER_BLIND_EVALUATION"
VERDICT_BLIND_NEUTRAL = "NO_BLIND_ADVANTAGE"
VERDICT_HALT = "BLIND_EVALUATION_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_BLIND_BETTER, VERDICT_BLIND_NEUTRAL, VERDICT_HALT,
)


def _metrics() -> dict[str, float]:
    return {
        "blindness_integrity": blindness_integrity(),
        "bias_resistance": bias_resistance(),
        "artifact_identity": artifact_identity(),
        "governance_identity": governance_identity(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = _metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    parts.append(f"winner_is_mutated={blind_winner_is_mutated()}")
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    m = _metrics()
    if m["replay_stability"] < 1.0:
        return VERDICT_HALT
    if (
        m["blindness_integrity"] < 1.0
        or m["bias_resistance"] < 1.0
        or m["artifact_identity"] < 1.0
        or m["governance_identity"] < 1.0
    ):
        return VERDICT_HALT
    if blind_winner_is_mutated():
        return VERDICT_BLIND_BETTER
    return VERDICT_BLIND_NEUTRAL


@dataclass(frozen=True)
class V322Report:
    blind_evaluation: bool
    blindness_integrity: float
    bias_resistance: float
    artifact_identity: float
    governance_identity: float
    replay_stability: float
    blind_winner: str
    blind_winner_is_mutated: bool
    margin: int
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "blind_evaluation": self.blind_evaluation,
            "blindness_integrity": self.blindness_integrity,
            "bias_resistance": self.bias_resistance,
            "artifact_identity": self.artifact_identity,
            "governance_identity": self.governance_identity,
            "replay_stability": self.replay_stability,
            "blind_winner": self.blind_winner,
            "blind_winner_is_mutated": self.blind_winner_is_mutated,
            "margin": self.margin,
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


def build_report() -> V322Report:
    m = _metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    rationale = (
        f"INFO: blind_evaluation={BLIND_EVALUATION}; both versions "
        f"scored under neutral labels {list(o.anon_label for o in run_blind())}",
        "INFO: the scorer uses only the measured recompute count; "
        "no version-aware scoring, no mutation favouritism, no "
        "branch bias",
        f"{'PASS' if m['blindness_integrity'] == 1.0 else 'FAIL'}: "
        f"blindness_integrity {m['blindness_integrity']} == 1.0 (no "
        f"true name leaked to the scorer)",
        f"{'PASS' if m['bias_resistance'] == 1.0 else 'FAIL'}: "
        f"bias_resistance {m['bias_resistance']} == 1.0 (winner is "
        f"label-invariant)",
        f"{'PASS' if m['artifact_identity'] == 1.0 else 'FAIL'}: "
        f"artifact_identity {m['artifact_identity']} == 1.0",
        f"{'PASS' if m['governance_identity'] == 1.0 else 'FAIL'}: "
        f"governance_identity {m['governance_identity']} == 1.0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; blind winner {blind_winner()} "
        f"(is_mutated={blind_winner_is_mutated()}, margin {margin()}); "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V322Report(
        blind_evaluation=BLIND_EVALUATION,
        blindness_integrity=m["blindness_integrity"],
        bias_resistance=m["bias_resistance"],
        artifact_identity=m["artifact_identity"],
        governance_identity=m["governance_identity"],
        replay_stability=replay,
        blind_winner=blind_winner(),
        blind_winner_is_mutated=blind_winner_is_mutated(),
        margin=margin(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_blind_artifact() -> dict[str, object]:
    m = _metrics()
    return {
        "schema_version": "v32_2_blind_evaluation",
        "disclaimer": (
            "A blind evaluation of the two versions under neutral "
            "anonymous labels. The scorer ranks only by the "
            "measured recompute count and never sees which version "
            "is the mutated one: there is no version-aware scoring, "
            "no mutation favouritism and no branch bias. The blind "
            "winner is determined first; only afterwards is the "
            "sealed label-to-name map used to verify that the "
            "winner is the mutated version. Outputs are "
            "byte-identical, governance is identical, replay is "
            "stable, and human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "blind_evaluation": BLIND_EVALUATION,
        "blindness_integrity": m["blindness_integrity"],
        "bias_resistance": m["bias_resistance"],
        "artifact_identity": m["artifact_identity"],
        "governance_identity": m["governance_identity"],
        "replay_stability": m["replay_stability"],
        "blind_winner": blind_winner(),
        "blind_winner_is_mutated": blind_winner_is_mutated(),
        "margin": margin(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "BLIND_EVALUATION",
    "REPORT_VERDICTS",
    "VERDICT_BLIND_BETTER",
    "VERDICT_BLIND_NEUTRAL",
    "VERDICT_HALT",
    "V322Report",
    "build_blind_artifact",
    "build_report",
]
