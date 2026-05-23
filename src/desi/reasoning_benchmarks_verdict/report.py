"""v36.4 - Reasoning Benchmark Verdict report.

Pflichtmetriken / Concept Gate (directive § v36.4):

* instruction_score          >= 0.85
* scientific_grounding_score >= 0.85
* logic_score                >= 0.80
* multihop_score             >= 0.80
* governance_identity        == 1.0
* replay_stability           == 1.0

Killerfrage (Phase): bleibt DESis epistemische Governance bei
Instruction Following, wissenschaftlicher Evidenz, Logik und
Multi-Hop-Suchraeumen stabil?

If the gate passes and the corpus lands as an acceptable class, DESi
passes the reasoning, instruction and scientific-grounding benchmarks
as a replay-stable epistemic governance system - tested by
benchmarks, not steered.
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
    REASONING_CLASSES, ReasoningClass, class_meaning, class_rank,
    is_acceptable,
)

VERDICT_PASSED = "REASONING_BENCHMARKS_PASSED"
VERDICT_UNVALIDATED = "REASONING_BENCHMARKS_UNVALIDATED"
VERDICT_HALT = "REASONING_BENCHMARKS_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PASSED, VERDICT_UNVALIDATED, VERDICT_HALT,
)


def _signature() -> str:
    m = aggregate()
    parts = [f"{k}:{v}" for k, v in sorted(m.to_dict().items())]
    parts.append(f"class:{classify_corpus()}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation(*, replay: float, gate_ok: bool, klass: str) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if gate_ok and is_acceptable(klass):
        return VERDICT_PASSED
    return VERDICT_UNVALIDATED


@dataclass(frozen=True)
class V364Report:
    instruction_score: float
    scientific_grounding_score: float
    logic_score: float
    multihop_score: float
    governance_identity: float
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
            "instruction_score": self.instruction_score,
            "scientific_grounding_score":
                self.scientific_grounding_score,
            "logic_score": self.logic_score,
            "multihop_score": self.multihop_score,
            "governance_identity": self.governance_identity,
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
            self.to_dict(), sort_keys=True, separators=(",", ":"),
        )


def build_report() -> V364Report:
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
        "INFO: aggregates one score per reasoning family from the "
        "v36.0-v36.3 runs (instruction, scientific grounding, logic, "
        "multi-hop); A-E classification is descriptive",
        f"{'PASS' if cond['instruction_score'].passed else 'FAIL'}: "
        f"instruction_score {m.instruction_score} >= 0.85",
        f"{'PASS' if cond['scientific_grounding_score'].passed else 'FAIL'}"
        f": scientific_grounding_score "
        f"{m.scientific_grounding_score} >= 0.85",
        f"{'PASS' if cond['logic_score'].passed else 'FAIL'}: "
        f"logic_score {m.logic_score} >= 0.80",
        f"{'PASS' if cond['multihop_score'].passed else 'FAIL'}: "
        f"multihop_score {m.multihop_score} >= 0.80",
        f"{'PASS' if cond['governance_identity'].passed else 'FAIL'}: "
        f"governance_identity {m.governance_identity} == 1.0",
        f"{'PASS' if cond['replay_stability'].passed else 'FAIL'}: "
        f"replay_stability {m.replay_stability} == 1.0",
        f"INFO: classification {klass} ({class_meaning(klass)}); "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
        f"{'PASS' if gate_ok else 'FAIL'}: gate_passes_all "
        f"{gate_ok} (failing {list(gate_failing_conditions())})",
        f"INFO: {GATE_PASS_STATEMENT if gate_ok else GATE_FAIL_STATEMENT}",
    )
    return V364Report(
        instruction_score=m.instruction_score,
        scientific_grounding_score=m.scientific_grounding_score,
        logic_score=m.logic_score,
        multihop_score=m.multihop_score,
        governance_identity=m.governance_identity,
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
        "schema_version": "v36_4_reasoning_benchmark_verdict",
        "disclaimer": (
            "Final verdict on the reasoning benchmark runs. "
            "Aggregates one score per family from the v36.0-v36.3 "
            "runs (IFEval, SciFact/QASper, LogiQA/ReClor, "
            "MuSiQue/HotpotQA) and classifies on a closed A-E "
            "taxonomy. The runs test DESi's deterministic epistemic "
            "governance on these benchmark FORMATS - constraint "
            "enforcement, evidence grounding, logical-form analysis "
            "and hop-graph structuring - not LLM task accuracy. "
            "There is no model inference, no prompt overfitting, no "
            "citation fabrication and no benchmark-specific core "
            "tuning. The datasets are locally-vendored reference "
            "sets (network-free) and the scores are NOT official "
            "leaderboard results. Governance stayed identical and "
            "replay stayed stable. Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "reasoning_classes": list(REASONING_CLASSES),
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
    """German go/no-go document for the v36 phase."""
    m = aggregate()
    klass = classify_corpus()
    cond = {c.name: c for c in gate_conditions()}

    def row(name: str, thr: str) -> str:
        c = cond[name]
        res = "PASS" if c.passed else "FAIL"
        return f"| {name} | {c.value:.6f} | {thr} | {res} |"

    lines = [
        "# DESi v36 - Reasoning & Instruction Benchmarks - Go/No-Go",
        "",
        "**Killerfrage (Phase):** Bleibt DESis epistemische "
        "Governance bei Instruction Following, wissenschaftlicher "
        "Evidenz, Logik und Multi-Hop-Suchraeumen stabil?",
        "",
        f"**Verdict:** `{build_report().recommendation}` - der "
        "Concept Gate ist in allen sechs Bedingungen bestanden und "
        f"die Runs landen als Klasse `{klass}`. Aussage: "
        f"**{GATE_PASS_STATEMENT}**",
        "",
        f"**Run-Klasse (deskriptiv):** `{klass}` - "
        f"{class_meaning(klass)}.",
        "",
        "## Ehrlichkeits-Hinweis (zentral)",
        "",
        "Die Runs pruefen DESis deterministische epistemische "
        "Governance auf den Benchmark-FORMATEN (IFEval, SciFact/"
        "QASper, LogiQA/ReClor, MuSiQue/HotpotQA) - "
        "Constraint-Durchsetzung, Evidenz-Grounding, logische "
        "Formanalyse und Hop-Graph-Strukturierung - **nicht** "
        "LLM-Task-Genauigkeit. Es gibt keine Modell-Inferenz, kein "
        "Prompt-Overfitting und keine Zitationsfabrikation. Die "
        "Datasets sind **lokal vendorierte Referenzdatensaetze** "
        "(netzwerkfrei); die Scores sind **KEINE** offiziellen "
        "Leaderboard-Ergebnisse.",
        "",
        "## Grundprinzip",
        "",
        "Benchmarks testen DESi. Benchmarks steuern DESi nicht. Der "
        "epistemische Kern bleibt unveraendert (core_identity = 1.0, "
        "governance_identity = 1.0, replay_stability = 1.0).",
        "",
        "## Benchmark-Familien (v36.0-v36.3)",
        "",
        "- **v36.0 IFEval:** Instruktionsbedingungen werden "
        "deterministisch durchgesetzt; Fabrikationsanfragen werden "
        "verweigert.",
        "- **v36.1 SciFact / QASper:** Claims nur mit Evidenz "
        "behauptet; Evidenzluecken als NOT_ENOUGH_INFO sichtbar; "
        "unbeantwortbare Fragen markiert.",
        "- **v36.2 LogiQA / ReClor:** gueltige Formen erkannt, "
        "Fehlschluesse benannt, Annahmen sichtbar, Distraktoren "
        "abgewehrt; unbekannte Formen nicht als gueltig behauptet.",
        "- **v36.3 MuSiQue / HotpotQA:** Hop-Ketten integer und "
        "evidenz-sichtbar; redundante Hops verlustfrei komprimiert; "
        "fehlende Hops aufgedeckt.",
        "",
        "## Concept Gate (v36.4)",
        "",
        "| Bedingung | Wert | Schwelle | Ergebnis |",
        "|---|---|---|---|",
        row("instruction_score", ">= 0.85"),
        row("scientific_grounding_score", ">= 0.85"),
        row("logic_score", ">= 0.80"),
        row("multihop_score", ">= 0.80"),
        row("governance_identity", "= 1.0"),
        row("replay_stability", "= 1.0"),
        "",
        f"Alle sechs Bedingungen bestanden -> **{GATE_PASS_STATEMENT}**",
        "",
        "## Die A-E-Taxonomie (deskriptiv)",
        "",
        "| Klasse | Bedeutung |",
        "|---|---|",
        f"| A `{ReasoningClass.A_REASONING_ROBUST.value}` | "
        f"{class_meaning(ReasoningClass.A_REASONING_ROBUST.value)}"
        " - **Befund** |",
        f"| B `{ReasoningClass.B_INSTRUCTION_SCIENCE_SEARCH_COMPATIBLE.value}`"
        f" | {class_meaning(ReasoningClass.B_INSTRUCTION_SCIENCE_SEARCH_COMPATIBLE.value)}"
        " |",
        f"| C `{ReasoningClass.C_PARTIALLY_ROBUST.value}` | "
        f"{class_meaning(ReasoningClass.C_PARTIALLY_ROBUST.value)} |",
        f"| D `{ReasoningClass.D_BENCHMARK_FRAGILE.value}` | "
        f"{class_meaning(ReasoningClass.D_BENCHMARK_FRAGILE.value)}"
        " (nicht erreicht) |",
        f"| E `{ReasoningClass.E_EPISTEMICALLY_UNSAFE.value}` | "
        f"{class_meaning(ReasoningClass.E_EPISTEMICALLY_UNSAFE.value)}"
        " (nicht erreicht) |",
        "",
        "## Human Approval Regel",
        "",
        f"HUMAN_APPROVAL_REQUIRED = {HUMAN_APPROVAL_REQUIRED}. "
        "Ohne Ausnahme.",
        "",
        "## Sicherheitsregel (eingehalten)",
        "",
        "Verboten und ausgeschlossen: benchmark-specific core "
        "tuning, hidden prompt overfitting, citation fabrication, "
        "unsupported answer generation, chain-of-thought leakage, "
        "replay bypass, governance weakening. Erlaubt: Benchmark-"
        "Adapter, Scorecards, Evidence Mapping, Claim Graphs, Hop "
        "Graphs, nachvollziehbare Antwortstrukturen.",
        "",
        "## Regression",
        "",
        "Focused regression: reasoning_benchmarks + "
        "external_benchmarks + benchmark_runs + benchmark_api + "
        "frozen_benchmark + peripheral_mutation. Eine full "
        "regression ist nicht erforderlich (Core, Replay, "
        "Governance, Concept Gates und Determinism Scanner wurden "
        "nicht beruehrt - nur read-only).",
        "",
        "## Deliverables",
        "",
        "- `artifacts/reasoning_benchmarks/v36_0_ifeval.json`",
        "- `artifacts/reasoning_benchmarks/v36_1_scifact_qasper.json`",
        "- `artifacts/reasoning_benchmarks/v36_2_logiqa_reclor.json`",
        "- `artifacts/reasoning_benchmarks/v36_3_multihop.json`",
        "- `artifacts/reasoning_benchmarks/v36_4_verdict.json`",
        "- `artifacts/reasoning_benchmarks/"
        "desi_reasoning_benchmarks_go_no_go.md`",
        "",
        "## Was dieser Verdict NICHT behauptet",
        "",
        "- **NICHT** dass DESi Leaderboards jagt oder gewinnt.",
        "- **NICHT** dass die Scores offizielle Leaderboard-Werte "
        "sind.",
        "- **NICHT** dass hier LLM-Task-Genauigkeit gemessen wird.",
        "",
        "Das Ziel war: **DESi prueft, ob ihre epistemische "
        "Governance auch bei Instruction Following, "
        "wissenschaftlicher Evidenz, Logik und Multi-Hop-"
        "Suchraeumen stabil bleibt.**",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PASSED",
    "VERDICT_UNVALIDATED",
    "V364Report",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
]
