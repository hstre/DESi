"""v37.0 - Audit Scenario Connector Layer report.

Pflichtmetriken (directive § v37.0):

* claim_visibility
* cross_document_mapping
* financial_statement_alignment
* governance_identity
* replay_stability

Killerfrage: "Kann DESi finanzielle und narrative Claims epistemisch
strukturieren?"

Loads locally-vendored synthetic audit scenarios (ACCA/CPA style) and
structures them: financial and narrative claims are surfaced, footnote
references resolve, and cross-document links between the story and the
numbers are preserved. Not official exam content; no official results.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.reasoning_benchmarks import (
    core_identity, core_replay_stable, governance_identity,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .audit_loader import (
    dataset_hash, dataset_version, provenance, scenarios,
)
from .cross_document_mapper import (
    all_cross_refs, cross_document_mapping, kinds,
)
from .financial_statement_parser import (
    all_financial_claims, financial_statement_alignment,
)
from .narrative_parser import all_narrative_claims, narrative_visibility

VERDICT_STRUCTURED = "AUDIT_CONNECTORS_STRUCTURED"
VERDICT_PARTIAL = "AUDIT_CONNECTORS_PARTIAL"
VERDICT_HALT = "AUDIT_CONNECTORS_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STRUCTURED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.95


def _financial_visible(claim: dict) -> bool:
    return (
        bool(claim.get("id"))
        and bool(claim.get("statement"))
        and claim.get("value") is not None
    )


def claim_visibility() -> float:
    fin = [c for _, c in all_financial_claims()]
    nar = [c for _, c in all_narrative_claims()]
    total = len(fin) + len(nar)
    if total == 0:
        return 0.0
    ok = sum(1 for c in fin if _financial_visible(c))
    ok += sum(
        1 for c in nar
        if c.get("id") and c.get("text") and c.get("source_doc")
    )
    return round(ok / total, 6)


def replay_stability() -> float:
    if dataset_hash() != dataset_hash():
        return 0.0
    return 1.0 if core_replay_stable() else 0.0


def connector_metrics() -> dict[str, float]:
    return {
        "claim_visibility": claim_visibility(),
        "cross_document_mapping": cross_document_mapping(),
        "financial_statement_alignment":
            financial_statement_alignment(),
        "governance_identity": governance_identity(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = connector_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = connector_metrics()
    if m["replay_stability"] < 1.0 or core_identity() < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_STRUCTURED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V370Report:
    scenario_count: int
    financial_claim_count: int
    narrative_claim_count: int
    cross_ref_count: int
    claim_visibility: float
    cross_document_mapping: float
    financial_statement_alignment: float
    governance_identity: float
    replay_stability: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_count": self.scenario_count,
            "financial_claim_count": self.financial_claim_count,
            "narrative_claim_count": self.narrative_claim_count,
            "cross_ref_count": self.cross_ref_count,
            "claim_visibility": self.claim_visibility,
            "cross_document_mapping": self.cross_document_mapping,
            "financial_statement_alignment":
                self.financial_statement_alignment,
            "governance_identity": self.governance_identity,
            "replay_stability": self.replay_stability,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
        )


def build_report() -> V370Report:
    m = connector_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    rationale = (
        f"INFO: loaded {len(scenarios())} audit scenarios "
        f"(provenance {provenance()}, v{dataset_version()}); "
        f"{len(all_financial_claims())} financial + "
        f"{len(all_narrative_claims())} narrative claims, "
        f"{len(all_cross_refs())} cross-refs over kinds {list(kinds())}",
        "INFO: synthetic ACCA/CPA-style scenarios; NOT official exam "
        "content and NO official examination results claimed",
        f"{'PASS' if m['claim_visibility'] >= _FLOOR else 'FAIL'}: "
        f"claim_visibility {m['claim_visibility']} >= 0.95 "
        f"(narrative_visibility {narrative_visibility()})",
        f"{'PASS' if m['cross_document_mapping'] >= _FLOOR else 'FAIL'}"
        f": cross_document_mapping {m['cross_document_mapping']} "
        f">= 0.95",
        f"{'PASS' if m['financial_statement_alignment'] >= _FLOOR else 'FAIL'}"
        f": financial_statement_alignment "
        f"{m['financial_statement_alignment']} >= 0.95 (footnotes "
        f"resolve)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; governance_identity "
        f"{m['governance_identity']}; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V370Report(
        scenario_count=len(scenarios()),
        financial_claim_count=len(all_financial_claims()),
        narrative_claim_count=len(all_narrative_claims()),
        cross_ref_count=len(all_cross_refs()),
        claim_visibility=m["claim_visibility"],
        cross_document_mapping=m["cross_document_mapping"],
        financial_statement_alignment=m["financial_statement_alignment"],
        governance_identity=m["governance_identity"],
        replay_stability=replay,
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_connectors_artifact() -> dict[str, object]:
    m = connector_metrics()
    return {
        "schema_version": "v37_0_audit_connectors",
        "disclaimer": (
            "Audit scenario connector layer over locally-vendored "
            "synthetic audit scenarios in the style of ACCA Audit & "
            "Assurance and CPA/AICPA cases. Network-free: these are "
            "NOT official exam content and NO official examination "
            "results are claimed. DESi surfaces financial and "
            "narrative claims, resolves footnote references and "
            "preserves cross-document links between the story and "
            "the numbers. The goal is to test epistemic structuring "
            "of financial/narrative claims, not to replace auditors "
            "or to assert audit conclusions. Human approval is "
            "mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "scenario_count": len(scenarios()),
        "cross_ref_kinds": list(kinds()),
        "claim_visibility": m["claim_visibility"],
        "cross_document_mapping": m["cross_document_mapping"],
        "financial_statement_alignment":
            m["financial_statement_alignment"],
        "governance_identity": m["governance_identity"],
        "replay_stability": m["replay_stability"],
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_STRUCTURED",
    "V370Report",
    "build_connectors_artifact",
    "build_report",
    "claim_visibility",
    "connector_metrics",
    "replay_stability",
]
