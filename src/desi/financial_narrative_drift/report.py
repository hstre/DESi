"""v15.1 - Longitudinal Narrative Drift report
(DAX retrospective).

Pflichtmetriken (directive § v15.1):

* narrative_drift
* semantic_reframing
* historical_consistency
* bridge_evolution_integrity
* replay_stability

Plus the ex-ante post-hoc validation
(ex_ante_drift_recall): did the longitudinal
narrative signals raise the later-troubled firms
before humans looked?

The closed output vocabulary is the phase-wide
audit-priority set (imported from v15.0). DESi
never concludes fraud, never rates, never advises.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.financial_governance import (
    ADVERSE_POST_HOC, AUDIT_PRIORITIES,
    AuditPriority, ELEVATED, PostHocLabel,
    severity_rank,
)

from .bridge_evolution import (
    bridge_evolution_integrity,
    bridge_evolution_integrity_firm,
)
from .lineage import (
    claim_lineage, historical_consistency,
    historical_consistency_firm,
)
from .semantic_shift import (
    semantic_reframing, semantic_reframing_firm,
)
from .trajectory import (
    THEMES, NarrativeTrajectory, narrative_drift,
    narrative_drift_firm, trajectories, years,
)

_AXIS_ELEVATED = 0.40
_AXIS_SEVERE = 0.50


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class DriftSignals:
    narrative_drift: float
    semantic_reframing: float
    inconsistency: float          # 1 - historical_consistency
    bridge_degradation: float     # 1 - bridge_evolution_integrity

    def as_list(self) -> list[float]:
        return [
            self.narrative_drift,
            self.semantic_reframing,
            self.inconsistency,
            self.bridge_degradation,
        ]


def drift_signals(
    tr: NarrativeTrajectory,
) -> DriftSignals:
    return DriftSignals(
        narrative_drift=narrative_drift_firm(tr),
        semantic_reframing=(
            semantic_reframing_firm(tr)
        ),
        inconsistency=_round(
            1.0 - historical_consistency_firm(tr),
        ),
        bridge_degradation=_round(
            1.0
            - bridge_evolution_integrity_firm(tr),
        ),
    )


def drift_priority_score(
    tr: NarrativeTrajectory,
) -> float:
    vals = drift_signals(tr).as_list()
    return _round(sum(vals) / len(vals))


def drift_priority_label(
    tr: NarrativeTrajectory,
) -> str:
    """Same depth+breadth mapping as v15.0, over
    the narrative-evolution axes."""
    sig = drift_signals(tr)
    score = drift_priority_score(tr)
    axes = sig.as_list()
    elevated = sum(
        1 for v in axes if v >= _AXIS_ELEVATED
    )
    severe = any(v >= _AXIS_SEVERE for v in axes)
    if score >= 0.45 and elevated >= 3:
        return (
            AuditPriority
            .GOVERNANCE_REVIEW_RECOMMENDED.value
        )
    if score >= 0.45 or elevated >= 3:
        return AuditPriority.HIGH_AUDIT_PRIORITY.value
    if score >= 0.25 or elevated >= 2 or severe:
        return (
            AuditPriority.MEDIUM_AUDIT_PRIORITY.value
        )
    return AuditPriority.LOW_AUDIT_PRIORITY.value


@dataclass(frozen=True)
class FirmDriftVerdict:
    firm_id: str
    sector: str
    priority_score: float
    priority_label: str
    narrative_drift: float
    semantic_reframing: float
    historical_consistency: float
    bridge_evolution_integrity: float
    post_hoc_label: str

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "sector": self.sector,
            "priority_score": self.priority_score,
            "priority_label": self.priority_label,
            "narrative_drift": self.narrative_drift,
            "semantic_reframing":
                self.semantic_reframing,
            "historical_consistency":
                self.historical_consistency,
            "bridge_evolution_integrity":
                self.bridge_evolution_integrity,
            "post_hoc_label": self.post_hoc_label,
        }


def firm_drift_verdicts() -> tuple[
    FirmDriftVerdict, ...
]:
    out: list[FirmDriftVerdict] = []
    for tr in trajectories():
        out.append(FirmDriftVerdict(
            firm_id=tr.firm_id,
            sector=tr.sector,
            priority_score=drift_priority_score(tr),
            priority_label=drift_priority_label(tr),
            narrative_drift=narrative_drift_firm(tr),
            semantic_reframing=(
                semantic_reframing_firm(tr)
            ),
            historical_consistency=(
                historical_consistency_firm(tr)
            ),
            bridge_evolution_integrity=(
                bridge_evolution_integrity_firm(tr)
            ),
            post_hoc_label=tr.post_hoc_label,
        ))
    out.sort(key=lambda v: v.firm_id)
    return tuple(out)


def corpus_priority_label() -> str:
    verdicts = firm_drift_verdicts()
    if not verdicts:
        return AuditPriority.UNRESOLVED.value
    return max(
        (v.priority_label for v in verdicts),
        key=severity_rank,
    )


# --- post-hoc validation (reads post_hoc_label) --
def ex_ante_drift_recall() -> float:
    """POST-HOC VALIDATION ONLY. Of the firms that
    later had an adverse outcome, what fraction did
    the longitudinal narrative signals flag as
    elevated (>= MEDIUM)?"""
    verdicts = firm_drift_verdicts()
    adverse = [
        v for v in verdicts
        if v.post_hoc_label in ADVERSE_POST_HOC
    ]
    if not adverse:
        return 1.0
    flagged = sum(
        1 for v in adverse
        if v.priority_label in ELEVATED
    )
    return _round(flagged / len(adverse))


def clean_firm_low_drift_rate() -> float:
    """POST-HOC VALIDATION ONLY. Of the firms with
    no later adverse outcome, what fraction stayed
    at LOW priority?"""
    verdicts = firm_drift_verdicts()
    clean = [
        v for v in verdicts
        if v.post_hoc_label == (
            PostHocLabel.NO_ADVERSE_EVENT.value
        )
    ]
    if not clean:
        return 1.0
    low = sum(
        1 for v in clean
        if v.priority_label == (
            AuditPriority.LOW_AUDIT_PRIORITY.value
        )
    )
    return _round(low / len(clean))


@dataclass(frozen=True)
class V151Report:
    firm_count: int
    year_count: int
    narrative_drift: float
    semantic_reframing: float
    historical_consistency: float
    bridge_evolution_integrity: float
    ex_ante_drift_recall: float
    clean_firm_low_drift_rate: float
    elevated_firms: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_count": self.firm_count,
            "year_count": self.year_count,
            "narrative_drift": self.narrative_drift,
            "semantic_reframing":
                self.semantic_reframing,
            "historical_consistency":
                self.historical_consistency,
            "bridge_evolution_integrity":
                self.bridge_evolution_integrity,
            "ex_ante_drift_recall":
                self.ex_ante_drift_recall,
            "clean_firm_low_drift_rate":
                self.clean_firm_low_drift_rate,
            "elevated_firms":
                list(self.elevated_firms),
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


def _metric_tuple() -> tuple[float, ...]:
    return (
        narrative_drift(),
        semantic_reframing(),
        historical_consistency(),
        bridge_evolution_integrity(),
        ex_ante_drift_recall(),
        clean_firm_low_drift_rate(),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == (
        _metric_tuple()
    ) else 0.0


def _elevated_firms() -> tuple[str, ...]:
    return tuple(
        v.firm_id for v in firm_drift_verdicts()
        if v.priority_label in ELEVATED
    )


def build_report() -> V151Report:
    nd = narrative_drift()
    sr = semantic_reframing()
    hc = historical_consistency()
    bei = bridge_evolution_integrity()
    recall = ex_ante_drift_recall()
    clean = clean_firm_low_drift_rate()
    elevated = _elevated_firms()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = (
        AuditPriority.UNRESOLVED.value
        if halt else corpus_priority_label()
    )
    rationale = (
        f"INFO: firm_count {len(trajectories())}; "
        f"year_count {len(years())}",
        "INFO: synthetic narrative trajectories "
        "over the v15.0 sector archetypes; NOT "
        "real companies",
        "INFO: DESi does NOT conclude fraud, does "
        "NOT rate, does NOT advise; output is "
        "audit-priority only",
        f"INFO: narrative_drift {nd}",
        f"INFO: semantic_reframing {sr}",
        f"INFO: historical_consistency {hc}",
        f"INFO: bridge_evolution_integrity {bei}",
        f"INFO: elevated_firms {list(elevated)}",
        f"{'PASS' if recall >= 0.90 else 'FAIL'}: "
        f"ex_ante_drift_recall {recall} >= 0.90 "
        f"(post-hoc validation only)",
        f"{'PASS' if clean >= 0.90 else 'FAIL'}: "
        f"clean_firm_low_drift_rate {clean} >= "
        f"0.90 (no false accusations)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V151Report(
        firm_count=len(trajectories()),
        year_count=len(years()),
        narrative_drift=nd,
        semantic_reframing=sr,
        historical_consistency=hc,
        bridge_evolution_integrity=bei,
        ex_ante_drift_recall=recall,
        clean_firm_low_drift_rate=clean,
        elevated_firms=elevated,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_narrative_drift_artifact() -> dict[
    str, object
]:
    return {
        "schema_version":
            "v15_1_longitudinal_narrative_drift",
        "disclaimer": (
            "Synthetic longitudinal narrative "
            "trajectories over the v15.0 sector "
            "archetypes; NOT real audited "
            "disclosures and NOT named real "
            "companies. DESi does NOT conclude "
            "fraud, does NOT rate, does NOT give "
            "investment advice - output is audit-"
            "priority only. Post-hoc labels are "
            "used solely as validation, never as "
            "scoring input."
        ),
        "audit_priorities": list(AUDIT_PRIORITIES),
        "themes": list(THEMES),
        "years": list(years()),
        "trajectories": [
            tr.to_dict() for tr in trajectories()
        ],
        "claim_lineage": [
            c.to_dict() for c in claim_lineage()
        ],
        "firm_drift_verdicts": [
            v.to_dict()
            for v in firm_drift_verdicts()
        ],
        "narrative_drift": narrative_drift(),
        "semantic_reframing": semantic_reframing(),
        "historical_consistency":
            historical_consistency(),
        "bridge_evolution_integrity":
            bridge_evolution_integrity(),
        "ex_ante_drift_recall":
            ex_ante_drift_recall(),
        "clean_firm_low_drift_rate":
            clean_firm_low_drift_rate(),
        "corpus_priority_label":
            corpus_priority_label(),
    }


__all__ = [
    "DriftSignals",
    "FirmDriftVerdict",
    "V151Report",
    "build_narrative_drift_artifact",
    "build_report",
    "clean_firm_low_drift_rate",
    "corpus_priority_label",
    "drift_priority_label",
    "drift_priority_score",
    "drift_signals",
    "ex_ante_drift_recall",
    "firm_drift_verdicts",
]
