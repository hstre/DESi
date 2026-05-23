"""v3.109 — metadata ablation report.

Pflichtmetriken (directive § v3.109):

* ``metadata_free_auc``
* ``metadata_free_purity``
* ``auc_delta``
* ``collapsed_candidates``
* ``replay_stability``

Killerfrage: "Ueberleben die Kandidaten ohne
Metadaten?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..t10_adaptive.report import (
    mean_candidate_auc as v3107_mean_auc,
)
from .ablation import (
    all_metadata_ablation_outcomes,
    collapsed_candidates,
)


AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def metadata_free_auc() -> float:
    outs = all_metadata_ablation_outcomes()
    if not outs:
        return 0.0
    aucs = [o.best_auc for o in outs]
    return _round(sum(aucs) / len(aucs))


def metadata_free_purity() -> float:
    outs = all_metadata_ablation_outcomes()
    if not outs:
        return 0.0
    purs = [o.best_purity for o in outs]
    return _round(sum(purs) / len(purs))


def rescue_rate() -> float:
    outs = all_metadata_ablation_outcomes()
    if not outs:
        return 0.0
    n = sum(1 for o in outs if o.rescued)
    return _round(n / len(outs))


def auc_delta() -> float:
    """Drop from the v3.107 mean candidate AUC
    (with metadata) to the metadata-free
    counterpart."""
    return _round(
        v3107_mean_auc() - metadata_free_auc(),
    )


@dataclass(frozen=True)
class V3109Report:
    instance_count: int
    metadata_free_auc: float
    metadata_free_purity: float
    auc_delta: float
    rescue_rate: float
    collapsed_candidates: tuple[str, ...]
    outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "instance_count":
                self.instance_count,
            "metadata_free_auc":
                self.metadata_free_auc,
            "metadata_free_purity":
                self.metadata_free_purity,
            "auc_delta": self.auc_delta,
            "rescue_rate": self.rescue_rate,
            "collapsed_candidates":
                list(self.collapsed_candidates),
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
        metadata_free_auc(),
        metadata_free_purity(),
        auc_delta(),
        collapsed_candidates(),
    )
    b = (
        metadata_free_auc(),
        metadata_free_purity(),
        auc_delta(),
        collapsed_candidates(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3109Report:
    outs = all_metadata_ablation_outcomes()
    mfa = metadata_free_auc()
    mfp = metadata_free_purity()
    ad = auc_delta()
    rr = rescue_rate()
    cc = collapsed_candidates()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif mfa >= AUC_THRESHOLD:
        verdict = "CANDIDATES_SURVIVE_ABLATION"
    elif rr > 0.0:
        verdict = "CANDIDATES_PARTIALLY_SURVIVE"
    else:
        verdict = "CANDIDATES_COLLAPSE_UNDER_ABLATION"

    rationale = (
        f"INFO: instance_count {len(outs)}",
        f"{'PASS' if mfa >= AUC_THRESHOLD else 'FAIL'}: "
        f"metadata_free_auc {mfa} "
        f"(threshold {AUC_THRESHOLD})",
        f"INFO: metadata_free_purity {mfp}",
        f"INFO: auc_delta {ad} "
        f"(positive ⇒ metadata mattered)",
        f"INFO: rescue_rate {rr}",
        f"INFO: collapsed_candidates {list(cc)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3109Report(
        instance_count=len(outs),
        metadata_free_auc=mfa,
        metadata_free_purity=mfp,
        auc_delta=ad,
        rescue_rate=rr,
        collapsed_candidates=cc,
        outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_metadata_ablation_artifact(
) -> dict[str, object]:
    outs = all_metadata_ablation_outcomes()
    return {
        "schema_version":
            "v3_109_t10_metadata_ablation",
        "instance_count": len(outs),
        "metadata_free_auc":
            metadata_free_auc(),
        "metadata_free_purity":
            metadata_free_purity(),
        "auc_delta": auc_delta(),
        "rescue_rate": rescue_rate(),
        "collapsed_candidates":
            list(collapsed_candidates()),
        "outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "AUC_THRESHOLD",
    "V3109Report",
    "auc_delta",
    "build_report",
    "build_t10_metadata_ablation_artifact",
    "collapsed_candidates",
    "metadata_free_auc",
    "metadata_free_purity",
    "rescue_rate",
]
