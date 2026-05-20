"""v3.117 — blindness census report.

Pflichtmetriken (directive § v3.117):

* ``blindness_pool_count``
* ``affected_family_count``
* ``largest_pool_size``
* ``mean_pool_size``
* ``replay_stability``

Killerfrage: "Ist der 10-Familien-Fall
einzigartig?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .census import (
    all_blindness_pools,
    cross_family_pools,
)
from .detect import (
    affected_family_count,
    blindness_pool_count,
    largest_pool_size,
    mean_pool_size,
    total_blind_anchor_count,
    total_pool_count,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3117Report:
    total_pool_count: int
    blindness_pool_count: int
    affected_family_count: int
    largest_pool_size: int
    mean_pool_size: float
    total_blind_anchor_count: int
    pools: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "total_pool_count":
                self.total_pool_count,
            "blindness_pool_count":
                self.blindness_pool_count,
            "affected_family_count":
                self.affected_family_count,
            "largest_pool_size":
                self.largest_pool_size,
            "mean_pool_size":
                self.mean_pool_size,
            "total_blind_anchor_count":
                self.total_blind_anchor_count,
            "pools": list(self.pools),
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
        blindness_pool_count(),
        affected_family_count(),
        largest_pool_size(),
        mean_pool_size(),
    )
    b = (
        blindness_pool_count(),
        affected_family_count(),
        largest_pool_size(),
        mean_pool_size(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3117Report:
    pools = cross_family_pools()
    bpc = blindness_pool_count()
    afc = affected_family_count()
    lps = largest_pool_size()
    mps = mean_pool_size()
    tbac = total_blind_anchor_count()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif bpc >= 10:
        verdict = "BLINDNESS_PERVASIVE"
    elif bpc > 0:
        verdict = "BLINDNESS_LOCAL"
    else:
        verdict = "NO_BLINDNESS"

    rationale = (
        f"INFO: total_pool_count "
        f"{total_pool_count()}",
        f"INFO: blindness_pool_count {bpc} "
        f"(cross-family)",
        f"INFO: affected_family_count {afc}",
        f"INFO: largest_pool_size {lps}",
        f"INFO: mean_pool_size {mps}",
        f"INFO: total_blind_anchor_count "
        f"{tbac}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3117Report(
        total_pool_count=total_pool_count(),
        blindness_pool_count=bpc,
        affected_family_count=afc,
        largest_pool_size=lps,
        mean_pool_size=mps,
        total_blind_anchor_count=tbac,
        pools=tuple(
            p.to_dict() for p in pools
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_state_blindness_census_artifact(
) -> dict[str, object]:
    pools = cross_family_pools()
    return {
        "schema_version":
            "v3_117_state_blindness_census",
        "total_pool_count":
            total_pool_count(),
        "blindness_pool_count":
            blindness_pool_count(),
        "affected_family_count":
            affected_family_count(),
        "largest_pool_size":
            largest_pool_size(),
        "mean_pool_size": mean_pool_size(),
        "total_blind_anchor_count":
            total_blind_anchor_count(),
        "pools": [
            p.to_dict() for p in pools
        ],
    }


__all__ = [
    "V3117Report",
    "build_report",
    "build_state_blindness_census_artifact",
]
