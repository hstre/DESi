"""v11.0 — search-redundancy audit report.

Five Pflichtmetriken:

* ``redundant_branch_rate``
* ``low_information_rate``
* ``forced_line_detection``
* ``replay_reuse``
* ``replay_stability``

Killerfrage: "Wie viel der Schachsuche ist
epistemisch redundant?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .branching import (
    critical_branch_count,
    mean_branching_factor,
    no_critical_branch_dropped,
    verdict_distribution,
)
from .positions import (
    POSITION_KINDS, fixture, kind_counts,
    total_branch_count,
)
from .redundancy import (
    BRANCH_VERDICTS, classified_branches,
    forced_line_detection,
    low_information_rate,
    redundant_branch_rate, replay_reuse,
)


@dataclass(frozen=True)
class V110Report:
    position_count: int
    branch_count: int
    mean_branching_factor: float
    redundant_branch_rate: float
    low_information_rate: float
    forced_line_detection: float
    replay_reuse: float
    critical_branch_count: int
    no_critical_dropped: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "position_count":
                self.position_count,
            "branch_count": self.branch_count,
            "mean_branching_factor":
                self.mean_branching_factor,
            "redundant_branch_rate":
                self.redundant_branch_rate,
            "low_information_rate":
                self.low_information_rate,
            "forced_line_detection":
                self.forced_line_detection,
            "replay_reuse": self.replay_reuse,
            "critical_branch_count":
                self.critical_branch_count,
            "no_critical_dropped":
                self.no_critical_dropped,
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
        redundant_branch_rate(),
        low_information_rate(),
        forced_line_detection(),
        replay_reuse(),
    )
    b = (
        redundant_branch_rate(),
        low_information_rate(),
        forced_line_detection(),
        replay_reuse(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, rbr: float, lir: float,
    fld: float, nocrit: bool,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if not nocrit:
        return "REDUNDANCY_CRITICAL_DROP"
    if fld < 0.90:
        return "REDUNDANCY_FORCED_MISS"
    if rbr < 0.80:
        return "REDUNDANCY_DETECTION_WEAK"
    if lir < 0.20:
        return "REDUNDANCY_NEGLIGIBLE"
    return "REDUNDANCY_AUDITED"


def build_report() -> V110Report:
    rbr = redundant_branch_rate()
    lir = low_information_rate()
    fld = forced_line_detection()
    rr = replay_reuse()
    nocrit = no_critical_branch_dropped()
    cc = critical_branch_count()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, rbr=rbr, lir=lir,
        fld=fld, nocrit=nocrit,
    )
    rationale = (
        f"INFO: position_count "
        f"{len(fixture())}",
        f"INFO: branch_count "
        f"{total_branch_count()}",
        f"INFO: kind_counts {kind_counts()}",
        f"INFO: mean_branching_factor "
        f"{mean_branching_factor()}",
        f"INFO: verdict_distribution "
        f"{verdict_distribution()}",
        f"INFO: critical_branch_count {cc}",
        f"{'PASS' if rbr >= 0.80 else 'FAIL'}: "
        f"redundant_branch_rate {rbr} >= 0.80",
        f"INFO: low_information_rate {lir}",
        f"{'PASS' if fld >= 0.90 else 'FAIL'}: "
        f"forced_line_detection {fld} >= 0.90",
        f"INFO: replay_reuse {rr}",
        f"{'PASS' if nocrit else 'FAIL'}: "
        f"no_critical_branch_dropped",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V110Report(
        position_count=len(fixture()),
        branch_count=total_branch_count(),
        mean_branching_factor=(
            mean_branching_factor()
        ),
        redundant_branch_rate=rbr,
        low_information_rate=lir,
        forced_line_detection=fld,
        replay_reuse=rr,
        critical_branch_count=cc,
        no_critical_dropped=nocrit,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_redundancy_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v11_0_search_redundancy",
        "position_kinds":
            list(POSITION_KINDS),
        "branch_verdicts":
            list(BRANCH_VERDICTS),
        "position_count": len(fixture()),
        "branch_count": total_branch_count(),
        "kind_counts": kind_counts(),
        "verdict_distribution":
            verdict_distribution(),
        "positions": [
            p.to_dict() for p in fixture()
        ],
        "classified_branches": [
            c.to_dict()
            for c in classified_branches()
        ],
        "mean_branching_factor":
            mean_branching_factor(),
        "redundant_branch_rate":
            redundant_branch_rate(),
        "low_information_rate":
            low_information_rate(),
        "forced_line_detection":
            forced_line_detection(),
        "replay_reuse": replay_reuse(),
        "critical_branch_count":
            critical_branch_count(),
        "no_critical_dropped":
            no_critical_branch_dropped(),
    }


__all__ = [
    "V110Report",
    "build_redundancy_artifact",
    "build_report",
]
