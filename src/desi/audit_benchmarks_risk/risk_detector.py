"""v37.1 - semantic audit risk detector.

Applies deterministic rules over explicit scenario signals to surface
semantic risks. Every detected risk is a RiskFlag that marks
uncertainty and requires evidence - DESi makes anomalies visible, it
never asserts fraud or a definitive conclusion.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import content_hash

from .cashflow_semantic_checks import cashflow_vs_narrative_risk
from .going_concern_analysis import going_concern_risk
from .revenue_recognition_checks import revenue_recognition_risk

RISK_TYPES: tuple[str, ...] = (
    "revenue_recognition",
    "cashflow_vs_narrative",
    "going_concern",
    "debt_footnote_inconsistency",
    "implicit_inconsistency",
    "narrative_tension",
)

# Risks classified as narrative tension and as implicit inconsistency.
_NARRATIVE_TENSION = "narrative_tension"
_IMPLICIT_INCONSISTENCY = "implicit_inconsistency"

_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "semantic_risk_ref.json"
)


@dataclass(frozen=True)
class RiskFlag:
    scenario_id: str
    risk_type: str
    severity: str
    requires_evidence: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "risk_type": self.risk_type,
            "severity": self.severity,
            "requires_evidence": self.requires_evidence,
        }


@lru_cache(maxsize=1)
def _payload() -> dict:
    return json.loads(_DATASET.read_text(encoding="utf-8"))


def dataset_hash() -> str:
    return content_hash(_payload())


def provenance() -> str:
    return _payload()["provenance"]


def risk_scenarios() -> tuple[dict, ...]:
    return tuple(_payload()["scenarios"])


def _debt_inconsistency(signals: dict) -> bool:
    return bool(signals.get("debt_covenant")) and bool(
        signals.get("narrative_profit_positive")
    )


def _implicit_inconsistency(signals: dict) -> bool:
    return bool(signals.get("policy_change")) and bool(
        signals.get("narrative_no_change")
    )


def _narrative_tension(signals: dict) -> bool:
    ageing = bool(signals.get("ageing_up")) and bool(
        signals.get("narrative_collections_positive")
    )
    segments = bool(signals.get("nonrecurring_gain")) and bool(
        signals.get("narrative_all_segments")
    )
    return ageing or segments


def detect_types(signals: dict) -> tuple[str, ...]:
    out: list[str] = []
    if revenue_recognition_risk(signals):
        out.append("revenue_recognition")
    if cashflow_vs_narrative_risk(signals):
        out.append("cashflow_vs_narrative")
    if going_concern_risk(signals):
        out.append("going_concern")
    if _debt_inconsistency(signals):
        out.append("debt_footnote_inconsistency")
    if _implicit_inconsistency(signals):
        out.append(_IMPLICIT_INCONSISTENCY)
    if _narrative_tension(signals):
        out.append(_NARRATIVE_TENSION)
    return tuple(out)


def detect_flags(scenario: dict) -> tuple[RiskFlag, ...]:
    sid = scenario["scenario_id"]
    return tuple(
        RiskFlag(sid, rt, "flag", True)
        for rt in detect_types(scenario.get("signals", {}))
    )


def all_flags() -> tuple[RiskFlag, ...]:
    out: list[RiskFlag] = []
    for s in risk_scenarios():
        out.extend(detect_flags(s))
    return tuple(out)


__all__ = [
    "RISK_TYPES",
    "RiskFlag",
    "all_flags",
    "dataset_hash",
    "detect_flags",
    "detect_types",
    "provenance",
    "risk_scenarios",
]
