"""v27.2 - Research Convergence & Divergence report.

Pflichtmetriken (directive § v27.2):

* convergence_visibility
* conflict_structure_visibility
* method_cluster_visibility
* epistemic_neutrality
* replay_stability

Killerfrage: "Kann DESi emergente Forschungsstrukturen sichtbar
machen ohne Forschungsautoritaet zu beanspruchen?"

DESi surfaces convergences, conflict lines, method clusters and
emergent trends - strictly as structure. It detects trends; it
never evaluates them, names a winner or indicates a right
direction. Epistemic neutrality is audited explicitly.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .assumptions import shared_assumptions
from .clusters import (
    method_cluster_visibility, method_clusters,
    shared_method_clusters,
)
from .convergence import (
    convergence_visibility, emergent_trends,
)
from .divergence import (
    conflict_lines, conflict_structure_visibility,
    fragile_claims, reproducible_claims,
)

VERDICT_NEUTRAL = "STRUCTURE_VISIBLE_NEUTRAL"
VERDICT_AUTHORITY = "RESEARCH_AUTHORITY_LEAK"
VERDICT_HALT = "CONVERGENCE_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_NEUTRAL, VERDICT_AUTHORITY, VERDICT_HALT,
)

_FLOOR = 0.90
_NEUTRALITY_FLOOR = 0.95

# Markers of research authority that must never appear in any
# produced label or description (DESi structures, never judges).
_AUTHORITY_MARKERS: tuple[str, ...] = (
    "best", "worst", "winner", "superior", "inferior",
    "outperform", "wrong", "right direction", "should ",
    "recommend", "ranking", "rank ", "debunk", "better than",
    "impact score", "state-of-the-art",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _all_labels() -> str:
    parts: list[str] = []
    for kind, name, n in emergent_trends():
        parts.append(f"{kind} {name} appears in {n} papers")
    for a, ps in shared_assumptions():
        parts.append(f"assumption {a} shared by {', '.join(ps)}")
    for m, ps in shared_method_clusters().items():
        parts.append(f"method cluster {m}: {', '.join(ps)}")
    for l in conflict_lines():
        parts.append(
            f"conflict line {l.paper_a} vs {l.paper_b}"
        )
    return " | ".join(parts)


def authority_marker_hits() -> tuple[str, ...]:
    low = _all_labels().lower()
    return tuple(
        m.strip() for m in _AUTHORITY_MARKERS if m in low
    )


def epistemic_neutrality() -> float:
    """Fraction of neutrality checks passed: no authority marker
    in any label, and trends are frequency-only (no score), in
    [0, 1]."""
    checks = [
        not authority_marker_hits(),
        all(
            isinstance(n, int)
            for _, _, n in emergent_trends()
        ),
    ]
    return _round(sum(1 for c in checks if c) / len(checks))


def _signature() -> str:
    parts = [_all_labels()]
    parts += [str(convergence_visibility())]
    parts += [str(conflict_structure_visibility())]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    return 1.0 if _signature() == _signature() else 0.0


def _recommendation(
    *, replay: float, convergence: float, conflict: float,
    cluster: float, neutrality: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if neutrality < _NEUTRALITY_FLOOR:
        return VERDICT_AUTHORITY
    if (
        convergence < _FLOOR
        or conflict < _FLOOR
        or cluster < _FLOOR
    ):
        return VERDICT_HALT
    return VERDICT_NEUTRAL


@dataclass(frozen=True)
class V272Report:
    convergence_visibility: float
    conflict_structure_visibility: float
    method_cluster_visibility: float
    epistemic_neutrality: float
    replay_stability: float
    emergent_trend_count: int
    conflict_line_count: int
    fragile_claim_count: int
    reproducible_claim_count: int
    authority_marker_hits: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "convergence_visibility": self.convergence_visibility,
            "conflict_structure_visibility":
                self.conflict_structure_visibility,
            "method_cluster_visibility":
                self.method_cluster_visibility,
            "epistemic_neutrality": self.epistemic_neutrality,
            "replay_stability": self.replay_stability,
            "emergent_trend_count": self.emergent_trend_count,
            "conflict_line_count": self.conflict_line_count,
            "fragile_claim_count": self.fragile_claim_count,
            "reproducible_claim_count":
                self.reproducible_claim_count,
            "authority_marker_hits":
                list(self.authority_marker_hits),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V272Report:
    convergence = convergence_visibility()
    conflict = conflict_structure_visibility()
    cluster = method_cluster_visibility()
    neutrality = epistemic_neutrality()
    replay = replay_stability()
    hits = authority_marker_hits()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, convergence=convergence,
        conflict=conflict, cluster=cluster,
        neutrality=neutrality,
    )
    rationale = (
        f"INFO: {len(emergent_trends())} emergent trends "
        f"(frequency only); {len(shared_method_clusters())} "
        f"shared method clusters; {len(conflict_lines())} "
        f"conflict lines",
        "INFO: DESi detects structure; it names no winner, no "
        "best method and no right direction",
        f"{'PASS' if convergence >= _FLOOR else 'FAIL'}: "
        f"convergence_visibility {convergence} >= 0.90",
        f"{'PASS' if conflict >= _FLOOR else 'FAIL'}: "
        f"conflict_structure_visibility {conflict} >= 0.90",
        f"{'PASS' if cluster >= _FLOOR else 'FAIL'}: "
        f"method_cluster_visibility {cluster} >= 0.90",
        f"{'PASS' if neutrality >= _NEUTRALITY_FLOOR else 'FAIL'}: "
        f"epistemic_neutrality {neutrality} >= 0.95 "
        f"(authority markers {list(hits)})",
        f"INFO: fragile claims {len(fragile_claims())}; "
        f"reproducible claims {len(reproducible_claims())} "
        f"(by class, not judgement)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V272Report(
        convergence_visibility=convergence,
        conflict_structure_visibility=conflict,
        method_cluster_visibility=cluster,
        epistemic_neutrality=neutrality,
        replay_stability=replay,
        emergent_trend_count=len(emergent_trends()),
        conflict_line_count=len(conflict_lines()),
        fragile_claim_count=len(fragile_claims()),
        reproducible_claim_count=len(reproducible_claims()),
        authority_marker_hits=hits,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_convergence_artifact() -> dict[str, object]:
    return {
        "schema_version": "v27_2_research_convergence",
        "disclaimer": (
            "Surfaces convergences, conflict lines, method "
            "clusters and emergent trends across the corpus, "
            "strictly as structure. DESi detects trends but "
            "never evaluates them, names a winner or indicates a "
            "right direction; emergent trends are reported as "
            "frequencies, not scores. Epistemic neutrality is "
            "audited (no research-authority markers). "
            "Deterministic and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "shared_assumptions": [
            {"assumption": a, "papers": list(ps)}
            for a, ps in shared_assumptions()
        ],
        "shared_method_clusters": {
            m: list(ps)
            for m, ps in shared_method_clusters().items()
        },
        "method_clusters": {
            m: list(ps) for m, ps in method_clusters().items()
        },
        "emergent_trends": [
            {"kind": k, "name": n, "frequency": f}
            for k, n, f in emergent_trends()
        ],
        "conflict_lines": [l.to_dict() for l in conflict_lines()],
        "fragile_claims": list(fragile_claims()),
        "reproducible_claims": list(reproducible_claims()),
        "convergence_visibility": convergence_visibility(),
        "conflict_structure_visibility":
            conflict_structure_visibility(),
        "method_cluster_visibility": method_cluster_visibility(),
        "epistemic_neutrality": epistemic_neutrality(),
        "replay_stability": replay_stability(),
        "authority_marker_hits": list(authority_marker_hits()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_AUTHORITY",
    "VERDICT_HALT",
    "VERDICT_NEUTRAL",
    "V272Report",
    "authority_marker_hits",
    "build_convergence_artifact",
    "build_report",
    "epistemic_neutrality",
    "replay_stability",
]
