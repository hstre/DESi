"""v3.96b - root cause isolation report.

Pflichtmetriken (directive § v3.96b):

* ``root_cause_found``
* ``unstable_function``
* ``unstable_container``
* ``ordering_dependency``
* ``replay_stability``

Killerfrage: "Wo entsteht die Nichtdeterministik?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .containers import (
    container_kind_counts,
    high_risk_hit_count,
    total_hit_count,
    unstable_container_kinds,
)
from .ordering import (
    OrderingFix,
    all_classifications,
    unstable_functions,
)
from .trace import (
    all_trace_hits, builtin_hash_hits,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V396bReport:
    total_hit_count: int
    high_risk_hit_count: int
    root_cause_found: bool
    unstable_function: tuple[str, ...]
    unstable_container: tuple[str, ...]
    ordering_dependency: tuple[str, ...]
    builtin_hash_hits: tuple[dict, ...]
    container_kind_counts: tuple[dict, ...]
    classifications: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "total_hit_count":
                self.total_hit_count,
            "high_risk_hit_count":
                self.high_risk_hit_count,
            "root_cause_found":
                self.root_cause_found,
            "unstable_function":
                list(self.unstable_function),
            "unstable_container":
                list(self.unstable_container),
            "ordering_dependency":
                list(self.ordering_dependency),
            "builtin_hash_hits":
                list(self.builtin_hash_hits),
            "container_kind_counts":
                list(self.container_kind_counts),
            "classifications":
                list(self.classifications),
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
    a = [h.to_dict() for h in all_trace_hits()]
    b = [h.to_dict() for h in all_trace_hits()]
    return 1.0 if a == b else 0.0


def build_report() -> V396bReport:
    hits = all_trace_hits()
    bh = builtin_hash_hits()
    ufs = unstable_functions()
    uck = unstable_container_kinds()
    classes = all_classifications()
    counts = container_kind_counts()
    replay = _replay_stability()

    root_cause = len(bh) > 0
    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif root_cause:
        verdict = "ROOT_CAUSE_IDENTIFIED"
    else:
        verdict = "ROOT_CAUSE_NOT_FOUND"

    fixes = tuple(sorted({
        c.suggested_fix for c in classes
    }))

    rationale = (
        f"INFO: total_hit_count "
        f"{total_hit_count()}",
        f"INFO: high_risk_hit_count "
        f"{high_risk_hit_count()}",
        f"{'PASS' if root_cause else 'FAIL'}: "
        f"root_cause_found {root_cause}",
        f"INFO: unstable_function "
        f"{list(ufs)}",
        f"INFO: unstable_container "
        f"{list(uck)}",
        f"INFO: ordering_dependency "
        f"{list(fixes)}",
        f"INFO: builtin_hash_hits "
        f"{[h.to_dict() for h in bh]}",
        f"INFO: container_kind_counts "
        f"{counts}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V396bReport(
        total_hit_count=total_hit_count(),
        high_risk_hit_count=high_risk_hit_count(),
        root_cause_found=root_cause,
        unstable_function=ufs,
        unstable_container=uck,
        ordering_dependency=fixes,
        builtin_hash_hits=tuple(
            h.to_dict() for h in bh
        ),
        container_kind_counts=tuple(
            {"kind": k, "count": v}
            for k, v in sorted(counts.items())
        ),
        classifications=tuple(
            c.to_dict() for c in classes
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_root_cause_trace_artifact(
) -> dict[str, object]:
    hits = all_trace_hits()
    classes = all_classifications()
    return {
        "schema_version":
            "v3_96b_root_cause_trace",
        "total_hit_count": len(hits),
        "high_risk_hit_count":
            high_risk_hit_count(),
        "all_hits": [h.to_dict() for h in hits],
        "classifications": [
            c.to_dict() for c in classes
        ],
        "builtin_hash_hits": [
            h.to_dict()
            for h in builtin_hash_hits()
        ],
        "container_kind_counts": [
            {"kind": k, "count": v}
            for k, v in sorted(
                container_kind_counts().items(),
            )
        ],
    }


__all__ = [
    "V396bReport",
    "build_report",
    "build_root_cause_trace_artifact",
]
