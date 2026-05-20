"""v16.1 - Narrative Competition report (Kennedy
epistemics sandbox).

Pflichtmetriken (directive § v16.1):

* bridge_pressure
* source_dependency
* speculative_growth
* cross_narrative_overlap
* replay_stability

Pflichtfragen answered structurally: which
narratives need the most unsupported bridges, which
have high source dependence, where speculation
grows, which claims stay robust across narratives,
and whether governance stays stable.

Killerfrage: "Kann DESi Narrative analysieren ohne
selbst ein Narrativ zu bevorzugen?"

DESi COMPARES narratives. It NEVER prefers one,
ranks one as true, or crowns a winner. There is by
design NO 'true_narrative' output.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.criminal_epistemics import ClaimStatus, by_id

from .bridge_analysis import (
    bridge_pressure, bridge_pressure_by_narrative,
    most_bridge_dependent,
)
from .causal_escalation import (
    most_speculative, speculative_growth,
    speculative_growth_by_narrative,
)
from .narratives import (
    NARRATIVE_IDS, narratives,
)
from .source_dependence import (
    most_source_dependent, source_dependency,
    source_dependency_by_narrative,
)

# Closed report-level vocabulary. None of these
# names a winning narrative.
VERDICT_NO_PREFERENCE = "NARRATIVES_STRUCTURED_NO_PREFERENCE"
VERDICT_PREFERENCE_DETECTED = "NARRATIVE_PREFERENCE_DETECTED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_NO_PREFERENCE,
    VERDICT_PREFERENCE_DETECTED,
    VERDICT_HALT,
)

# A narrative conclusion at or above this would be
# a promotion to settled truth - which DESi must
# never do for a contested historical question.
_PROMOTED = frozenset({ClaimStatus.VERIFIED.value})


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def robust_claims() -> tuple[str, ...]:
    """Claims appearing in EVERY narrative - the
    bedrock all framings share (Pflichtfrage 4)."""
    sets = [set(n.claim_ids) for n in narratives()]
    if not sets:
        return ()
    inter = set.intersection(*sets)
    return tuple(sorted(inter))


def _union_claims() -> tuple[str, ...]:
    out: set[str] = set()
    for n in narratives():
        out |= set(n.claim_ids)
    return tuple(sorted(out))


def cross_narrative_overlap() -> float:
    """Jaccard overlap across all narratives:
    |shared| / |union|, in [0, 1]. The shared core
    is the robust, narrative-independent evidence."""
    union = _union_claims()
    if not union:
        return 0.0
    return _round(len(robust_claims()) / len(union))


def no_preferred_narrative() -> bool:
    """Governance invariant: DESi must not promote
    any narrative's conclusion to settled truth.
    Holds iff no narrative conclusion is VERIFIED -
    i.e. every contested framing stays contested."""
    return all(
        by_id(n.conclusion).status not in _PROMOTED
        for n in narratives()
    )


def _metric_tuple() -> tuple[object, ...]:
    return (
        bridge_pressure(),
        source_dependency(),
        speculative_growth(),
        cross_narrative_overlap(),
        tuple(sorted(
            bridge_pressure_by_narrative().items()
        )),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == (
        _metric_tuple()
    ) else 0.0


def _recommendation(
    *, replay: float, no_preference: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if not no_preference:
        return VERDICT_PREFERENCE_DETECTED
    return VERDICT_NO_PREFERENCE


@dataclass(frozen=True)
class V161Report:
    narrative_count: int
    bridge_pressure: float
    source_dependency: float
    speculative_growth: float
    cross_narrative_overlap: float
    bridge_pressure_by_narrative: dict
    source_dependency_by_narrative: dict
    speculative_growth_by_narrative: dict
    robust_claims: tuple[str, ...]
    most_bridge_dependent: str
    most_source_dependent: str
    most_speculative: str
    no_preferred_narrative: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "narrative_count": self.narrative_count,
            "bridge_pressure": self.bridge_pressure,
            "source_dependency": self.source_dependency,
            "speculative_growth":
                self.speculative_growth,
            "cross_narrative_overlap":
                self.cross_narrative_overlap,
            "bridge_pressure_by_narrative":
                self.bridge_pressure_by_narrative,
            "source_dependency_by_narrative":
                self.source_dependency_by_narrative,
            "speculative_growth_by_narrative":
                self.speculative_growth_by_narrative,
            "robust_claims": list(self.robust_claims),
            "most_bridge_dependent":
                self.most_bridge_dependent,
            "most_source_dependent":
                self.most_source_dependent,
            "most_speculative": self.most_speculative,
            "no_preferred_narrative":
                self.no_preferred_narrative,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V161Report:
    bp = bridge_pressure()
    sd = source_dependency()
    sg = speculative_growth()
    cno = cross_narrative_overlap()
    nopref = no_preferred_narrative()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, no_preference=nopref,
    )
    rationale = (
        f"INFO: narrative_count {len(narratives())}; "
        f"narratives {list(NARRATIVE_IDS)}",
        "INFO: compares publicly documented framings "
        "only; DESi prefers NO narrative and crowns "
        "NO winner",
        "INFO: high bridge_pressure / source_"
        "dependency / speculative_growth are "
        "STRUCTURAL observations, not verdicts of "
        "falsehood",
        f"INFO: bridge_pressure {bp}; most_bridge_"
        f"dependent {most_bridge_dependent()}",
        f"INFO: source_dependency {sd}; most_source_"
        f"dependent {most_source_dependent()}",
        f"INFO: speculative_growth {sg}; most_"
        f"speculative {most_speculative()}",
        f"INFO: cross_narrative_overlap {cno}; "
        f"robust_claims {list(robust_claims())}",
        f"{'PASS' if nopref else 'FAIL'}: "
        f"no_preferred_narrative {nopref}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V161Report(
        narrative_count=len(narratives()),
        bridge_pressure=bp,
        source_dependency=sd,
        speculative_growth=sg,
        cross_narrative_overlap=cno,
        bridge_pressure_by_narrative=(
            bridge_pressure_by_narrative()
        ),
        source_dependency_by_narrative=(
            source_dependency_by_narrative()
        ),
        speculative_growth_by_narrative=(
            speculative_growth_by_narrative()
        ),
        robust_claims=robust_claims(),
        most_bridge_dependent=most_bridge_dependent(),
        most_source_dependent=most_source_dependent(),
        most_speculative=most_speculative(),
        no_preferred_narrative=nopref,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_narratives_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v16_1_narrative_competition",
        "disclaimer": (
            "Compares PUBLICLY DOCUMENTED framings "
            "of a historical case (lone-gunman, "
            "institutional, multi-actor, alternative "
            "reconstruction). DESi prefers NO "
            "narrative, ranks NONE as true, crowns "
            "NO winner, and makes no new factual "
            "claim. High bridge pressure / source "
            "dependency / speculative growth are "
            "structural descriptions, never verdicts "
            "of truth or falsehood. There is by "
            "design no 'true_narrative' output."
        ),
        "narrative_ids": list(NARRATIVE_IDS),
        "report_verdicts": list(REPORT_VERDICTS),
        "narratives": [
            n.to_dict() for n in narratives()
        ],
        "bridge_pressure_by_narrative":
            bridge_pressure_by_narrative(),
        "source_dependency_by_narrative":
            source_dependency_by_narrative(),
        "speculative_growth_by_narrative":
            speculative_growth_by_narrative(),
        "robust_claims": list(robust_claims()),
        "bridge_pressure": bridge_pressure(),
        "source_dependency": source_dependency(),
        "speculative_growth": speculative_growth(),
        "cross_narrative_overlap":
            cross_narrative_overlap(),
        "no_preferred_narrative":
            no_preferred_narrative(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_NO_PREFERENCE",
    "VERDICT_PREFERENCE_DETECTED",
    "V161Report",
    "build_narratives_artifact",
    "build_report",
    "cross_narrative_overlap",
    "no_preferred_narrative",
    "robust_claims",
]
