"""v10.2 — path-dependence report.

Five Pflichtmetriken:

* ``path_rigidity``
* ``bad_precedent_persistence``
* ``norm_drift``
* ``epistemic_flexibility``
* ``replay_stability``

Killerfrage: "Kann DESi institutionelles
Gedaechtnis haben, ohne epistemisch zu
verkrusten?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .memory import (
    PRECEDENT_KINDS, fixture, kind_counts,
)
from .norms import norm_drift, path_rigidity
from .precedent import (
    bad_precedent_persistence,
    epistemic_flexibility, overturn_rate,
    precedent_verdicts,
)


@dataclass(frozen=True)
class V102Report:
    decision_count: int
    path_rigidity: float
    bad_precedent_persistence: float
    norm_drift: float
    epistemic_flexibility: float
    overturn_rate: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_count":
                self.decision_count,
            "path_rigidity":
                self.path_rigidity,
            "bad_precedent_persistence":
                self.bad_precedent_persistence,
            "norm_drift": self.norm_drift,
            "epistemic_flexibility":
                self.epistemic_flexibility,
            "overturn_rate":
                self.overturn_rate,
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


def _replay_stability() -> float:
    a = (
        path_rigidity(),
        bad_precedent_persistence(),
        norm_drift(), epistemic_flexibility(),
        overturn_rate(),
    )
    b = (
        path_rigidity(),
        bad_precedent_persistence(),
        norm_drift(), epistemic_flexibility(),
        overturn_rate(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, pr: float, bpp: float,
    nd: float, ef: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if bpp > 0.10:
        return "PATH_BAD_PRECEDENT"
    if pr > 0.95:
        return "PATH_RIGIDIFIED"
    if ef < 0.90:
        return "PATH_INFLEXIBLE"
    if nd > 1.0:
        return "PATH_NORM_DRIFT"
    return "PATH_HEALTHY"


def build_report() -> V102Report:
    pr = path_rigidity()
    bpp = bad_precedent_persistence()
    nd = norm_drift()
    ef = epistemic_flexibility()
    o = overturn_rate()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, pr=pr, bpp=bpp,
        nd=nd, ef=ef,
    )
    rationale = (
        f"INFO: decision_count "
        f"{len(fixture())}",
        f"INFO: kind_counts {kind_counts()}",
        f"INFO: overturn_rate {o}",
        f"{'PASS' if bpp <= 0.10 else 'FAIL'}: "
        f"bad_precedent_persistence {bpp} "
        f"<= 0.10",
        f"{'PASS' if pr <= 0.95 else 'FAIL'}: "
        f"path_rigidity {pr} <= 0.95",
        f"{'PASS' if nd <= 1.0 else 'FAIL'}: "
        f"norm_drift {nd} <= 1.0",
        f"{'PASS' if ef >= 0.90 else 'FAIL'}: "
        f"epistemic_flexibility {ef} >= 0.90",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V102Report(
        decision_count=len(fixture()),
        path_rigidity=pr,
        bad_precedent_persistence=bpp,
        norm_drift=nd,
        epistemic_flexibility=ef,
        overturn_rate=o,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_path_dependence_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v10_2_path_dependence",
        "precedent_kinds":
            list(PRECEDENT_KINDS),
        "decision_count": len(fixture()),
        "kind_counts": kind_counts(),
        "decisions": [
            d.to_dict() for d in fixture()
        ],
        "precedent_verdicts": [
            v.to_dict()
            for v in precedent_verdicts()
        ],
        "path_rigidity": path_rigidity(),
        "bad_precedent_persistence":
            bad_precedent_persistence(),
        "norm_drift": norm_drift(),
        "epistemic_flexibility":
            epistemic_flexibility(),
        "overturn_rate": overturn_rate(),
    }


__all__ = [
    "V102Report",
    "build_path_dependence_artifact",
    "build_report",
]
