"""v3.93 — residual dimension audit report.

Pflichtmetriken (directive § v3.93):

* ``residual_variance_by_dim``
* ``dominant_dims``
* ``proxy_information_loss``
* ``replay_stability``

Killerfrage: "Welche Dimension versteckt die
Trennung?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .residual import (
    hidden_dim_candidates,
    non_proxy_variance_share,
    proxy_dims, proxy_information_loss,
    proxy_variance_share,
)
from .variance import (
    ENTANGLED_FAMILY_IDS,
    dominant_dims, entangled_members,
    family_mean_diffs,
    residual_total_variance,
    residual_variance_by_dim,
    variance_share_by_dim,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V393Report:
    entangled_family_ids: tuple[str, ...]
    entangled_member_count: int
    residual_total_variance: float
    residual_variance_by_dim: tuple[dict, ...]
    variance_share_by_dim: tuple[dict, ...]
    dominant_dims: tuple[str, ...]
    proxy_dims: tuple[str, ...]
    proxy_variance_share: float
    proxy_information_loss: float
    hidden_dim_candidates: tuple[str, ...]
    family_mean_diffs: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entangled_family_ids":
                list(self.entangled_family_ids),
            "entangled_member_count":
                self.entangled_member_count,
            "residual_total_variance":
                self.residual_total_variance,
            "residual_variance_by_dim":
                list(self.residual_variance_by_dim),
            "variance_share_by_dim":
                list(self.variance_share_by_dim),
            "dominant_dims":
                list(self.dominant_dims),
            "proxy_dims": list(self.proxy_dims),
            "proxy_variance_share":
                self.proxy_variance_share,
            "proxy_information_loss":
                self.proxy_information_loss,
            "hidden_dim_candidates":
                list(self.hidden_dim_candidates),
            "family_mean_diffs":
                list(self.family_mean_diffs),
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
        residual_variance_by_dim(),
        dominant_dims(),
        proxy_information_loss(),
    )
    b = (
        residual_variance_by_dim(),
        dominant_dims(),
        proxy_information_loss(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V393Report:
    members = entangled_members()
    rvbd = residual_variance_by_dim()
    vsbd = variance_share_by_dim()
    pil = proxy_information_loss()
    pvs = proxy_variance_share()
    hidden = hidden_dim_candidates()
    doms = dominant_dims()
    mdiffs = family_mean_diffs()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif not doms:
        verdict = "NO_DOMINANT_DIMS"
    elif pil > 0.5:
        verdict = "PROXY_MISSING_HIDDEN_DIMS"
    else:
        verdict = "PROXY_COVERS_RESIDUAL"

    rvbd_sorted = tuple(
        {"dim": k, "variance": rvbd[k],
         "share": vsbd[k]}
        for k in sorted(
            rvbd, key=lambda d: (-rvbd[d], d),
        )
    )

    rationale = (
        f"INFO: entangled_family_ids "
        f"{list(ENTANGLED_FAMILY_IDS)} "
        f"(member_count={len(members)})",
        f"INFO: residual_total_variance "
        f"{residual_total_variance()}",
        f"INFO: dominant_dims {list(doms)} "
        f"(share > 0.05)",
        f"INFO: proxy_dims {list(proxy_dims())} "
        f"(v3.82 minimal)",
        f"INFO: proxy_variance_share {pvs} "
        f"(share inside proxy)",
        f"INFO: proxy_information_loss {pil} "
        f"(share outside proxy)",
        f"INFO: hidden_dim_candidates "
        f"{list(hidden)}",
        f"INFO: residual_variance_by_dim "
        f"{list(rvbd_sorted)}",
        f"INFO: family_mean_diffs "
        f"{[m.to_dict() for m in mdiffs]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V393Report(
        entangled_family_ids=ENTANGLED_FAMILY_IDS,
        entangled_member_count=len(members),
        residual_total_variance=(
            residual_total_variance()
        ),
        residual_variance_by_dim=rvbd_sorted,
        variance_share_by_dim=tuple(
            {"dim": k, "share": v}
            for k, v in sorted(
                vsbd.items(),
                key=lambda kv: (-kv[1], kv[0]),
            )
        ),
        dominant_dims=doms,
        proxy_dims=proxy_dims(),
        proxy_variance_share=pvs,
        proxy_information_loss=pil,
        hidden_dim_candidates=hidden,
        family_mean_diffs=tuple(
            m.to_dict() for m in mdiffs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_entangled_dimensions_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_93_entangled_dimensions",
        "entangled_family_ids":
            list(ENTANGLED_FAMILY_IDS),
        "entangled_member_count":
            len(entangled_members()),
        "residual_total_variance":
            residual_total_variance(),
        "residual_variance_by_dim": [
            {"dim": k, "variance": v,
             "share":
                variance_share_by_dim()[k]}
            for k, v in sorted(
                residual_variance_by_dim().items(),
                key=lambda kv: (-kv[1], kv[0]),
            )
        ],
        "dominant_dims": list(dominant_dims()),
        "proxy_dims": list(proxy_dims()),
        "proxy_variance_share":
            proxy_variance_share(),
        "proxy_information_loss":
            proxy_information_loss(),
        "hidden_dim_candidates":
            list(hidden_dim_candidates()),
        "family_mean_diffs": [
            m.to_dict()
            for m in family_mean_diffs()
        ],
    }


__all__ = [
    "V393Report",
    "build_entangled_dimensions_artifact",
    "build_report",
]
