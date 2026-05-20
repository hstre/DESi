"""v3.89 — frame contribution audit report.

Pflichtmetriken (directive § v3.89):

* ``frame_variance_share``
* ``purity_no_frame``
* ``purity_frame_only``
* ``residual_purity``
* ``replay_stability``

Killerfrage: "Ist frame_id wirklich der dominante
Verzerrer?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..novel_family_cluster.report import (
    PURITY_THRESHOLD,
)
from .contribution import (
    FrameCondition, dominant_dim,
    frame_variance_share,
    per_dim_variance, total_variance,
)
from .variance import (
    all_condition_outcomes,
    cluster_purity_for,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V389Report:
    total_variance: float
    per_dim_variance: tuple[dict, ...]
    frame_variance_share: float
    dominant_dim: str
    purity_full: float
    purity_no_frame: float
    purity_frame_only: float
    residual_purity: float
    condition_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "total_variance":
                self.total_variance,
            "per_dim_variance":
                list(self.per_dim_variance),
            "frame_variance_share":
                self.frame_variance_share,
            "dominant_dim": self.dominant_dim,
            "purity_full": self.purity_full,
            "purity_no_frame":
                self.purity_no_frame,
            "purity_frame_only":
                self.purity_frame_only,
            "residual_purity":
                self.residual_purity,
            "condition_outcomes":
                list(self.condition_outcomes),
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
        frame_variance_share(),
        cluster_purity_for(
            FrameCondition.NO_FRAME.value,
        ),
        cluster_purity_for(
            FrameCondition.FRAME_ONLY.value,
        ),
        cluster_purity_for(
            FrameCondition.RESIDUAL.value,
        ),
    )
    b = (
        frame_variance_share(),
        cluster_purity_for(
            FrameCondition.NO_FRAME.value,
        ),
        cluster_purity_for(
            FrameCondition.FRAME_ONLY.value,
        ),
        cluster_purity_for(
            FrameCondition.RESIDUAL.value,
        ),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V389Report:
    fvs = frame_variance_share()
    pdv = per_dim_variance()
    pdv_sorted = tuple(
        {"dim": k, "variance": v, "share": _round(
            v / total_variance(),
        ) if total_variance() > 0 else 0.0}
        for k, v in sorted(
            pdv.items(),
            key=lambda kv: (-kv[1], kv[0]),
        )
    )
    outcomes = all_condition_outcomes()
    purity_by = {o.condition: o.purity for o in outcomes}
    full_p = purity_by[FrameCondition.FULL.value]
    nf_p = purity_by[FrameCondition.NO_FRAME.value]
    fo_p = purity_by[FrameCondition.FRAME_ONLY.value]
    res_p = purity_by[FrameCondition.RESIDUAL.value]
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        fvs >= 0.5
        and nf_p > full_p
    ):
        verdict = "FRAME_IS_DOMINANT_NOISE"
    elif nf_p > full_p:
        verdict = "FRAME_IS_PARTIAL_NOISE"
    else:
        verdict = "FRAME_IS_NOT_NOISE"

    rationale = (
        f"INFO: total_variance "
        f"{total_variance()}",
        f"INFO: dominant_dim {dominant_dim()}",
        f"INFO: frame_variance_share {fvs}",
        f"INFO: purity_full {full_p} "
        f"(baseline)",
        f"{'DELTA+' if nf_p > full_p else 'DELTA-'}: "
        f"purity_no_frame {nf_p} "
        f"(delta {_round(nf_p - full_p)})",
        f"INFO: purity_frame_only {fo_p}",
        f"INFO: residual_purity {res_p}",
        f"INFO: per_dim_variance "
        f"{[d for d in pdv_sorted]}",
        f"INFO: condition_outcomes "
        f"{[o.to_dict() for o in outcomes]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V389Report(
        total_variance=total_variance(),
        per_dim_variance=pdv_sorted,
        frame_variance_share=fvs,
        dominant_dim=dominant_dim(),
        purity_full=full_p,
        purity_no_frame=nf_p,
        purity_frame_only=fo_p,
        residual_purity=res_p,
        condition_outcomes=tuple(
            o.to_dict() for o in outcomes
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_frame_contribution_audit_artifact(
) -> dict[str, object]:
    outcomes = all_condition_outcomes()
    return {
        "schema_version":
            "v3_89_frame_contribution_audit",
        "total_variance": total_variance(),
        "frame_variance_share":
            frame_variance_share(),
        "dominant_dim": dominant_dim(),
        "per_dim_variance": [
            {"dim": k, "variance": v}
            for k, v in sorted(
                per_dim_variance().items(),
                key=lambda kv: (-kv[1], kv[0]),
            )
        ],
        "condition_outcomes": [
            o.to_dict() for o in outcomes
        ],
    }


__all__ = [
    "V389Report",
    "build_frame_contribution_audit_artifact",
    "build_report",
]
