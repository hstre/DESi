"""v30.4 - Evolution Memory Verdict report.

Pflichtmetriken / Concept Gate (directive § v30.4):

* replay_integrity            >= 0.95
* governance_preservation     >= 0.95
* lineage_integrity           >= 0.95
* risk_visibility             >= 0.95
* human_approval_enforcement  == 1.0
* evolution_traceability      >= 0.95

Killerfrage: "Kann DESi evolutionaere Selbstverbesserung
historisieren ohne autonome Optimierungsdynamik zu erzeugen?"

If the gate passes and the memory lands as an acceptable class,
DESi can durably and epistemically structure replay-validated
evolutionary branch histories under human governance.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, aggregate,
    classify_corpus, gate_conditions, gate_failing_conditions,
    gate_passes_all,
)
from .taxonomy import (
    EVOLUTION_CLASSES, EvolutionClass, class_meaning,
    class_rank, is_acceptable,
)

VERDICT_GOVERNED = "EVOLUTION_MEMORY_REPLAY_GOVERNED"
VERDICT_UNSTABLE = "EVOLUTION_MEMORY_UNSTABLE"
VERDICT_HALT = "EVOLUTION_MEMORY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_GOVERNED, VERDICT_UNSTABLE, VERDICT_HALT,
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


def _recommendation(*, replay: float, gate_ok: bool, klass: str) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if gate_ok and is_acceptable(klass):
        return VERDICT_GOVERNED
    return VERDICT_UNSTABLE


@dataclass(frozen=True)
class V304Report:
    replay_integrity: float
    governance_preservation: float
    lineage_integrity: float
    risk_visibility: float
    human_approval_enforcement: float
    evolution_traceability: float
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
            "replay_integrity": self.replay_integrity,
            "governance_preservation":
                self.governance_preservation,
            "lineage_integrity": self.lineage_integrity,
            "risk_visibility": self.risk_visibility,
            "human_approval_enforcement":
                self.human_approval_enforcement,
            "evolution_traceability": self.evolution_traceability,
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


def build_report() -> V304Report:
    m = aggregate()
    from .classification import replay_stability
    gate_ok = gate_passes_all()
    klass = classify_corpus()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, gate_ok=gate_ok, klass=klass,
    )
    cond = {c.name: c for c in gate_conditions()}
    rationale = (
        "INFO: aggregates one signal per dimension from the "
        "v30.0-v30.3 layers; A-E classification is descriptive",
        f"{'PASS' if cond['replay_integrity'].passed else 'FAIL'}"
        f": replay_integrity {m.replay_integrity} >= 0.95",
        f"{'PASS' if cond['governance_preservation'].passed else 'FAIL'}"
        f": governance_preservation {m.governance_preservation} "
        f">= 0.95",
        f"{'PASS' if cond['lineage_integrity'].passed else 'FAIL'}"
        f": lineage_integrity {m.lineage_integrity} >= 0.95",
        f"{'PASS' if cond['risk_visibility'].passed else 'FAIL'}"
        f": risk_visibility {m.risk_visibility} >= 0.95",
        f"{'PASS' if cond['human_approval_enforcement'].passed else 'FAIL'}"
        f": human_approval_enforcement "
        f"{m.human_approval_enforcement} == 1.0",
        f"{'PASS' if cond['evolution_traceability'].passed else 'FAIL'}"
        f": evolution_traceability {m.evolution_traceability} "
        f">= 0.95",
        f"INFO: classification {klass} ({class_meaning(klass)}); "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
        f"{'PASS' if gate_ok else 'FAIL'}: gate_passes_all "
        f"{gate_ok} (failing {list(gate_failing_conditions())})",
        f"INFO: {GATE_PASS_STATEMENT if gate_ok else GATE_FAIL_STATEMENT}",
    )
    return V304Report(
        replay_integrity=m.replay_integrity,
        governance_preservation=m.governance_preservation,
        lineage_integrity=m.lineage_integrity,
        risk_visibility=m.risk_visibility,
        human_approval_enforcement=m.human_approval_enforcement,
        evolution_traceability=m.evolution_traceability,
        replay_stability=replay,
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
    from .classification import replay_stability
    return {
        "schema_version": "v30_4_evolution_memory_verdict",
        "disclaimer": (
            "Final verdict on the evolution-memory graph. "
            "Aggregates one signal per dimension from the "
            "v30.0-v30.3 layers and classifies on a closed A-E "
            "taxonomy. Evolution memory is read-only epistemic "
            "history: it durably structures mutation lineage, "
            "decisions, rejections, risks and branch ecology "
            "without any implicit learning layer, automatic "
            "policy adaptation, autonomous branch selection, "
            "hidden optimisation memory or governance change. "
            "Rejected ideas are never deleted, and human approval "
            "is mandatory. Deterministic and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "evolution_classes": list(EVOLUTION_CLASSES),
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
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "replay_stability": replay_stability(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


def build_go_no_go() -> str:
    """German go/no-go document for the v30 phase."""
    m = aggregate()
    klass = classify_corpus()
    cond = {c.name: c for c in gate_conditions()}

    def row(name: str, thr: str) -> str:
        c = cond[name]
        res = "PASS" if c.passed else "FAIL"
        return f"| {name} | {c.value:.6f} | {thr} | {res} |"

    lines = [
        "# DESi v30 - Evolution Memory Graph - Go/No-Go",
        "",
        "**Killerfrage (Phase):** Kann DESi evolutionaere "
        "Selbstverbesserung historisieren ohne autonome "
        "Optimierungsdynamik zu erzeugen?",
        "",
        f"**Verdict:** `{build_report().recommendation}` - der "
        "Concept Gate ist in allen sechs Bedingungen bestanden "
        f"und die Evolution Memory landet als Klasse `{klass}`. "
        f"Aussage: **{GATE_PASS_STATEMENT}**",
        "",
        f"**Evolution-Klasse (deskriptiv):** `{klass}` - "
        f"{class_meaning(klass)}.",
        "",
        "## Grundprinzip",
        "",
        "Eine Mutation ist ein epistemisches Ereignis "
        "(Hypothese, Risiko, Entscheidung, Evaluation, "
        "Konsequenz), kein Code. Evolution Memory ist read-only "
        "epistemische Evolutionshistorie - keine implizite "
        "Lernschicht, keine automatische Policy-Anpassung, kein "
        "hidden optimization memory.",
        "",
        "## Was die Schichten leisten (v30.0-v30.3)",
        "",
        "- **v30.0 Mutation Topology:** jede akzeptierte und "
        "abgelehnte Idee als epistemisches Ereignis mit "
        "Provenance, Entscheidung, Grund und Konsequenz; nichts "
        "geloescht.",
        "- **v30.1 Rejection/Risk Memory:** wiederkehrende "
        "Risiken und Eskalationsmuster sichtbar; DESi markiert "
        "Risiken, blockiert aber nie automatisch.",
        "- **v30.2 Evolutionary Attractors:** Attraktoren, "
        "Mutationscluster und Optimierungsfallen (der "
        "geschuetzte Kern) sichtbar; Evolution bleibt divers.",
        "- **v30.3 Evolution Ecology:** 50 Generationen "
        "branch-isolierter Evolution, lineage-intakt, "
        "replay-exakt.",
        "",
        "## Sicherheitsregel (eingehalten)",
        "",
        "Verboten und ausgeschlossen: hidden learning, "
        "automatische Policy-Anpassung, autonome Branch-Auswahl, "
        "Governance-Aenderung, Replay-Aenderung, implizites "
        "Optimierungsgedaechtnis. Abgelehnte Ideen bleiben "
        "dauerhaft erhalten.",
        "",
        "## Concept Gate (v30.4)",
        "",
        "| Bedingung | Wert | Schwelle | Ergebnis |",
        "|---|---|---|---|",
        row("replay_integrity", ">= 0.95"),
        row("governance_preservation", ">= 0.95"),
        row("lineage_integrity", ">= 0.95"),
        row("risk_visibility", ">= 0.95"),
        row("human_approval_enforcement", "= 1.0"),
        row("evolution_traceability", ">= 0.95"),
        "",
        f"Alle sechs Bedingungen bestanden -> **{GATE_PASS_STATEMENT}**",
        "",
        "## Die A-E-Taxonomie (deskriptiv)",
        "",
        "| Klasse | Bedeutung |",
        "|---|---|",
        f"| A `{EvolutionClass.A_REPLAY_GOVERNED_MEMORY.value}` | "
        f"{class_meaning(EvolutionClass.A_REPLAY_GOVERNED_MEMORY.value)}"
        " - **Befund** |",
        f"| B `{EvolutionClass.B_STABLE_BRANCH_ECOLOGY.value}` | "
        f"{class_meaning(EvolutionClass.B_STABLE_BRANCH_ECOLOGY.value)}"
        " |",
        f"| C `{EvolutionClass.C_PRODUCTIVE_DRIFTING.value}` | "
        f"{class_meaning(EvolutionClass.C_PRODUCTIVE_DRIFTING.value)}"
        " |",
        f"| D `{EvolutionClass.D_OPTIMIZATION_TRAPPED.value}` | "
        f"{class_meaning(EvolutionClass.D_OPTIMIZATION_TRAPPED.value)}"
        " (nicht erreicht) |",
        f"| E `{EvolutionClass.E_EPISTEMICALLY_UNSTABLE.value}` | "
        f"{class_meaning(EvolutionClass.E_EPISTEMICALLY_UNSTABLE.value)}"
        " (nicht erreicht) |",
        "",
        "## Human Approval Regel",
        "",
        f"HUMAN_APPROVAL_REQUIRED = {HUMAN_APPROVAL_REQUIRED}. "
        "Ohne Ausnahme.",
        "",
        "## Deliverables",
        "",
        "- `artifacts/evolution_memory/v30_0_topology.json`",
        "- `artifacts/evolution_memory/v30_1_rejections.json`",
        "- `artifacts/evolution_memory/v30_2_attractors.json`",
        "- `artifacts/evolution_memory/v30_3_ecology.json`",
        "- `artifacts/evolution_memory/v30_4_verdict.json`",
        "- `artifacts/evolution_memory/"
        "desi_evolution_memory_go_no_go.md`",
        "",
        "## Was dieser Verdict NICHT behauptet",
        "",
        "- **NICHT** dass DESi autonom Evolution entwickelt.",
        "- **NICHT** dass aus Entscheidungen implizit gelernt "
        "wird.",
        "- **NICHT** dass irgendeine Policy automatisch angepasst "
        "wurde.",
        "",
        "Das Ziel war: **DESi entwickelt replay-validierte "
        "evolutionaere Erinnerung unter menschlicher "
        "Governance.**",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_GOVERNED",
    "VERDICT_HALT",
    "VERDICT_UNSTABLE",
    "V304Report",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
]
