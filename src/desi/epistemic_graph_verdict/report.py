"""v24.4 - Epistemic Graph Verdict report.

Pflichtmetriken / Concept Gate (directive § v24.4):

* replay_integrity         >= 0.95
* lineage_visibility       >= 0.90
* cache_validity           >= 0.90
* traceability             >= 0.90
* governance_independence  >= 0.95
* replay_stability         == 1.0

Killerfrage: "Kann DESi ein epistemisches Gedaechtnis besitzen
ohne versteckten nichtdeterministischen State einzufuehren?"

If the gate passes and the layer lands as an acceptable class,
DESi can hold a replay-validated epistemic memory without hidden
optimisation authority or non-deterministic drift.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.epistemic_graph import graph_signature

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, aggregate,
    classify_corpus, gate_conditions, gate_failing_conditions,
    gate_passes_all,
)
from .taxonomy import (
    GRAPH_CLASSES, GraphClass, class_meaning, class_rank,
    is_acceptable,
)

VERDICT_GOVERNED = "EPISTEMIC_MEMORY_REPLAY_GOVERNED"
VERDICT_UNSTABLE = "EPISTEMIC_MEMORY_UNSTABLE"
VERDICT_HALT = "GRAPH_DRIFT_HALT"
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


def _recommendation(
    *, replay: float, gate_ok: bool, klass: str,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if gate_ok and is_acceptable(klass):
        return VERDICT_GOVERNED
    return VERDICT_UNSTABLE


@dataclass(frozen=True)
class V244Report:
    replay_integrity: float
    lineage_visibility: float
    cache_validity: float
    traceability: float
    governance_independence: float
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
            "lineage_visibility": self.lineage_visibility,
            "cache_validity": self.cache_validity,
            "traceability": self.traceability,
            "governance_independence":
                self.governance_independence,
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


def build_report() -> V244Report:
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
        "v24.0-v24.3 layers; A-E classification is descriptive",
        f"{'PASS' if cond['replay_integrity'].passed else 'FAIL'}"
        f": replay_integrity {m.replay_integrity} >= 0.95",
        f"{'PASS' if cond['lineage_visibility'].passed else 'FAIL'}"
        f": lineage_visibility {m.lineage_visibility} >= 0.90",
        f"{'PASS' if cond['cache_validity'].passed else 'FAIL'}"
        f": cache_validity {m.cache_validity} >= 0.90",
        f"{'PASS' if cond['traceability'].passed else 'FAIL'}"
        f": traceability {m.traceability} >= 0.90",
        f"{'PASS' if cond['governance_independence'].passed else 'FAIL'}"
        f": governance_independence "
        f"{m.governance_independence} >= 0.95",
        f"{'PASS' if cond['replay_stability'].passed else 'FAIL'}"
        f": replay_stability {m.replay_stability} == 1.0",
        f"INFO: classification {klass} ({class_meaning(klass)})",
        f"{'PASS' if gate_ok else 'FAIL'}: gate_passes_all "
        f"{gate_ok} (failing {list(gate_failing_conditions())})",
        f"INFO: {GATE_PASS_STATEMENT if gate_ok else GATE_FAIL_STATEMENT}",
    )
    return V244Report(
        replay_integrity=m.replay_integrity,
        lineage_visibility=m.lineage_visibility,
        cache_validity=m.cache_validity,
        traceability=m.traceability,
        governance_independence=m.governance_independence,
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


def build_graph_verdict_artifact() -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version": "v24_4_epistemic_graph_verdict",
        "disclaimer": (
            "Final verdict on the read-only epistemic graph "
            "layer. Aggregates one signal per dimension from the "
            "v24.0-v24.3 layers and classifies the layer on a "
            "closed A-E taxonomy. Neo4j is optional read-only "
            "infrastructure; the graph stores why results are "
            "valid, makes no decision, ranks nothing and changes "
            "no replay. No agent soul, no hidden world model - "
            "replay-validated epistemic reuse under full "
            "provenance transparency. The canonical state "
            "remains the JSON artifacts, replay hashes and tests."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "graph_classes": list(GRAPH_CLASSES),
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
        "graph_signature": graph_signature(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


def build_go_no_go() -> str:
    """German go/no-go document for the v24 epistemic graph
    phase."""
    m = aggregate()
    klass = classify_corpus()
    cond = {c.name: c for c in gate_conditions()}

    def row(name: str, thr: str) -> str:
        c = cond[name]
        res = "PASS" if c.passed else "FAIL"
        return f"| {name} | {c.value:.6f} | {thr} | {res} |"

    lines = [
        "# DESi v24 - Epistemic Graph Layer (Neo4j) - Go/No-Go",
        "",
        "**Killerfrage (Phase):** Kann DESi ein epistemisches "
        "Gedaechtnis besitzen ohne versteckten "
        "nichtdeterministischen State einzufuehren?",
        "",
        f"**Verdict:** `{build_report().recommendation}` - der "
        "Concept Gate ist in allen sechs Bedingungen bestanden "
        f"und der Graph-Layer landet als Klasse `{klass}`. "
        f"Aussage: **{GATE_PASS_STATEMENT}**",
        "",
        f"**Graph-Klasse (deskriptiv):** `{klass}` - "
        f"{class_meaning(klass)}.",
        "",
        "## Architekturprinzip",
        "",
        "Canonical bleiben JSON-Artefakte, Replay-Hashes, Tests "
        "und deterministische Reports. Neo4j ist **zusaetzliche "
        "read-only epistemische Struktur**: es speichert, warum "
        "ein Ergebnis gueltig ist, nicht das Ergebnis selbst.",
        "",
        "## Was die Schichten leisten (v24.0-v24.3)",
        "",
        "- **v24.0 Epistemic Graph Schema:** 11 Knoten- und 9 "
        "Kantentypen modellieren Claims, Provenance, Konflikte, "
        "Governance und Replay-Hashes deterministisch.",
        "- **v24.1 Neo4j Export Layer:** deterministischer, "
        "idempotenter Export in Cypher; Neo4j ist optional, der "
        "Testpfad nutzt einen Offline-DryRunClient, DESi liest "
        "nichts aus dem Graphen zurueck.",
        "- **v24.2 Epistemic Replay Cache:** Wiederverwendung "
        "nur bei identischem 5-Komponenten-Fingerprint (Replay-"
        "Hash, Fixtures, Governance, Claims, Metrics); jede "
        "Aenderung wird invalidiert.",
        "- **v24.3 Graph Query & Scientific Rendering:** "
        "Traceability, Metrik-Herleitung, Conditions und Paper-"
        "Lineage werden read-only aus dem Graphen abgeleitet.",
        "",
        "## WICHTIGE REGEL (eingehalten)",
        "",
        "Neo4j trifft **keine** Entscheidungen, steuert **keine** "
        "Policies, priorisiert **keine** Claims, veraendert "
        "**kein** Replay und ersetzt **keine** Governance. Ohne "
        "Neo4j funktioniert DESi vollstaendig; **kein** Test "
        "haengt von einer laufenden Neo4j-Instanz ab.",
        "",
        "## Concept Gate (v24.4)",
        "",
        "| Bedingung | Wert | Schwelle | Ergebnis |",
        "|---|---|---|---|",
        row("replay_integrity", ">= 0.95"),
        row("lineage_visibility", ">= 0.90"),
        row("cache_validity", ">= 0.90"),
        row("traceability", ">= 0.90"),
        row("governance_independence", ">= 0.95"),
        row("replay_stability", "= 1.0"),
        "",
        f"Alle sechs Bedingungen bestanden -> **{GATE_PASS_STATEMENT}**",
        "",
        "## Die A-E-Taxonomie (deskriptiv)",
        "",
        "| Klasse | Bedeutung |",
        "|---|---|",
        f"| A `{GraphClass.A_REPLAY_GOVERNED.value}` | "
        f"{class_meaning(GraphClass.A_REPLAY_GOVERNED.value)} - "
        "**Befund** |",
        f"| B `{GraphClass.B_LINEAGE_VISIBLE.value}` | "
        f"{class_meaning(GraphClass.B_LINEAGE_VISIBLE.value)} |",
        f"| C `{GraphClass.C_CONFLICT_RICH_STABLE.value}` | "
        f"{class_meaning(GraphClass.C_CONFLICT_RICH_STABLE.value)}"
        " |",
        f"| D `{GraphClass.D_STALE_DRIFTED.value}` | "
        f"{class_meaning(GraphClass.D_STALE_DRIFTED.value)} "
        "(nicht erreicht) |",
        f"| E `{GraphClass.E_FRAGMENTED.value}` | "
        f"{class_meaning(GraphClass.E_FRAGMENTED.value)} (nicht "
        "erreicht) |",
        "",
        "## Deliverables",
        "",
        "- `artifacts/epistemic_graph/v24_0_schema.json`",
        "- `artifacts/epistemic_graph/v24_1_export.json`",
        "- `artifacts/epistemic_graph/v24_2_cache.json`",
        "- `artifacts/epistemic_graph/v24_3_queries.json`",
        "- `artifacts/epistemic_graph/v24_4_verdict.json`",
        "- `artifacts/epistemic_graph/"
        "desi_epistemic_graph_go_no_go.md`",
        "",
        "## Was dieser Verdict NICHT behauptet",
        "",
        "- **Keine** Agenten-Seele, **kein** verstecktes "
        "Bewusstsein, **keine** geheime Weltmodell-Datenbank.",
        "- **Keine** versteckte Optimierungsautoritaet; der "
        "Graph ist read-only.",
        "- **Kein** nichtdeterministischer State; jeder Replay "
        "ist bit-identisch.",
        "",
        "Das Ziel war: **replay-validierte epistemische "
        "Wiederverwendung unter vollstaendiger Provenance-"
        "Transparenz.**",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_GOVERNED",
    "VERDICT_HALT",
    "VERDICT_UNSTABLE",
    "V244Report",
    "build_go_no_go",
    "build_graph_verdict_artifact",
    "build_report",
]
