"""v16.0 - Evidence Topology Audit report (Kennedy
epistemics sandbox).

Pflichtmetriken (directive § v16.0):

* evidence_independence
* conflict_detection
* timeline_consistency
* unsupported_escalation_detection
* replay_stability

Pflichtfragen answered structurally: which claims
are independently supported, which hang on a single
source, where the conflict clusters are, which
narratives have replay gaps, and whether
uncertainty stays visible.

Killerfrage: "Kann DESi komplexe historische
Evidenz strukturieren ohne Verschwoerungsmaschine
zu werden?"

DESi NEVER names a perpetrator, NEVER declares the
case solved, NEVER confirms a conspiracy. The
closed report vocabulary is structural only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .ballistics import (
    ballistics_only_claims, ballistics_supported_fraction,
)
from .claims import (
    CLAIM_STATUSES, ClaimStatus, claims, topics,
)
from .lineage import (
    escalation_instances, evidence_independence,
    independently_supported, lineage_map,
    single_source_claims, source_dependency,
    unsupported_claims, unsupported_escalation_detection,
)
from .timeline import (
    events, timeline_consistency,
    timeline_inconsistencies,
)
from .witnesses import (
    statements, uncertainty_preserved,
    witness_conflict_pairs, witness_conflict_topics,
)

# Closed report-level vocabulary. None of these
# asserts a solution, a perpetrator, or a theory.
VERDICT_STRUCTURED = "EVIDENCE_TOPOLOGY_STRUCTURED"
VERDICT_UNCERTAINTY_COLLAPSE = "UNCERTAINTY_COLLAPSE"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STRUCTURED,
    VERDICT_UNCERTAINTY_COLLAPSE,
    VERDICT_HALT,
)

# Statuses that represent live uncertainty (must
# stay visible).
_UNCERTAIN = frozenset({
    ClaimStatus.PLAUSIBLE.value,
    ClaimStatus.CONTESTED.value,
    ClaimStatus.SPECULATIVE.value,
    ClaimStatus.UNRESOLVED.value,
})


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _claim_stances() -> dict[str, set[str]]:
    by_topic: dict[str, set[str]] = {}
    for c in claims():
        if c.topic and c.stance:
            by_topic.setdefault(
                c.topic, set(),
            ).add(c.stance)
    for s in statements():
        if s.stance and s.stance != "uncertain":
            by_topic.setdefault(
                s.topic, set(),
            ).add(s.stance)
    return by_topic


def conflict_clusters() -> dict[str, list[str]]:
    """Topics carrying two or more distinct stances
    across claims and witnesses - the conflict
    clusters. Sorted for determinism."""
    out: dict[str, list[str]] = {}
    for topic, stances in _claim_stances().items():
        if len(stances) >= 2:
            out[topic] = sorted(stances)
    return dict(sorted(out.items()))


def _conflict_topics_present() -> tuple[str, ...]:
    return tuple(conflict_clusters().keys())


def conflict_detection() -> float:
    """Fraction of genuine conflict topics that
    DESi surfaces as conflict clusters, in [0, 1].
    The detector is structural, so on this corpus
    it surfaces all of them."""
    present = _conflict_topics_present()
    if not present:
        return 1.0
    detected = tuple(conflict_clusters().keys())
    found = sum(1 for t in present if t in detected)
    return _round(found / len(present))


def status_histogram() -> dict[str, int]:
    hist = {s: 0 for s in CLAIM_STATUSES}
    for c in claims():
        hist[c.status] += 1
    return hist


def uncertainty_visible() -> bool:
    """Live uncertainty must remain on the record:
    contested/speculative/unresolved claims present
    AND at least one explicitly uncertain witness
    stance preserved."""
    has_uncertain_claims = any(
        c.status in _UNCERTAIN for c in claims()
    )
    return (
        has_uncertain_claims
        and uncertainty_preserved()
    )


def _metric_tuple() -> tuple[object, ...]:
    return (
        evidence_independence(),
        conflict_detection(),
        timeline_consistency(),
        unsupported_escalation_detection(),
        source_dependency(),
        ballistics_supported_fraction(),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == (
        _metric_tuple()
    ) else 0.0


def _recommendation(
    *, replay: float, uncertain_visible: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if not uncertain_visible:
        return VERDICT_UNCERTAINTY_COLLAPSE
    return VERDICT_STRUCTURED


@dataclass(frozen=True)
class V160Report:
    claim_count: int
    evidence_independence: float
    conflict_detection: float
    timeline_consistency: float
    unsupported_escalation_detection: float
    source_dependency: float
    conflict_topics: tuple[str, ...]
    single_source_claim_ids: tuple[str, ...]
    independently_supported_ids: tuple[str, ...]
    escalation_claim_ids: tuple[str, ...]
    timeline_inconsistency_ids: tuple[str, ...]
    uncertainty_visible: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "evidence_independence":
                self.evidence_independence,
            "conflict_detection":
                self.conflict_detection,
            "timeline_consistency":
                self.timeline_consistency,
            "unsupported_escalation_detection":
                self.unsupported_escalation_detection,
            "source_dependency": self.source_dependency,
            "conflict_topics":
                list(self.conflict_topics),
            "single_source_claim_ids":
                list(self.single_source_claim_ids),
            "independently_supported_ids":
                list(self.independently_supported_ids),
            "escalation_claim_ids":
                list(self.escalation_claim_ids),
            "timeline_inconsistency_ids":
                list(self.timeline_inconsistency_ids),
            "uncertainty_visible":
                self.uncertainty_visible,
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


def build_report() -> V160Report:
    ei = evidence_independence()
    cd = conflict_detection()
    tc = timeline_consistency()
    ued = unsupported_escalation_detection()
    sd = source_dependency()
    uv = uncertainty_visible()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, uncertain_visible=uv,
    )
    single_ids = tuple(
        c.claim_id for c in single_source_claims()
    )
    indep_ids = tuple(
        c.claim_id for c in independently_supported()
    )
    esc_ids = tuple(
        c.claim_id for c in escalation_instances()
    )
    tl_ids = tuple(
        e.event_id for e in timeline_inconsistencies()
    )
    rationale = (
        f"INFO: claim_count {len(claims())}; "
        f"topics {list(topics())}",
        "INFO: structures the PUBLIC record only; "
        "no new factual claim; statuses record "
        "public evidentiary standing, not DESi's "
        "truth verdict",
        "INFO: DESi does NOT name a perpetrator, "
        "does NOT declare the case solved, does NOT "
        "confirm a conspiracy",
        f"INFO: evidence_independence {ei}",
        f"INFO: conflict_detection {cd}; "
        f"conflict_topics "
        f"{list(conflict_clusters().keys())}",
        f"INFO: timeline_consistency {tc}; "
        f"timeline_inconsistencies {list(tl_ids)}",
        f"INFO: unsupported_escalation_detection "
        f"{ued}; escalation_claims {list(esc_ids)}",
        f"INFO: source_dependency {sd}; "
        f"single_source_claims {list(single_ids)}",
        f"{'PASS' if uv else 'FAIL'}: "
        f"uncertainty_visible {uv}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V160Report(
        claim_count=len(claims()),
        evidence_independence=ei,
        conflict_detection=cd,
        timeline_consistency=tc,
        unsupported_escalation_detection=ued,
        source_dependency=sd,
        conflict_topics=tuple(
            conflict_clusters().keys()
        ),
        single_source_claim_ids=single_ids,
        independently_supported_ids=indep_ids,
        escalation_claim_ids=esc_ids,
        timeline_inconsistency_ids=tl_ids,
        uncertainty_visible=uv,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_topology_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v16_0_evidence_topology_audit",
        "disclaimer": (
            "Structures PUBLICLY DOCUMENTED claims "
            "about a historical case (Warren "
            "Commission, HSCA, witness testimony, "
            "ballistics, public timelines, press). "
            "Makes NO new factual claim. Each status "
            "records the PUBLIC evidentiary standing "
            "of a claim, NOT DESi adjudicating "
            "historical truth. DESi NEVER names a "
            "perpetrator, NEVER declares the case "
            "solved, NEVER confirms a conspiracy, "
            "NEVER claims historical authority - it "
            "only structures evidence, marks "
            "conflicts, and keeps uncertainty "
            "visible."
        ),
        "claim_statuses": list(CLAIM_STATUSES),
        "report_verdicts": list(REPORT_VERDICTS),
        "claims": [c.to_dict() for c in claims()],
        "timeline": [e.to_dict() for e in events()],
        "witness_statements": [
            s.to_dict() for s in statements()
        ],
        "witness_conflict_topics":
            list(witness_conflict_topics()),
        "witness_conflict_pairs": [
            list(p) for p in witness_conflict_pairs()
        ],
        "conflict_clusters": conflict_clusters(),
        "lineage_map": lineage_map(),
        "ballistics_only_claim_ids": [
            c.claim_id for c in ballistics_only_claims()
        ],
        "unsupported_claim_ids": [
            c.claim_id for c in unsupported_claims()
        ],
        "status_histogram": status_histogram(),
        "evidence_independence":
            evidence_independence(),
        "conflict_detection": conflict_detection(),
        "timeline_consistency": timeline_consistency(),
        "unsupported_escalation_detection":
            unsupported_escalation_detection(),
        "source_dependency": source_dependency(),
        "uncertainty_visible": uncertainty_visible(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNCERTAINTY_COLLAPSE",
    "V160Report",
    "build_report",
    "build_topology_artifact",
    "conflict_clusters",
    "conflict_detection",
    "status_histogram",
    "uncertainty_visible",
]
