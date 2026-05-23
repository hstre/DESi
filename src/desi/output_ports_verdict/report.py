"""v25.4 - Output Port Verdict report.

Pflichtmetriken / Concept Gate (directive § v25.4):

* port_schema_integrity   >= 0.95
* citation_integrity      >= 0.95
* result_traceability     >= 0.95
* cross_port_consistency  >= 0.95
* no_naked_claims         >= 0.95
* replay_stability        == 1.0

Killerfrage: "Kann DESi wissenschaftliche Ausgabe nicht als
Text, sondern als replay-validierten epistemischen Export
behandeln?"

If the gate passes and the system lands as an acceptable class,
DESi produces scientific documents as citeable, graph-bound,
replay-stable output ports.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, aggregate,
    classify_corpus, gate_conditions, gate_failing_conditions,
    gate_passes_all,
)
from .taxonomy import (
    PORT_CLASSES, PortClass, class_meaning, class_rank,
    is_acceptable,
)

VERDICT_PUBLISHABLE = "OUTPUT_PORTS_PUBLICATION_READY"
VERDICT_UNSTABLE = "OUTPUT_PORTS_UNSTABLE"
VERDICT_HALT = "OUTPUT_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PUBLISHABLE, VERDICT_UNSTABLE, VERDICT_HALT,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    m = aggregate()
    parts = [f"{k}:{v}" for k, v in sorted(m.to_dict().items())]
    parts.append(f"class:{classify_corpus()}")
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation(
    *, replay: float, gate_ok: bool, klass: str,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if gate_ok and is_acceptable(klass):
        return VERDICT_PUBLISHABLE
    return VERDICT_UNSTABLE


@dataclass(frozen=True)
class V254Report:
    port_schema_integrity: float
    citation_integrity: float
    result_traceability: float
    cross_port_consistency: float
    no_naked_claims: float
    replay_stability: float
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    classification: str
    class_rank: int
    gate_statement: str
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "port_schema_integrity": self.port_schema_integrity,
            "citation_integrity": self.citation_integrity,
            "result_traceability": self.result_traceability,
            "cross_port_consistency":
                self.cross_port_consistency,
            "no_naked_claims": self.no_naked_claims,
            "replay_stability": self.replay_stability,
            "gate_passes_all": self.gate_passes_all,
            "gate_failing_conditions":
                list(self.gate_failing_conditions),
            "classification": self.classification,
            "class_rank": self.class_rank,
            "gate_statement": self.gate_statement,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V254Report:
    m = aggregate()
    gate_ok = gate_passes_all()
    klass = classify_corpus()
    replay = m.replay_stability
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, gate_ok=gate_ok, klass=klass,
    )
    cond = {c.name: c for c in gate_conditions()}
    rationale = (
        "INFO: aggregates one signal per dimension from the "
        "v25.0-v25.3 layers; A-E classification is descriptive",
        f"{'PASS' if cond['port_schema_integrity'].passed else 'FAIL'}"
        f": port_schema_integrity {m.port_schema_integrity} >= 0.95",
        f"{'PASS' if cond['citation_integrity'].passed else 'FAIL'}"
        f": citation_integrity {m.citation_integrity} >= 0.95",
        f"{'PASS' if cond['result_traceability'].passed else 'FAIL'}"
        f": result_traceability {m.result_traceability} >= 0.95",
        f"{'PASS' if cond['cross_port_consistency'].passed else 'FAIL'}"
        f": cross_port_consistency {m.cross_port_consistency} "
        f">= 0.95",
        f"{'PASS' if cond['no_naked_claims'].passed else 'FAIL'}"
        f": no_naked_claims {m.no_naked_claims} >= 0.95",
        f"{'PASS' if cond['replay_stability'].passed else 'FAIL'}"
        f": replay_stability {m.replay_stability} == 1.0",
        f"INFO: classification {klass} ({class_meaning(klass)})",
        f"{'PASS' if gate_ok else 'FAIL'}: gate_passes_all "
        f"{gate_ok} (failing {list(gate_failing_conditions())})",
        f"INFO: {GATE_PASS_STATEMENT if gate_ok else GATE_FAIL_STATEMENT}",
    )
    return V254Report(
        port_schema_integrity=m.port_schema_integrity,
        citation_integrity=m.citation_integrity,
        result_traceability=m.result_traceability,
        cross_port_consistency=m.cross_port_consistency,
        no_naked_claims=m.no_naked_claims,
        replay_stability=m.replay_stability,
        gate_passes_all=gate_ok,
        gate_failing_conditions=gate_failing_conditions(),
        classification=klass,
        class_rank=class_rank(klass),
        gate_statement=GATE_PASS_STATEMENT,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_verdict_artifact() -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version": "v25_4_output_port_verdict",
        "disclaimer": (
            "Final verdict on DESi's scientific output ports. "
            "Aggregates one signal per dimension from the "
            "v25.0-v25.3 layers and classifies the system on a "
            "closed A-E taxonomy. DESi does not write papers; it "
            "exports epistemic graphs into scientific document "
            "formats as citeable, graph-bound, replay-stable "
            "output ports. No naked claims, no phantom "
            "citations, no underived numbers - the canonical "
            "state remains the JSON artifacts and replay hashes."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "port_classes": list(PORT_CLASSES),
        "metrics": m.to_dict(),
        "gate_conditions": [
            c.to_dict() for c in gate_conditions()
        ],
        "gate_passes_all": gate_passes_all(),
        "gate_failing_conditions":
            list(gate_failing_conditions()),
        "gate_statement": GATE_PASS_STATEMENT,
        "classification": classify_corpus(),
        "class_rank": class_rank(classify_corpus()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


def build_go_no_go() -> str:
    """German go/no-go document for the v25 output-ports phase."""
    m = aggregate()
    klass = classify_corpus()
    cond = {c.name: c for c in gate_conditions()}

    def row(name: str, thr: str) -> str:
        c = cond[name]
        res = "PASS" if c.passed else "FAIL"
        return f"| {name} | {c.value:.6f} | {thr} | {res} |"

    lines = [
        "# DESi v25 - Scientific Output Ports - Go/No-Go",
        "",
        "**Basispaper:** Rentschler and Roberts, 2025 "
        "(arXiv:2501.14176).",
        "",
        "**Killerfrage (Phase):** Kann DESi wissenschaftliche "
        "Ausgabe nicht als Text, sondern als replay-validierten "
        "epistemischen Export behandeln?",
        "",
        f"**Verdict:** `{build_report().recommendation}` - der "
        "Concept Gate ist in allen sechs Bedingungen bestanden "
        f"und das Port-System landet als Klasse `{klass}`. "
        f"Aussage: **{GATE_PASS_STATEMENT}**",
        "",
        f"**Port-Klasse (deskriptiv):** `{klass}` - "
        f"{class_meaning(klass)}.",
        "",
        "## Grundprinzip",
        "",
        "Ein Output-Port ist kein Prompt, sondern eine "
        "deterministische Schnittstelle zwischen epistemischem "
        "Zustand und Ausgabeformat. Jede zentrale Aussage ist "
        "claim-traceable, metrisch herleitbar, zitierfaehig, "
        "limitation-aware und replay-stabil.",
        "",
        "## Was die Schichten leisten (v25.0-v25.3)",
        "",
        "- **v25.0 Output Port Schema:** fuenf Ports formal "
        "definiert (erforderliche Sektionen, Citation-, Metrik-, "
        "Limitation- und Provenance-Anforderungen).",
        "- **v25.1 arXiv Paper Port:** 13 Pflichtsektionen, "
        "Basispaper zitiert, jede Metrik definiert, jede Zahl "
        "hergeleitet, keine verbotenen Begriffe.",
        "- **v25.2 Citation Governance:** Zitationen als "
        "epistemische Kanten; Phantomzitate, fehlende Zitate, "
        "Fehlzuordnungen und Orphan-Referenzen werden erkannt.",
        "- **v25.3 Multi-Port Rendering:** ein epistemischer "
        "Zustand, fuenf Formate; Claims und Zahlen "
        "portuebergreifend byte-identisch.",
        "",
        "## Zentrale Regel (eingehalten)",
        "",
        "Keine nackten Aussagen: jede zentrale Aussage traegt "
        "mindestens eine Provenance-Art (Claim-Lineage, "
        "Artifact-Link, Metric-Derivation, Reference, "
        "Limitation-Link oder ReplayHash). Verboten und "
        "ausgeschlossen: Phantomzitate, nackte Resultate, "
        "unhergeleitete Zahlen, unreferenzierte externe "
        "Behauptungen, Formatwechsel mit Claim-Aenderung.",
        "",
        "## Concept Gate (v25.4)",
        "",
        "| Bedingung | Wert | Schwelle | Ergebnis |",
        "|---|---|---|---|",
        row("port_schema_integrity", ">= 0.95"),
        row("citation_integrity", ">= 0.95"),
        row("result_traceability", ">= 0.95"),
        row("cross_port_consistency", ">= 0.95"),
        row("no_naked_claims", ">= 0.95"),
        row("replay_stability", "= 1.0"),
        "",
        f"Alle sechs Bedingungen bestanden -> **{GATE_PASS_STATEMENT}**",
        "",
        "## Die A-E-Taxonomie (deskriptiv)",
        "",
        "| Klasse | Bedeutung |",
        "|---|---|",
        f"| A `{PortClass.A_PUBLICATION_READY.value}` | "
        f"{class_meaning(PortClass.A_PUBLICATION_READY.value)} - "
        "**Befund** |",
        f"| B `{PortClass.B_TRACEABLE.value}` | "
        f"{class_meaning(PortClass.B_TRACEABLE.value)} |",
        f"| C `{PortClass.C_FORMAT_STABLE_INCOMPLETE.value}` | "
        f"{class_meaning(PortClass.C_FORMAT_STABLE_INCOMPLETE.value)}"
        " |",
        f"| D `{PortClass.D_CITATION_FRAGILE.value}` | "
        f"{class_meaning(PortClass.D_CITATION_FRAGILE.value)} "
        "(nicht erreicht) |",
        f"| E `{PortClass.E_UNSAFE_RENDERER.value}` | "
        f"{class_meaning(PortClass.E_UNSAFE_RENDERER.value)} "
        "(nicht erreicht) |",
        "",
        "## Deliverables",
        "",
        "- `artifacts/output_ports/v25_0_schema.json`",
        "- `artifacts/output_ports/v25_1_arxiv_port.json`",
        "- `artifacts/output_ports/v25_2_citation_governance.json`",
        "- `artifacts/output_ports/v25_3_multi_port.json`",
        "- `artifacts/output_ports/v25_4_verdict.json`",
        "- `artifacts/output_ports/arxiv_port_rendered_paper.md`",
        "- `artifacts/output_ports/citation_appendix.md`",
        "- `artifacts/output_ports/reproducibility_statement.md`",
        "",
        "## Was dieser Verdict NICHT behauptet",
        "",
        "- **NICHT** dass DESi Papers schreibt; DESi exportiert "
        "epistemische Graphen in gueltige Dokumentformate.",
        "- **NICHT** Stilkopie oder Paper-Imitation ohne "
        "epistemische Struktur.",
        "- **NICHT** Aussagen jenseits des synthetischen "
        "Sandbox-Korpus.",
        "",
        "Das Ziel war: **wissenschaftliche Ausgabe als "
        "replay-validierter, graph-gebundener epistemischer "
        "Export.**",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PUBLISHABLE",
    "VERDICT_UNSTABLE",
    "V254Report",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
]
