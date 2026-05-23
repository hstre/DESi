"""v15.2 - Financial Blindness Pools report
(DAX retrospective).

Pflichtmetriken (directive § v15.2):

* blindness_pool_count
* risk_family_detection
* structural_redundancy
* recoverability_signal
* replay_stability

Goal: find EPISTEMIC STRUCTURE patterns, NOT
industry classification. The clustering groups
firms by shared blind-spot shape; the multi-member
pool deliberately spans several sectors.

Plus the ex-ante post-hoc validation
(ex_ante_pool_recall): did the structural pools
place the later-troubled firms in a non-sound risk
family? The closed output vocabulary is the phase-
wide audit-priority set. DESi never concludes
fraud, never rates, never advises.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from desi.financial_governance import (
    ADVERSE_POST_HOC, AUDIT_PRIORITIES,
    AuditPriority, ELEVATED, PostHocLabel,
    by_id as _firm_by_id, severity_rank,
)

from .clusters import (
    blindness_pool_count, multi_member_pools,
    pools,
)
from .redundancy import (
    recoverability_signal, redundant_firm_fraction,
    structural_redundancy,
)
from .risk_families import (
    RISK_FAMILIES, RiskFamily, detected_families,
    family_assignments, firm_family_count,
    firm_risk_families, risk_family_detection,
)
from .trajectory_similarity import (
    SIGNATURE_AXES, signatures,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def pool_priority_label(firm_id: str) -> str:
    """Audit priority from the BREADTH of a firm's
    blind-spot structure (how many distinct risk
    families it carries)."""
    n = firm_family_count(firm_id)
    if n >= 4:
        return (
            AuditPriority
            .GOVERNANCE_REVIEW_RECOMMENDED.value
        )
    if n >= 2:
        return AuditPriority.HIGH_AUDIT_PRIORITY.value
    if n == 1:
        return (
            AuditPriority.MEDIUM_AUDIT_PRIORITY.value
        )
    return AuditPriority.LOW_AUDIT_PRIORITY.value


@dataclass(frozen=True)
class FirmPoolVerdict:
    firm_id: str
    sector: str
    pool_id: int
    risk_families: tuple[str, ...]
    family_count: int
    priority_label: str
    post_hoc_label: str

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "sector": self.sector,
            "pool_id": self.pool_id,
            "risk_families": list(self.risk_families),
            "family_count": self.family_count,
            "priority_label": self.priority_label,
            "post_hoc_label": self.post_hoc_label,
        }


def _pool_id_of(firm_id: str) -> int:
    for p in pools():
        if firm_id in p.members:
            return p.pool_id
    return -1


@lru_cache(maxsize=1)
def firm_pool_verdicts() -> tuple[FirmPoolVerdict, ...]:
    out: list[FirmPoolVerdict] = []
    for sig in signatures():
        fid = sig.firm_id
        firm = _firm_by_id(fid)
        out.append(FirmPoolVerdict(
            firm_id=fid,
            sector=sig.sector,
            pool_id=_pool_id_of(fid),
            risk_families=firm_risk_families(fid),
            family_count=firm_family_count(fid),
            priority_label=pool_priority_label(fid),
            post_hoc_label=firm.post_hoc_label,
        ))
    out.sort(key=lambda v: v.firm_id)
    return tuple(out)


def corpus_priority_label() -> str:
    verdicts = firm_pool_verdicts()
    if not verdicts:
        return AuditPriority.UNRESOLVED.value
    return max(
        (v.priority_label for v in verdicts),
        key=severity_rank,
    )


# --- post-hoc validation (reads post_hoc_label) --
def ex_ante_pool_recall() -> float:
    """POST-HOC VALIDATION ONLY. Of the firms that
    later had an adverse outcome, what fraction did
    the structural pools place in a non-sound risk
    family (>= MEDIUM)?"""
    verdicts = firm_pool_verdicts()
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


def clean_firm_sound_rate() -> float:
    """POST-HOC VALIDATION ONLY. Of the firms with
    no later adverse outcome, what fraction were
    placed as STRUCTURALLY_SOUND (LOW)?"""
    verdicts = firm_pool_verdicts()
    clean = [
        v for v in verdicts
        if v.post_hoc_label == (
            PostHocLabel.NO_ADVERSE_EVENT.value
        )
    ]
    if not clean:
        return 1.0
    sound = sum(
        1 for v in clean
        if v.priority_label == (
            AuditPriority.LOW_AUDIT_PRIORITY.value
        )
    )
    return _round(sound / len(clean))


@dataclass(frozen=True)
class V152Report:
    firm_count: int
    blindness_pool_count: int
    cross_sector_pool_count: int
    risk_family_detection: float
    structural_redundancy: float
    recoverability_signal: float
    redundant_firm_fraction: float
    ex_ante_pool_recall: float
    clean_firm_sound_rate: float
    elevated_firms: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_count": self.firm_count,
            "blindness_pool_count":
                self.blindness_pool_count,
            "cross_sector_pool_count":
                self.cross_sector_pool_count,
            "risk_family_detection":
                self.risk_family_detection,
            "structural_redundancy":
                self.structural_redundancy,
            "recoverability_signal":
                self.recoverability_signal,
            "redundant_firm_fraction":
                self.redundant_firm_fraction,
            "ex_ante_pool_recall":
                self.ex_ante_pool_recall,
            "clean_firm_sound_rate":
                self.clean_firm_sound_rate,
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


def _cross_sector_pool_count() -> int:
    return sum(
        1 for p in pools() if p.is_cross_sector
    )


def _metric_tuple() -> tuple[object, ...]:
    return (
        blindness_pool_count(),
        risk_family_detection(),
        structural_redundancy(),
        recoverability_signal(),
        ex_ante_pool_recall(),
        clean_firm_sound_rate(),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == (
        _metric_tuple()
    ) else 0.0


def _elevated_firms() -> tuple[str, ...]:
    return tuple(
        v.firm_id for v in firm_pool_verdicts()
        if v.priority_label in ELEVATED
    )


def build_report() -> V152Report:
    bpc = blindness_pool_count()
    rfd = risk_family_detection()
    sr = structural_redundancy()
    rec = recoverability_signal()
    rff = redundant_firm_fraction()
    recall = ex_ante_pool_recall()
    clean = clean_firm_sound_rate()
    elevated = _elevated_firms()
    xsp = _cross_sector_pool_count()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = (
        AuditPriority.UNRESOLVED.value
        if halt else corpus_priority_label()
    )
    rationale = (
        f"INFO: firm_count {len(signatures())}; "
        f"blindness_pool_count {bpc}",
        "INFO: pools are built from epistemic "
        "structure only, NOT sector; "
        f"cross_sector_pool_count {xsp}",
        "INFO: DESi does NOT conclude fraud, does "
        "NOT rate, does NOT advise; output is "
        "audit-priority only",
        f"INFO: detected_families "
        f"{list(detected_families())}",
        f"INFO: risk_family_detection {rfd}",
        f"INFO: structural_redundancy {sr}; "
        f"redundant_firm_fraction {rff}",
        f"INFO: recoverability_signal {rec}",
        f"INFO: elevated_firms {list(elevated)}",
        f"{'PASS' if recall >= 0.90 else 'FAIL'}: "
        f"ex_ante_pool_recall {recall} >= 0.90 "
        f"(post-hoc validation only)",
        f"{'PASS' if clean >= 0.90 else 'FAIL'}: "
        f"clean_firm_sound_rate {clean} >= 0.90 "
        f"(no false accusations)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V152Report(
        firm_count=len(signatures()),
        blindness_pool_count=bpc,
        cross_sector_pool_count=xsp,
        risk_family_detection=rfd,
        structural_redundancy=sr,
        recoverability_signal=rec,
        redundant_firm_fraction=rff,
        ex_ante_pool_recall=recall,
        clean_firm_sound_rate=clean,
        elevated_firms=elevated,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_blindness_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v15_2_financial_blindness_pools",
        "disclaimer": (
            "Structural blindness pools over the "
            "synthetic v15.0/v15.1 sector "
            "archetypes; clusters are built from "
            "epistemic structure only, NEVER from "
            "the sector label, and are NOT an "
            "industry classification. NOT real "
            "companies. DESi does NOT conclude "
            "fraud, does NOT rate, does NOT give "
            "investment advice - output is audit-"
            "priority only. Post-hoc labels are "
            "used solely as validation, never as "
            "scoring input."
        ),
        "audit_priorities": list(AUDIT_PRIORITIES),
        "risk_families": list(RISK_FAMILIES),
        "signature_axes": list(SIGNATURE_AXES),
        "signatures": [
            s.to_dict() for s in signatures()
        ],
        "pools": [p.to_dict() for p in pools()],
        "family_assignments": {
            k: list(v)
            for k, v in family_assignments().items()
        },
        "firm_pool_verdicts": [
            v.to_dict()
            for v in firm_pool_verdicts()
        ],
        "blindness_pool_count":
            blindness_pool_count(),
        "cross_sector_pool_count":
            _cross_sector_pool_count(),
        "risk_family_detection":
            risk_family_detection(),
        "structural_redundancy":
            structural_redundancy(),
        "recoverability_signal":
            recoverability_signal(),
        "redundant_firm_fraction":
            redundant_firm_fraction(),
        "ex_ante_pool_recall":
            ex_ante_pool_recall(),
        "clean_firm_sound_rate":
            clean_firm_sound_rate(),
        "corpus_priority_label":
            corpus_priority_label(),
    }


__all__ = [
    "FirmPoolVerdict",
    "V152Report",
    "build_blindness_artifact",
    "build_report",
    "clean_firm_sound_rate",
    "corpus_priority_label",
    "ex_ante_pool_recall",
    "firm_pool_verdicts",
    "pool_priority_label",
]
