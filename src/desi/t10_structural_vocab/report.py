"""v3.115 — minimal structural alphabet report.

Pflichtmetriken (directive § v3.115):

* ``minimal_vocab_size``
* ``vocab_recovery``
* ``mean_auc``
* ``complexity_cost``
* ``replay_stability``

Killerfrage: "Gibt es ein echtes strukturelles
Alphabet?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .search import (
    MAX_VOCAB_SIZE,
    all_subset_outcomes,
    best_subset,
)
from .vocab import (
    complexity_cost,
    mean_auc,
    minimal_vocab_size,
    vocab_recovery,
)


RECOVERY_THRESHOLD: float = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3115Report:
    subset_count: int
    best_subset: tuple[str, ...]
    minimal_vocab_size: int
    vocab_recovery: float
    mean_auc: float
    complexity_cost: float
    subset_outcomes_sample: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "subset_count": self.subset_count,
            "best_subset":
                list(self.best_subset),
            "minimal_vocab_size":
                self.minimal_vocab_size,
            "vocab_recovery":
                self.vocab_recovery,
            "mean_auc": self.mean_auc,
            "complexity_cost":
                self.complexity_cost,
            "subset_outcomes_sample":
                list(
                    self.subset_outcomes_sample,
                ),
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
        best_subset().to_dict(),
        vocab_recovery(),
    )
    b = (
        best_subset().to_dict(),
        vocab_recovery(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3115Report:
    outs = all_subset_outcomes()
    best = best_subset()
    vs = minimal_vocab_size()
    vr = vocab_recovery()
    ma = mean_auc()
    cc = complexity_cost()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif vr >= RECOVERY_THRESHOLD:
        verdict = "STRUCTURAL_ALPHABET_FOUND"
    elif vr > 0.0:
        verdict = "STRUCTURAL_ALPHABET_PARTIAL"
    else:
        verdict = "NO_STRUCTURAL_ALPHABET"

    sample = tuple(
        o.to_dict() for o in outs[:6]
    )

    rationale = (
        f"INFO: subset_count {len(outs)} "
        f"(sizes 1..{MAX_VOCAB_SIZE})",
        f"INFO: best_subset {list(best.subset)}",
        f"INFO: minimal_vocab_size {vs}",
        f"{'PASS' if vr >= RECOVERY_THRESHOLD else 'FAIL'}: "
        f"vocab_recovery {vr} "
        f"(threshold {RECOVERY_THRESHOLD})",
        f"INFO: mean_auc {ma}",
        f"INFO: complexity_cost {cc}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3115Report(
        subset_count=len(outs),
        best_subset=best.subset,
        minimal_vocab_size=vs,
        vocab_recovery=vr,
        mean_auc=ma,
        complexity_cost=cc,
        subset_outcomes_sample=sample,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_structural_vocab_artifact(
) -> dict[str, object]:
    outs = all_subset_outcomes()
    return {
        "schema_version":
            "v3_115_t10_structural_vocab",
        "subset_count": len(outs),
        "best_subset":
            list(best_subset().subset),
        "minimal_vocab_size":
            minimal_vocab_size(),
        "vocab_recovery": vocab_recovery(),
        "mean_auc": mean_auc(),
        "complexity_cost":
            complexity_cost(),
        "subset_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "RECOVERY_THRESHOLD",
    "V3115Report",
    "build_report",
    "build_t10_structural_vocab_artifact",
]
