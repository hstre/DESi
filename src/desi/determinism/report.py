"""v3.96a — jitter census report.

Pflichtmetriken (directive § v3.96a):

* ``jitter_rate``
* ``affected_packages``
* ``affected_dims``
* ``max_state_delta``
* ``replay_stability``

Killerfrage: "Wie gross ist der tatsaechliche
Jitter?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .jitter import (
    SEED_CENSUS, affected_packages, census,
)
from .seeds import (
    SHUFFLE_SEEDS, all_shuffle_outcomes,
    shuffle_failure_rate,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V396aReport:
    seed_count: int
    shuffle_seed_count: int
    trajectory_count: int
    jittery_trajectory_count: int
    jittery_trajectory_ids: tuple[str, ...]
    jitter_rate: float
    affected_packages: tuple[str, ...]
    affected_dims: tuple[str, ...]
    max_state_delta: float
    shuffle_failure_rate: float
    shuffle_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "seed_count": self.seed_count,
            "shuffle_seed_count":
                self.shuffle_seed_count,
            "trajectory_count":
                self.trajectory_count,
            "jittery_trajectory_count":
                self.jittery_trajectory_count,
            "jittery_trajectory_ids":
                list(self.jittery_trajectory_ids),
            "jitter_rate": self.jitter_rate,
            "affected_packages":
                list(self.affected_packages),
            "affected_dims":
                list(self.affected_dims),
            "max_state_delta":
                self.max_state_delta,
            "shuffle_failure_rate":
                self.shuffle_failure_rate,
            "shuffle_outcomes":
                list(self.shuffle_outcomes),
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
        census().to_dict(),
        affected_packages(),
    )
    b = (
        census().to_dict(),
        affected_packages(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V396aReport:
    c = census()
    shuf = all_shuffle_outcomes()
    sfr = shuffle_failure_rate()
    pkgs = affected_packages()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif c.jitter_rate == 0.0 and sfr == 0.0:
        verdict = "NO_JITTER_DETECTED"
    elif c.jitter_rate > 0.0:
        verdict = "JITTER_CONFIRMED"
    else:
        verdict = "ORDER_JITTER_ONLY"

    rationale = (
        f"INFO: seed_count {c.seed_count} "
        f"(SEED_CENSUS = range 0..{c.seed_count})",
        f"INFO: shuffle_seed_count "
        f"{len(SHUFFLE_SEEDS)} "
        f"(SHUFFLE_SEEDS = range 0..{len(SHUFFLE_SEEDS)})",
        f"INFO: trajectory_count "
        f"{c.trajectory_count}",
        f"INFO: jittery_trajectory_count "
        f"{c.jittery_trajectory_count}",
        f"INFO: jittery_trajectory_ids "
        f"{list(c.jittery_trajectory_ids)}",
        f"INFO: jitter_rate {c.jitter_rate} "
        f"(jittery / total)",
        f"INFO: affected_packages "
        f"{list(pkgs)}",
        f"INFO: affected_dims "
        f"{list(c.affected_dims)}",
        f"INFO: max_state_delta "
        f"{c.max_state_delta}",
        f"INFO: shuffle_failure_rate {sfr}",
        f"INFO: shuffle_outcomes "
        f"{[o.to_dict() for o in shuf]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V396aReport(
        seed_count=c.seed_count,
        shuffle_seed_count=len(SHUFFLE_SEEDS),
        trajectory_count=c.trajectory_count,
        jittery_trajectory_count=(
            c.jittery_trajectory_count
        ),
        jittery_trajectory_ids=(
            c.jittery_trajectory_ids
        ),
        jitter_rate=c.jitter_rate,
        affected_packages=pkgs,
        affected_dims=c.affected_dims,
        max_state_delta=c.max_state_delta,
        shuffle_failure_rate=sfr,
        shuffle_outcomes=tuple(
            o.to_dict() for o in shuf
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_jitter_census_artifact(
) -> dict[str, object]:
    c = census()
    shuf = all_shuffle_outcomes()
    return {
        "schema_version":
            "v3_96a_jitter_census",
        "census": c.to_dict(),
        "affected_packages":
            list(affected_packages()),
        "shuffle_failure_rate":
            shuffle_failure_rate(),
        "shuffle_outcomes": [
            o.to_dict() for o in shuf
        ],
    }


__all__ = [
    "V396aReport",
    "build_jitter_census_artifact",
    "build_report",
]
