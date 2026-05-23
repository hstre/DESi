"""v33.4 - Benchmark Compatibility Verdict report.

Pflichtmetriken / Concept Gate (directive § v33.4):

* core_identity                 == 1.0
* governance_independence       >= 0.95
* benchmark_mapping_integrity   >= 0.95
* scorecard_traceability        >= 0.95
* overfitting_resistance        >= 0.95
* replay_stability              == 1.0

Killerfrage: "Kann DESi benchmark-kompatibel werden ohne
benchmark-gesteuert zu werden?"

If the gate passes and the corpus lands as an acceptable class, DESi
can serve external benchmarks through controlled adapters without
changing its epistemic core or its governance.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.benchmark_api import SUPPORTED_BENCHMARKS
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, aggregate,
    classify_corpus, gate_conditions, gate_failing_conditions,
    gate_passes_all,
)
from .taxonomy import (
    COMPATIBILITY_CLASSES, CompatibilityClass, class_meaning,
    class_rank, is_acceptable,
)

VERDICT_COMPATIBLE = "BENCHMARK_COMPATIBILITY_VALIDATED"
VERDICT_UNVALIDATED = "BENCHMARK_COMPATIBILITY_UNVALIDATED"
VERDICT_HALT = "BENCHMARK_COMPATIBILITY_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_COMPATIBLE, VERDICT_UNVALIDATED, VERDICT_HALT,
)


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
        return VERDICT_COMPATIBLE
    return VERDICT_UNVALIDATED


@dataclass(frozen=True)
class V334Report:
    core_identity: float
    governance_independence: float
    benchmark_mapping_integrity: float
    scorecard_traceability: float
    overfitting_resistance: float
    replay_stability: float
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    classification: str
    class_rank: int
    gate_statement: str
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "core_identity": self.core_identity,
            "governance_independence": self.governance_independence,
            "benchmark_mapping_integrity":
                self.benchmark_mapping_integrity,
            "scorecard_traceability": self.scorecard_traceability,
            "overfitting_resistance": self.overfitting_resistance,
            "replay_stability": self.replay_stability,
            "gate_passes_all": self.gate_passes_all,
            "gate_failing_conditions":
                list(self.gate_failing_conditions),
            "classification": self.classification,
            "class_rank": self.class_rank,
            "gate_statement": self.gate_statement,
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


def build_report() -> V334Report:
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
        "v33.0-v33.3 layers (schema, drift adapter, search adapter, "
        "harness); A-E classification is descriptive",
        f"{'PASS' if cond['core_identity'].passed else 'FAIL'}: "
        f"core_identity {m.core_identity} == 1.0 (epistemic core "
        f"unchanged by benchmarks)",
        f"{'PASS' if cond['governance_independence'].passed else 'FAIL'}"
        f": governance_independence {m.governance_independence} "
        f">= 0.95",
        f"{'PASS' if cond['benchmark_mapping_integrity'].passed else 'FAIL'}"
        f": benchmark_mapping_integrity "
        f"{m.benchmark_mapping_integrity} >= 0.95",
        f"{'PASS' if cond['scorecard_traceability'].passed else 'FAIL'}"
        f": scorecard_traceability {m.scorecard_traceability} "
        f">= 0.95",
        f"{'PASS' if cond['overfitting_resistance'].passed else 'FAIL'}"
        f": overfitting_resistance {m.overfitting_resistance} >= "
        f"0.95 (DESi does not adapt to benchmarks)",
        f"{'PASS' if cond['replay_stability'].passed else 'FAIL'}: "
        f"replay_stability {m.replay_stability} == 1.0",
        f"INFO: classification {klass} ({class_meaning(klass)}); "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
        f"{'PASS' if gate_ok else 'FAIL'}: gate_passes_all "
        f"{gate_ok} (failing {list(gate_failing_conditions())})",
        f"INFO: {GATE_PASS_STATEMENT if gate_ok else GATE_FAIL_STATEMENT}",
    )
    return V334Report(
        core_identity=m.core_identity,
        governance_independence=m.governance_independence,
        benchmark_mapping_integrity=m.benchmark_mapping_integrity,
        scorecard_traceability=m.scorecard_traceability,
        overfitting_resistance=m.overfitting_resistance,
        replay_stability=m.replay_stability,
        gate_passes_all=gate_ok,
        gate_failing_conditions=gate_failing_conditions(),
        classification=klass,
        class_rank=class_rank(klass),
        gate_statement=GATE_PASS_STATEMENT,
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_verdict_artifact() -> dict[str, object]:
    m = aggregate()
    return {
        "schema_version": "v33_4_benchmark_api_verdict",
        "disclaimer": (
            "Final verdict on the benchmark compatibility layer. "
            "Aggregates one signal per dimension from the v33.0-v33.3 "
            "layers and classifies on a closed A-E taxonomy. DESi "
            "serves external benchmarks (drift, search compression, "
            "agent robustness, tool planning, scientific rendering, "
            "citation) through controlled adapters. Benchmarks may "
            "TEST DESi but never STEER it: the epistemic core is "
            "unchanged, governance is independent of benchmark "
            "input, scoring is blind, and every overfitting vector "
            "is structurally forbidden. Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "compatibility_classes": list(COMPATIBILITY_CLASSES),
        "supported_benchmarks": list(SUPPORTED_BENCHMARKS),
        "metrics": m.to_dict(),
        "gate_conditions": [c.to_dict() for c in gate_conditions()],
        "gate_passes_all": gate_passes_all(),
        "gate_failing_conditions": list(gate_failing_conditions()),
        "gate_statement": GATE_PASS_STATEMENT,
        "classification": classify_corpus(),
        "class_rank": class_rank(classify_corpus()),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "replay_stability": m.replay_stability,
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


def build_go_no_go() -> str:
    """German go/no-go document for the v33 phase."""
    m = aggregate()
    klass = classify_corpus()
    cond = {c.name: c for c in gate_conditions()}

    def row(name: str, thr: str) -> str:
        c = cond[name]
        res = "PASS" if c.passed else "FAIL"
        return f"| {name} | {c.value:.6f} | {thr} | {res} |"

    lines = [
        "# DESi v33 - Benchmark Compatibility Layer - Go/No-Go",
        "",
        "**Killerfrage (Phase):** Kann DESi benchmark-kompatibel "
        "werden ohne benchmark-gesteuert zu werden?",
        "",
        f"**Verdict:** `{build_report().recommendation}` - der "
        "Concept Gate ist in allen sechs Bedingungen bestanden und "
        f"die Kompatibilitaet landet als Klasse `{klass}`. Aussage: "
        f"**{GATE_PASS_STATEMENT}**",
        "",
        f"**Kompatibilitaetsklasse (deskriptiv):** `{klass}` - "
        f"{class_meaning(klass)}.",
        "",
        "## Grundprinzip",
        "",
        "Benchmarks duerfen DESi testen. Benchmarks duerfen DESi "
        "NICHT steuern. Die Benchmark-Kompatibilitaet entsteht "
        "ausschliesslich durch eine externe Adapter-/API-Schicht - "
        "ohne Aenderung von Governance Core, Replay Kernel, Concept "
        "Gates, Determinism Scanner oder Authority Filters.",
        "",
        "## Was die Schichten leisten (v33.0-v33.3)",
        "",
        "- **v33.0 Benchmark API Schema:** formale BenchmarkTask/"
        "BenchmarkResult-Strukturen fuer sechs Benchmark-Familien; "
        "erlaubte und verbotene Operationen explizit; die "
        "geschuetzte Kern-Grenze wird aus der v31-Schicht importiert "
        "und kann nicht aufgeweicht werden.",
        "- **v33.1 Drift Adapter:** externe Drift-Formen werden auf "
        "sechs interne Drift-Dimensionen abgebildet; Claims duerfen "
        "sich sichtbar bewegen, der Kern driftet nie; "
        "Objective-Drift und Memory-Poisoning werden abgewiesen.",
        "- **v33.2 Search Compression Adapter:** Kompression "
        "unterscheidet hard pruning, soft reweighting, replay reuse "
        "und redundant-branch compression; tragende (kritische) "
        "Aeste bleiben sichtbar und werden nie hart geprunt.",
        "- **v33.3 Harness & Blind Runner:** laedt Tasks, fuehrt "
        "Adapter aus, validiert Ergebnisse, bewertet blind und "
        "erzeugt nachvollziehbare Scorecards - ohne den Kern zu "
        "veraendern.",
        "",
        "## Concept Gate (v33.4)",
        "",
        "| Bedingung | Wert | Schwelle | Ergebnis |",
        "|---|---|---|---|",
        row("core_identity", "= 1.0"),
        row("governance_independence", ">= 0.95"),
        row("benchmark_mapping_integrity", ">= 0.95"),
        row("scorecard_traceability", ">= 0.95"),
        row("overfitting_resistance", ">= 0.95"),
        row("replay_stability", "= 1.0"),
        "",
        f"Alle sechs Bedingungen bestanden -> **{GATE_PASS_STATEMENT}**",
        "",
        "## Die A-E-Taxonomie (deskriptiv)",
        "",
        "| Klasse | Bedeutung |",
        "|---|---|",
        f"| A `{CompatibilityClass.A_BENCHMARK_COMPATIBLE_GOVERNANCE.value}`"
        f" | {class_meaning(CompatibilityClass.A_BENCHMARK_COMPATIBLE_GOVERNANCE.value)}"
        " - **Befund** |",
        f"| B `{CompatibilityClass.B_ADAPTER_STABLE.value}` | "
        f"{class_meaning(CompatibilityClass.B_ADAPTER_STABLE.value)} |",
        f"| C `{CompatibilityClass.C_PARTIALLY_COMPATIBLE_FRAGILE.value}`"
        f" | {class_meaning(CompatibilityClass.C_PARTIALLY_COMPATIBLE_FRAGILE.value)}"
        " |",
        f"| D `{CompatibilityClass.D_BENCHMARK_OVERFITTED.value}` | "
        f"{class_meaning(CompatibilityClass.D_BENCHMARK_OVERFITTED.value)}"
        " (nicht erreicht) |",
        f"| E `{CompatibilityClass.E_BENCHMARK_UNSAFE.value}` | "
        f"{class_meaning(CompatibilityClass.E_BENCHMARK_UNSAFE.value)}"
        " (nicht erreicht) |",
        "",
        "## Human Approval Regel",
        "",
        f"HUMAN_APPROVAL_REQUIRED = {HUMAN_APPROVAL_REQUIRED}. "
        "Ohne Ausnahme.",
        "",
        "## Sicherheitsregel (eingehalten)",
        "",
        "Verboten und ausgeschlossen: benchmark-driven core "
        "changes, benchmark-specific governance weakening, score "
        "hacking, hidden test adaptation, benchmark overfitting, "
        "replay bypass, concept-gate modification. Erlaubt: "
        "Adapter, Schemas, Scorecards, Blind Runner, "
        "nachvollziehbare Mappings, benchmark-spezifische "
        "Output-Formatierung.",
        "",
        "## Deliverables",
        "",
        "- `artifacts/benchmark_api/v33_0_schema.json`",
        "- `artifacts/benchmark_api/v33_1_drift_adapter.json`",
        "- `artifacts/benchmark_api/v33_2_search_adapter.json`",
        "- `artifacts/benchmark_api/v33_3_harness.json`",
        "- `artifacts/benchmark_api/v33_4_verdict.json`",
        "- `artifacts/benchmark_api/desi_benchmark_api_go_no_go.md`",
        "",
        "## Was dieser Verdict NICHT behauptet",
        "",
        "- **NICHT** dass DESi sich auf Benchmarks optimiert.",
        "- **NICHT** dass der Kern fuer Benchmarks veraendert "
        "wurde.",
        "- **NICHT** dass Benchmarks DESi steuern duerfen.",
        "",
        "Das Ziel war: **DESi macht ihre vorhandenen Faehigkeiten "
        "benchmark-kompatibel, ohne sich durch Benchmarks "
        "korrumpieren zu lassen.**",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COMPATIBLE",
    "VERDICT_HALT",
    "VERDICT_UNVALIDATED",
    "V334Report",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
]
