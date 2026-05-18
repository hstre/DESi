"""v3.111 — semantic substitution report.

Pflichtmetriken (directive § v3.111):

* ``semantic_recovery``
* ``semantic_auc``
* ``semantic_purity``
* ``complexity_delta``
* ``replay_stability``

Killerfrage: "Gibt es strukturelle Alternativen
zu den Proxies?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .semantic import SEMANTIC_CANDIDATES
from .substitute import (
    all_semantic_outcomes,
    complexity_delta,
    semantic_auc,
    semantic_purity,
    semantic_recovery,
)


RECOVERY_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3111Report:
    instance_count: int
    semantic_candidate_count: int
    semantic_recovery: float
    semantic_auc: float
    semantic_purity: float
    complexity_delta: float
    outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "instance_count":
                self.instance_count,
            "semantic_candidate_count":
                self.semantic_candidate_count,
            "semantic_recovery":
                self.semantic_recovery,
            "semantic_auc": self.semantic_auc,
            "semantic_purity":
                self.semantic_purity,
            "complexity_delta":
                self.complexity_delta,
            "outcomes": list(self.outcomes),
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
        semantic_recovery(),
        semantic_auc(),
        semantic_purity(),
        complexity_delta(),
    )
    b = (
        semantic_recovery(),
        semantic_auc(),
        semantic_purity(),
        complexity_delta(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3111Report:
    outs = all_semantic_outcomes()
    sr = semantic_recovery()
    sa = semantic_auc()
    sp = semantic_purity()
    cd = complexity_delta()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif sr >= RECOVERY_THRESHOLD:
        verdict = "SEMANTIC_SUBSTITUTE_FOUND"
    elif sr > 0.0:
        verdict = (
            "SEMANTIC_SUBSTITUTE_PARTIAL"
        )
    else:
        verdict = "NO_SEMANTIC_SUBSTITUTE"

    rationale = (
        f"INFO: instance_count {len(outs)}",
        f"INFO: semantic_candidate_count "
        f"{len(SEMANTIC_CANDIDATES)}",
        f"{'PASS' if sr >= RECOVERY_THRESHOLD else 'FAIL'}: "
        f"semantic_recovery {sr} "
        f"(threshold {RECOVERY_THRESHOLD})",
        f"INFO: semantic_auc {sa}",
        f"INFO: semantic_purity {sp}",
        f"INFO: complexity_delta {cd} "
        f"(positive ⇒ semantic vocab is bigger)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3111Report(
        instance_count=len(outs),
        semantic_candidate_count=len(
            SEMANTIC_CANDIDATES,
        ),
        semantic_recovery=sr,
        semantic_auc=sa,
        semantic_purity=sp,
        complexity_delta=cd,
        outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_semantic_substitution_artifact(
) -> dict[str, object]:
    outs = all_semantic_outcomes()
    return {
        "schema_version":
            "v3_111_t10_semantic_substitution",
        "instance_count": len(outs),
        "semantic_candidates":
            list(SEMANTIC_CANDIDATES),
        "semantic_recovery":
            semantic_recovery(),
        "semantic_auc": semantic_auc(),
        "semantic_purity": semantic_purity(),
        "complexity_delta":
            complexity_delta(),
        "outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "RECOVERY_THRESHOLD",
    "V3111Report",
    "build_report",
    "build_t10_semantic_substitution_artifact",
]
