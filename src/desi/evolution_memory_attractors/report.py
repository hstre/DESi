"""v30.2 - Evolutionary Attractor Analysis report.

Pflichtmetriken (directive § v30.2):

* attractor_visibility
* mutation_cluster_visibility
* drift_visibility
* evolution_diversity
* replay_stability

Killerfrage: "Entwickelt DESi stabile evolutionaere Attraktoren
unter Replay-Governance?"

Surfaces evolutionary attractors, mutation clusters, optimisation
traps (all-rejected areas) and branch drift. Descriptive only;
evolution stays diverse and replay-stable.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .attractors import (
    attractor_areas, attractor_visibility, attractors,
    evolution_diversity,
)
from .branch_drift import (
    branches_targeting_main, converges_on_base, drift_visibility,
)
from .mutation_clusters import (
    clusters_by_area, mutation_cluster_visibility,
)
from .optimization_traps import (
    optimization_traps, productive_areas, trap_visibility,
)

VERDICT_STABLE = "STABLE_ATTRACTORS_DIVERSE"
VERDICT_COLLAPSED = "EVOLUTION_COLLAPSED"
VERDICT_HALT = "ATTRACTOR_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STABLE, VERDICT_COLLAPSED, VERDICT_HALT,
)

_FLOOR = 0.90
_DIVERSITY_FLOOR = 0.50


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{a}:{','.join(ms)}"
        for a, ms in sorted(clusters_by_area().items())
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    return 1.0 if _signature() == _signature() else 0.0


def _recommendation(
    *, replay: float, attractor: float, cluster: float,
    drift: float, diversity: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if diversity < _DIVERSITY_FLOOR:
        return VERDICT_COLLAPSED
    if (
        attractor < _FLOOR
        or cluster < _FLOOR
        or drift < _FLOOR
    ):
        return VERDICT_HALT
    return VERDICT_STABLE


@dataclass(frozen=True)
class V302Report:
    cluster_count: int
    attractor_count: int
    trap_count: int
    attractor_visibility: float
    mutation_cluster_visibility: float
    drift_visibility: float
    evolution_diversity: float
    replay_stability: float
    optimization_traps: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_count": self.cluster_count,
            "attractor_count": self.attractor_count,
            "trap_count": self.trap_count,
            "attractor_visibility": self.attractor_visibility,
            "mutation_cluster_visibility":
                self.mutation_cluster_visibility,
            "drift_visibility": self.drift_visibility,
            "evolution_diversity": self.evolution_diversity,
            "replay_stability": self.replay_stability,
            "optimization_traps": list(self.optimization_traps),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V302Report:
    attractor = attractor_visibility()
    cluster = mutation_cluster_visibility()
    drift = drift_visibility()
    diversity = evolution_diversity()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, attractor=attractor, cluster=cluster,
        drift=drift, diversity=diversity,
    )
    rationale = (
        f"INFO: {len(clusters_by_area())} mutation clusters; "
        f"{len(attractors())} attractors "
        f"{list(attractor_areas())}; {len(optimization_traps())} "
        f"optimisation traps (all-rejected areas)",
        "INFO: descriptive structure only; no auto-avoidance, no "
        "policy learning, governance unchanged",
        f"{'PASS' if attractor >= _FLOOR else 'FAIL'}: "
        f"attractor_visibility {attractor} >= 0.90",
        f"{'PASS' if cluster >= _FLOOR else 'FAIL'}: "
        f"mutation_cluster_visibility {cluster} >= 0.90",
        f"{'PASS' if drift >= _FLOOR else 'FAIL'}: "
        f"drift_visibility {drift} >= 0.90 (converging on base "
        f"{len(converges_on_base())}; to-main "
        f"{list(branches_targeting_main())})",
        f"{'PASS' if diversity >= _DIVERSITY_FLOOR else 'FAIL'}: "
        f"evolution_diversity {diversity} >= 0.50 (not "
        f"collapsed; productive areas {len(productive_areas())})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V302Report(
        cluster_count=len(clusters_by_area()),
        attractor_count=len(attractors()),
        trap_count=len(optimization_traps()),
        attractor_visibility=attractor,
        mutation_cluster_visibility=cluster,
        drift_visibility=drift,
        evolution_diversity=diversity,
        replay_stability=replay,
        optimization_traps=optimization_traps(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_attractors_artifact() -> dict[str, object]:
    return {
        "schema_version": "v30_2_evolutionary_attractors",
        "disclaimer": (
            "Surfaces evolutionary attractors (areas that "
            "repeatedly attract mutation ideas), mutation "
            "clusters, optimisation traps (all-rejected areas) "
            "and branch drift over the evolution history. "
            "Descriptive only - no auto-avoidance, no policy "
            "learning, no governance change. Evolution stays "
            "diverse and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "clusters_by_area": {
            a: list(ms) for a, ms in clusters_by_area().items()
        },
        "attractors": {
            a: list(ms) for a, ms in attractors().items()
        },
        "optimization_traps": list(optimization_traps()),
        "productive_areas": list(productive_areas()),
        "attractor_visibility": attractor_visibility(),
        "mutation_cluster_visibility":
            mutation_cluster_visibility(),
        "drift_visibility": drift_visibility(),
        "evolution_diversity": evolution_diversity(),
        "replay_stability": replay_stability(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COLLAPSED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "V302Report",
    "build_attractors_artifact",
    "build_report",
    "replay_stability",
]
