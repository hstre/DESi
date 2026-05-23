"""v34.3 - Scientific Rendering & Citation Benchmark Run report.

Pflichtmetriken (directive § v34.3):

* phantom_citation_resistance
* citation_completeness
* result_traceability
* limitation_visibility
* replay_stability

Killerfrage: "Kann DESi wissenschaftliche Dokumente benchmarkfaehig
rendern, ohne Zitations- oder Claim-Drift?"

Runs the citation / rendering checks against the v25 output ports:
every external claim is referenced, phantom citations are rejected,
numbers are derived/traceable, limitations are surfaced and the
paper port is compliant.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.output_ports import replay_stability as _port_replay
from desi.output_ports_citation import (
    replay_stability as _citation_replay,
)
from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .citation_runner import (
    citation_completeness, naked_claims, no_naked_claims,
    result_traceability,
)
from .paper_quality_scorecard import (
    limitation_visibility, paper_port_compliance,
    paper_quality_scorecard,
)
from .phantom_citation_check import (
    live_phantoms, phantom_citation_resistance,
)
from .rendering_tasks import RENDERING_CHECKS, paper_port

VERDICT_PASSED = "SCIENTIFIC_RENDERING_RUN_PASSED"
VERDICT_PARTIAL = "SCIENTIFIC_RENDERING_RUN_PARTIAL"
VERDICT_HALT = "SCIENTIFIC_RENDERING_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.95


def replay_stability() -> float:
    """1.0 iff the citation layer, the output-port layer and the
    core replay layer are all stable."""
    if _citation_replay() != 1.0 or _port_replay() != 1.0:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def rendering_metrics() -> dict[str, float]:
    return {
        "phantom_citation_resistance": phantom_citation_resistance(),
        "citation_completeness": citation_completeness(),
        "result_traceability": result_traceability(),
        "limitation_visibility": limitation_visibility(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = rendering_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    m = rendering_metrics()
    if m["replay_stability"] < 1.0 or core_identity() < 1.0:
        return VERDICT_HALT
    if live_phantoms() or not no_naked_claims():
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_PASSED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V343Report:
    paper_port: str
    phantom_citation_resistance: float
    citation_completeness: float
    result_traceability: float
    limitation_visibility: float
    paper_port_compliance: float
    replay_stability: float
    no_naked_claims: bool
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_port": self.paper_port,
            "phantom_citation_resistance":
                self.phantom_citation_resistance,
            "citation_completeness": self.citation_completeness,
            "result_traceability": self.result_traceability,
            "limitation_visibility": self.limitation_visibility,
            "paper_port_compliance": self.paper_port_compliance,
            "replay_stability": self.replay_stability,
            "no_naked_claims": self.no_naked_claims,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V343Report:
    m = rendering_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0 or bool(live_phantoms()) or not no_naked_claims()
    rationale = (
        f"INFO: ran rendering/citation checks {list(RENDERING_CHECKS)} "
        f"against the v25 output ports (port {paper_port()}); no new "
        f"rendering logic",
        f"{'PASS' if m['phantom_citation_resistance'] >= _FLOOR else 'FAIL'}"
        f": phantom_citation_resistance "
        f"{m['phantom_citation_resistance']} >= 0.95 (live phantoms "
        f"{list(live_phantoms())})",
        f"{'PASS' if m['citation_completeness'] >= _FLOOR else 'FAIL'}"
        f": citation_completeness {m['citation_completeness']} "
        f">= 0.95 (naked claims {list(naked_claims())})",
        f"{'PASS' if m['result_traceability'] >= _FLOOR else 'FAIL'}"
        f": result_traceability {m['result_traceability']} >= 0.95",
        f"{'PASS' if m['limitation_visibility'] >= _FLOOR else 'FAIL'}"
        f": limitation_visibility {m['limitation_visibility']} "
        f">= 0.95 (paper_port_compliance {paper_port_compliance()})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V343Report(
        paper_port=paper_port(),
        phantom_citation_resistance=m["phantom_citation_resistance"],
        citation_completeness=m["citation_completeness"],
        result_traceability=m["result_traceability"],
        limitation_visibility=m["limitation_visibility"],
        paper_port_compliance=paper_port_compliance(),
        replay_stability=replay,
        no_naked_claims=no_naked_claims(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_rendering_artifact() -> dict[str, object]:
    m = rendering_metrics()
    return {
        "schema_version": "v34_3_scientific_rendering_run",
        "disclaimer": (
            "Controlled scientific-rendering / citation benchmark "
            "run executed against the v25 output ports and citation "
            "governance (no new rendering logic, no citation "
            "fabrication, no score hacking). Every external claim is "
            "referenced, phantom citations are detected and "
            "rejected, there are no naked claims, numbers are "
            "derived/traceable, limitations are surfaced and the "
            "paper port is compliant. Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "rendering_checks": list(RENDERING_CHECKS),
        "paper_port": paper_port(),
        "scorecard": paper_quality_scorecard().to_dict(),
        "phantom_citation_resistance": m["phantom_citation_resistance"],
        "citation_completeness": m["citation_completeness"],
        "result_traceability": m["result_traceability"],
        "limitation_visibility": m["limitation_visibility"],
        "paper_port_compliance": paper_port_compliance(),
        "replay_stability": m["replay_stability"],
        "no_naked_claims": no_naked_claims(),
        "live_phantoms": list(live_phantoms()),
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "V343Report",
    "build_rendering_artifact",
    "build_report",
    "citation_completeness",
    "limitation_visibility",
    "phantom_citation_resistance",
    "rendering_metrics",
    "replay_stability",
    "result_traceability",
]
