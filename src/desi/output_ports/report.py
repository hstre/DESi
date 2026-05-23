"""v25.0 - Output Port Schema report.

Pflichtmetriken (directive § v25.0):

* port_schema_coverage
* required_section_visibility
* citation_requirement_visibility
* limitation_requirement_visibility
* replay_stability

Killerfrage: "Kann DESi wissenschaftliche Ausgabeformate als
formale epistemische Schnittstellen modellieren?"

Each port is a formal schema: required sections, citation /
metric / limitation / provenance requirements and forbidden
patterns. The schema decides nothing and renders nothing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .port_types import PORT_TYPES
from .requirements import PROVENANCE_KINDS
from .schema import port_schemas, schema_signature

VERDICT_FORMAL = "OUTPUT_PORTS_FORMALISED"
VERDICT_INCOMPLETE = "OUTPUT_PORTS_INCOMPLETE"
VERDICT_HALT = "SCHEMA_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_FORMAL, VERDICT_INCOMPLETE, VERDICT_HALT,
)

_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def port_schema_coverage() -> float:
    """Fraction of ports with a complete formal schema, in
    [0, 1]."""
    schemas = port_schemas()
    if not schemas:
        return 0.0
    complete = sum(1 for s in schemas if s.is_complete())
    return _round(complete / len(schemas))


def required_section_visibility() -> float:
    """Fraction of ports that expose at least one required
    section, in [0, 1]."""
    schemas = port_schemas()
    if not schemas:
        return 0.0
    visible = sum(1 for s in schemas if s.required_sections)
    return _round(visible / len(schemas))


def citation_requirement_visibility() -> float:
    """Fraction of ports whose citation policy is explicitly
    declared, in [0, 1]."""
    schemas = port_schemas()
    if not schemas:
        return 0.0
    declared = sum(
        1 for s in schemas if s.citation is not None
    )
    return _round(declared / len(schemas))


def limitation_requirement_visibility() -> float:
    """Fraction of ports that mandate a Limitations section, in
    [0, 1]."""
    schemas = port_schemas()
    if not schemas:
        return 0.0
    mandated = sum(
        1 for s in schemas if s.limitation.required
    )
    return _round(mandated / len(schemas))


def replay_stability() -> float:
    return 1.0 if schema_signature() == schema_signature() else 0.0


def _recommendation(
    *, replay: float, coverage: float, sections: float,
    citation: float, limitation: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        coverage < _FLOOR
        or sections < _FLOOR
        or citation < _FLOOR
        or limitation < _FLOOR
    ):
        return VERDICT_INCOMPLETE
    return VERDICT_FORMAL


@dataclass(frozen=True)
class V250Report:
    port_count: int
    provenance_kind_count: int
    port_schema_coverage: float
    required_section_visibility: float
    citation_requirement_visibility: float
    limitation_requirement_visibility: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "port_count": self.port_count,
            "provenance_kind_count": self.provenance_kind_count,
            "port_schema_coverage": self.port_schema_coverage,
            "required_section_visibility":
                self.required_section_visibility,
            "citation_requirement_visibility":
                self.citation_requirement_visibility,
            "limitation_requirement_visibility":
                self.limitation_requirement_visibility,
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


def build_report() -> V250Report:
    coverage = port_schema_coverage()
    sections = required_section_visibility()
    citation = citation_requirement_visibility()
    limitation = limitation_requirement_visibility()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, coverage=coverage, sections=sections,
        citation=citation, limitation=limitation,
    )
    rationale = (
        f"INFO: {len(PORT_TYPES)} output ports; "
        f"{len(PROVENANCE_KINDS)} provenance kinds "
        f"{list(PROVENANCE_KINDS)}",
        "INFO: a port is a deterministic interface between the "
        "epistemic state and a document format - not a prompt",
        f"{'PASS' if coverage >= 0.90 else 'FAIL'}: "
        f"port_schema_coverage {coverage} >= 0.90",
        f"{'PASS' if sections >= 0.90 else 'FAIL'}: "
        f"required_section_visibility {sections} >= 0.90",
        f"{'PASS' if citation >= 0.90 else 'FAIL'}: "
        f"citation_requirement_visibility {citation} >= 0.90",
        f"{'PASS' if limitation >= 0.90 else 'FAIL'}: "
        f"limitation_requirement_visibility {limitation} >= "
        f"0.90 (Limitations mandatory per port)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{schema_signature()[:12]})",
    )
    return V250Report(
        port_count=len(PORT_TYPES),
        provenance_kind_count=len(PROVENANCE_KINDS),
        port_schema_coverage=coverage,
        required_section_visibility=sections,
        citation_requirement_visibility=citation,
        limitation_requirement_visibility=limitation,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_schema_artifact() -> dict[str, object]:
    return {
        "schema_version": "v25_0_output_port_schema",
        "disclaimer": (
            "Formal schemas for DESi's scientific output ports. "
            "An output port is a deterministic interface between "
            "the epistemic state (graph, artifacts, claims, "
            "metrics, references, replay hashes) and a document "
            "format - not free text generation, paper imitation "
            "or style copying. Each port declares required "
            "sections and citation / metric / limitation / "
            "provenance requirements; the central rule is that "
            "no central claim may be naked. Deterministic."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "port_types": list(PORT_TYPES),
        "provenance_kinds": list(PROVENANCE_KINDS),
        "schemas": [s.to_dict() for s in port_schemas()],
        "port_schema_coverage": port_schema_coverage(),
        "required_section_visibility":
            required_section_visibility(),
        "citation_requirement_visibility":
            citation_requirement_visibility(),
        "limitation_requirement_visibility":
            limitation_requirement_visibility(),
        "replay_stability": replay_stability(),
        "schema_signature": schema_signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_FORMAL",
    "VERDICT_HALT",
    "VERDICT_INCOMPLETE",
    "V250Report",
    "build_report",
    "build_schema_artifact",
    "citation_requirement_visibility",
    "limitation_requirement_visibility",
    "port_schema_coverage",
    "replay_stability",
    "required_section_visibility",
]
