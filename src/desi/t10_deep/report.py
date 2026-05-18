"""v3.113 — structural topology census report.

Pflichtmetriken (directive § v3.113):

* ``candidate_count``
* ``signal_candidates``
* ``top_candidate_auc``
* ``top_candidate_purity``
* ``top_candidate_margin``
* ``replay_stability``

Killerfrage: "Welche echte strukturelle
Information fehlt DESi?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .graph import (
    all_structural_outcomes,
    signal_candidates,
    top_candidate,
)
from .topology import STRUCTURAL_CANDIDATES


AUC_SIGNAL_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3113Report:
    candidate_count: int
    signal_candidates: tuple[str, ...]
    signal_candidate_count: int
    top_candidate: str
    top_candidate_auc: float
    top_candidate_purity: float
    top_candidate_margin: float
    structural_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_count":
                self.candidate_count,
            "signal_candidates":
                list(self.signal_candidates),
            "signal_candidate_count":
                self.signal_candidate_count,
            "top_candidate":
                self.top_candidate,
            "top_candidate_auc":
                self.top_candidate_auc,
            "top_candidate_purity":
                self.top_candidate_purity,
            "top_candidate_margin":
                self.top_candidate_margin,
            "structural_outcomes":
                list(self.structural_outcomes),
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
        signal_candidates(),
        top_candidate().to_dict(),
    )
    b = (
        signal_candidates(),
        top_candidate().to_dict(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3113Report:
    outs = all_structural_outcomes()
    sigs = signal_candidates()
    top = top_candidate()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif top.mean_auc >= AUC_SIGNAL_THRESHOLD:
        verdict = "STRUCTURAL_SIGNAL_FOUND"
    elif sigs:
        verdict = "STRUCTURAL_SIGNAL_WEAK"
    else:
        verdict = "NO_STRUCTURAL_SIGNAL"

    rationale = (
        f"INFO: candidate_count "
        f"{len(STRUCTURAL_CANDIDATES)}",
        f"INFO: signal_candidate_count "
        f"{len(sigs)}",
        f"INFO: signal_candidates {list(sigs)}",
        f"INFO: top_candidate {top.candidate}",
        f"{'PASS' if top.mean_auc >= AUC_SIGNAL_THRESHOLD else 'FAIL'}: "
        f"top_candidate_auc {top.mean_auc} "
        f"(threshold {AUC_SIGNAL_THRESHOLD})",
        f"INFO: top_candidate_purity "
        f"{top.mean_purity}",
        f"INFO: top_candidate_margin "
        f"{top.mean_margin}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3113Report(
        candidate_count=len(
            STRUCTURAL_CANDIDATES,
        ),
        signal_candidates=sigs,
        signal_candidate_count=len(sigs),
        top_candidate=top.candidate,
        top_candidate_auc=top.mean_auc,
        top_candidate_purity=top.mean_purity,
        top_candidate_margin=top.mean_margin,
        structural_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_structural_topology_artifact(
) -> dict[str, object]:
    outs = all_structural_outcomes()
    top = top_candidate()
    return {
        "schema_version":
            "v3_113_t10_structural_topology",
        "candidate_count":
            len(STRUCTURAL_CANDIDATES),
        "candidates":
            list(STRUCTURAL_CANDIDATES),
        "signal_candidates":
            list(signal_candidates()),
        "top_candidate": top.candidate,
        "top_candidate_auc": top.mean_auc,
        "top_candidate_purity":
            top.mean_purity,
        "top_candidate_margin":
            top.mean_margin,
        "structural_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "AUC_SIGNAL_THRESHOLD",
    "V3113Report",
    "build_report",
    "build_t10_structural_topology_artifact",
]
