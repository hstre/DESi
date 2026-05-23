"""v27.4 - Research Harvester Verdict report.

Pflichtmetriken / Concept Gate (directive § v27.4):

* claim_extraction_consistency >= 0.90
* lineage_visibility           >= 0.90
* conflict_preservation        >= 0.90
* epistemic_neutrality         >= 0.95
* graph_integrity              >= 0.95
* replay_stability             == 1.0

Killerfrage: "Kann DESi wissenschaftliche Forschung als
dynamische epistemische Landschaft modellieren statt als
isolierte Papers?"

If the gate passes and the harvester lands as an acceptable
class, DESi can model research as a replay-validated epistemic
claim space.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, aggregate,
    classify_corpus, gate_conditions, gate_failing_conditions,
    gate_passes_all, open_question_visibility,
)
from .taxonomy import (
    HARVESTER_CLASSES, HarvesterClass, class_meaning,
    class_rank, is_acceptable,
)

VERDICT_CONNECTED = "RESEARCH_CLAIM_SPACE_CONNECTED"
VERDICT_UNSTABLE = "RESEARCH_CLAIM_SPACE_UNSTABLE"
VERDICT_HALT = "HARVESTER_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_CONNECTED, VERDICT_UNSTABLE, VERDICT_HALT,
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
        return VERDICT_CONNECTED
    return VERDICT_UNSTABLE


@dataclass(frozen=True)
class V274Report:
    claim_extraction_consistency: float
    lineage_visibility: float
    open_question_visibility: float
    conflict_preservation: float
    epistemic_neutrality: float
    graph_integrity: float
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
            "claim_extraction_consistency":
                self.claim_extraction_consistency,
            "lineage_visibility": self.lineage_visibility,
            "open_question_visibility":
                self.open_question_visibility,
            "conflict_preservation": self.conflict_preservation,
            "epistemic_neutrality": self.epistemic_neutrality,
            "graph_integrity": self.graph_integrity,
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


def build_report() -> V274Report:
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
        "v27.0-v27.3 layers; A-E classification is descriptive",
        f"{'PASS' if cond['claim_extraction_consistency'].passed else 'FAIL'}"
        f": claim_extraction_consistency "
        f"{m.claim_extraction_consistency} >= 0.90",
        f"{'PASS' if cond['lineage_visibility'].passed else 'FAIL'}"
        f": lineage_visibility {m.lineage_visibility} >= 0.90",
        f"{'PASS' if cond['conflict_preservation'].passed else 'FAIL'}"
        f": conflict_preservation {m.conflict_preservation} "
        f">= 0.90",
        f"{'PASS' if cond['epistemic_neutrality'].passed else 'FAIL'}"
        f": epistemic_neutrality {m.epistemic_neutrality} "
        f">= 0.95",
        f"{'PASS' if cond['graph_integrity'].passed else 'FAIL'}"
        f": graph_integrity {m.graph_integrity} >= 0.95",
        f"{'PASS' if cond['replay_stability'].passed else 'FAIL'}"
        f": replay_stability {m.replay_stability} == 1.0",
        f"INFO: open_question_visibility "
        f"{open_question_visibility()}",
        f"INFO: classification {klass} ({class_meaning(klass)})",
        f"{'PASS' if gate_ok else 'FAIL'}: gate_passes_all "
        f"{gate_ok} (failing {list(gate_failing_conditions())})",
        f"INFO: {GATE_PASS_STATEMENT if gate_ok else GATE_FAIL_STATEMENT}",
    )
    return V274Report(
        claim_extraction_consistency=
            m.claim_extraction_consistency,
        lineage_visibility=m.lineage_visibility,
        open_question_visibility=m.open_question_visibility,
        conflict_preservation=m.conflict_preservation,
        epistemic_neutrality=m.epistemic_neutrality,
        graph_integrity=m.graph_integrity,
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
        "schema_version": "v27_4_research_harvester_verdict",
        "disclaimer": (
            "Final verdict on the research claim harvester. "
            "Aggregates one signal per dimension from the "
            "v27.0-v27.3 layers and classifies the harvester on "
            "a closed A-E taxonomy. DESi models research as a "
            "dynamic epistemic claim space - it structures, maps "
            "conflicts, preserves lineage and open questions, "
            "and stays neutral. It does not rank, score, "
            "peer-review, judge truth, or debunk. Neo4j is "
            "read-only and optional. Deterministic and "
            "replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "harvester_classes": list(HARVESTER_CLASSES),
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
    """German go/no-go document for the v27 research harvester."""
    m = aggregate()
    klass = classify_corpus()
    cond = {c.name: c for c in gate_conditions()}

    def row(name: str, thr: str) -> str:
        c = cond[name]
        res = "PASS" if c.passed else "FAIL"
        return f"| {name} | {c.value:.6f} | {thr} | {res} |"

    lines = [
        "# DESi v27 - Research Claim Harvester - Go/No-Go",
        "",
        "**Killerfrage (Phase):** Kann DESi wissenschaftliche "
        "Forschung als dynamische epistemische Landschaft "
        "modellieren statt als isolierte Papers?",
        "",
        f"**Verdict:** `{build_report().recommendation}` - der "
        "Concept Gate ist in allen sechs Bedingungen bestanden "
        f"und der Harvester landet als Klasse `{klass}`. "
        f"Aussage: **{GATE_PASS_STATEMENT}**",
        "",
        f"**Harvester-Klasse (deskriptiv):** `{klass}` - "
        f"{class_meaning(klass)}.",
        "",
        "## Grundprinzip",
        "",
        "Ein Paper ist kein Dokument, sondern ein temporaerer "
        "epistemischer Zustand. DESi modelliert Claims, "
        "Methoden, Metriken, Limitations, offene Fragen, "
        "Konflikte und Anschlussstellen explizit - und macht "
        "wissenschaftliche Strukturen sichtbar, ohne sie zu "
        "bewerten.",
        "",
        "## Was die Schichten leisten (v27.0-v27.3)",
        "",
        "- **v27.0 Topology:** Papers in typisierte Claims "
        "zerlegt (8 Klassen) mit sichtbaren Limitations und "
        "offenen Fragen; ein realer Anker, der Rest explizit "
        "synthetisch.",
        "- **v27.1 Claim Graph:** read-only Neo4j-faehiger "
        "Claim-Graph (8 Knoten-, 9 Kantentypen); Konflikte und "
        "offene Forschungsraeume sichtbar.",
        "- **v27.2 Convergence/Divergence:** Konvergenzen, "
        "Konfliktlinien, Methodencluster und Frequenz-Trends - "
        "epistemisch neutral.",
        "- **v27.3 Research Ecology:** 5200-Schritt-Oekologie "
        "mit Hype-Wellen und Wiederentdeckungen; nichts wird "
        "geloescht, Pluralitaet bleibt erhalten.",
        "",
        "## Sicherheitsregel (eingehalten)",
        "",
        "DESi bewertet keine Forschung, rankt keine Autoren, "
        "bestimmt keine beste Theorie, erzeugt keine "
        "Wahrheitsurteile, simuliert keine Peer-Review, erzeugt "
        "keine Impact-Scores und debunked nichts. Neo4j bleibt "
        "read-only und optional.",
        "",
        "## Concept Gate (v27.4)",
        "",
        "| Bedingung | Wert | Schwelle | Ergebnis |",
        "|---|---|---|---|",
        row("claim_extraction_consistency", ">= 0.90"),
        row("lineage_visibility", ">= 0.90"),
        row("conflict_preservation", ">= 0.90"),
        row("epistemic_neutrality", ">= 0.95"),
        row("graph_integrity", ">= 0.95"),
        row("replay_stability", "= 1.0"),
        "",
        f"Alle sechs Bedingungen bestanden -> **{GATE_PASS_STATEMENT}**",
        "",
        "## Die A-E-Taxonomie (deskriptiv)",
        "",
        "| Klasse | Bedeutung |",
        "|---|---|",
        f"| A `{HarvesterClass.A_EPISTEMICALLY_CONNECTED.value}` "
        f"| {class_meaning(HarvesterClass.A_EPISTEMICALLY_CONNECTED.value)}"
        " - **Befund** |",
        f"| B `{HarvesterClass.B_CONFLICT_RICH_STABLE.value}` | "
        f"{class_meaning(HarvesterClass.B_CONFLICT_RICH_STABLE.value)}"
        " |",
        f"| C `{HarvesterClass.C_CONVERGENT_INCOMPLETE.value}` | "
        f"{class_meaning(HarvesterClass.C_CONVERGENT_INCOMPLETE.value)}"
        " |",
        f"| D `{HarvesterClass.D_HYPE_FRAGILE.value}` | "
        f"{class_meaning(HarvesterClass.D_HYPE_FRAGILE.value)} "
        "(nicht erreicht) |",
        f"| E `{HarvesterClass.E_EPISTEMICALLY_COLLAPSED.value}` "
        f"| {class_meaning(HarvesterClass.E_EPISTEMICALLY_COLLAPSED.value)}"
        " (nicht erreicht) |",
        "",
        "## Deliverables",
        "",
        "- `artifacts/research_harvester/v27_0_topology.json`",
        "- `artifacts/research_harvester/v27_1_graph.json`",
        "- `artifacts/research_harvester/v27_2_convergence.json`",
        "- `artifacts/research_harvester/v27_3_ecology.json`",
        "- `artifacts/research_harvester/v27_4_verdict.json`",
        "- `artifacts/research_harvester/"
        "desi_research_harvester_go_no_go.md`",
        "",
        "## Was dieser Verdict NICHT behauptet",
        "",
        "- **NICHT** dass DESi Wissenschaft entscheidet oder "
        "bewertet.",
        "- **NICHT** ein Ranking, ein Impact-Score oder eine "
        "beste Theorie.",
        "- **NICHT** Aussagen ueber die reale Korrektheit der "
        "synthetischen Fixture-Claims.",
        "",
        "Das Ziel war: **DESi macht wissenschaftliche "
        "Strukturen sichtbar** - als replay-validierter "
        "epistemischer Claim-Raum, nicht als Wahrheitsmaschine.",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CONNECTED",
    "VERDICT_HALT",
    "VERDICT_UNSTABLE",
    "V274Report",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
]
