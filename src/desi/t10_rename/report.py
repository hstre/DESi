"""v3.110 — cross-rename attack report.

Pflichtmetriken (directive § v3.110):

* ``rename_attack_auc``
* ``rename_attack_purity``
* ``name_leakage_score``
* ``broken_candidates``
* ``replay_stability``

Killerfrage: "Lernen die Kandidaten Namen statt
Struktur?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .attack import (
    all_rename_cell_outcomes,
    broken_candidates,
    name_leakage_score,
    rename_attack_auc,
    rename_attack_rescue_rate,
)
from .rename import RENAME_KINDS, RENAME_SEEDS


AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3110Report:
    rename_kind_count: int
    rename_seed_count: int
    cell_count: int
    rename_attack_auc: float
    rename_attack_rescue_rate: float
    name_leakage_score: float
    broken_candidates: tuple[str, ...]
    cell_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "rename_kind_count":
                self.rename_kind_count,
            "rename_seed_count":
                self.rename_seed_count,
            "cell_count": self.cell_count,
            "rename_attack_auc":
                self.rename_attack_auc,
            "rename_attack_rescue_rate":
                self.rename_attack_rescue_rate,
            "name_leakage_score":
                self.name_leakage_score,
            "broken_candidates":
                list(self.broken_candidates),
            "cell_outcomes":
                list(self.cell_outcomes),
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
        rename_attack_auc(),
        name_leakage_score(),
        broken_candidates(),
    )
    b = (
        rename_attack_auc(),
        name_leakage_score(),
        broken_candidates(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3110Report:
    outs = all_rename_cell_outcomes()
    auc = rename_attack_auc()
    rr = rename_attack_rescue_rate()
    nls = name_leakage_score()
    bc = broken_candidates()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif auc >= AUC_THRESHOLD and nls <= 0.20:
        verdict = "STRUCTURE_NOT_NAME_BASED"
    elif auc >= AUC_THRESHOLD:
        verdict = "STRUCTURE_PARTIAL_LEAKAGE"
    else:
        verdict = "NAME_LEAKAGE_DOMINATES"

    rationale = (
        f"INFO: rename_kind_count "
        f"{len(RENAME_KINDS)}",
        f"INFO: rename_seed_count "
        f"{len(RENAME_SEEDS)}",
        f"INFO: cell_count {len(outs)}",
        f"{'PASS' if auc >= AUC_THRESHOLD else 'FAIL'}: "
        f"rename_attack_auc {auc} "
        f"(threshold {AUC_THRESHOLD})",
        f"INFO: rename_attack_rescue_rate {rr}",
        f"INFO: name_leakage_score {nls}",
        f"INFO: broken_candidates {list(bc)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3110Report(
        rename_kind_count=len(RENAME_KINDS),
        rename_seed_count=len(RENAME_SEEDS),
        cell_count=len(outs),
        rename_attack_auc=auc,
        rename_attack_rescue_rate=rr,
        name_leakage_score=nls,
        broken_candidates=bc,
        cell_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_cross_rename_attack_artifact(
) -> dict[str, object]:
    outs = all_rename_cell_outcomes()
    return {
        "schema_version":
            "v3_110_t10_cross_rename_attack",
        "rename_kinds": list(RENAME_KINDS),
        "rename_seeds": list(RENAME_SEEDS),
        "cell_count": len(outs),
        "rename_attack_auc":
            rename_attack_auc(),
        "rename_attack_rescue_rate":
            rename_attack_rescue_rate(),
        "name_leakage_score":
            name_leakage_score(),
        "broken_candidates":
            list(broken_candidates()),
        "cell_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "AUC_THRESHOLD",
    "V3110Report",
    "build_report",
    "build_t10_cross_rename_attack_artifact",
]
