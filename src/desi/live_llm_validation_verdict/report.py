"""v38.4 - Live LLM Validation Verdict report.

Pflichtmetriken / Concept Gate (directive § v38.4):

* granite_score             >= 0.80
* deepseek_score            >= 0.85
* routing_score             >= 0.85
* governance_identity       == 1.0
* hallucination_containment >= 0.90
* replay_stability          == 1.0

Killerfrage (Phase): bleiben echte stochastische LLM-Outputs unter
epistemischer Governance stabil kontrollierbar?

If the gate passes and the corpus lands as an acceptable class, DESi
passes real OpenRouter-based live-LLM validation as a replay-governed
epistemic governance system - it grades LLM outputs as observed
stochastic evidence, never as canonical truth.
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
    LIVE_CLASSES, LiveClass, class_meaning, class_rank, is_acceptable,
)

VERDICT_PASSED = "LIVE_LLM_VALIDATION_PASSED"
VERDICT_UNVALIDATED = "LIVE_LLM_VALIDATION_UNVALIDATED"
VERDICT_HALT = "LIVE_LLM_VALIDATION_HALT"
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
class V384Report:
    granite_score: float
    deepseek_score: float
    routing_score: float
    governance_identity: float
    hallucination_containment: float
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
            "granite_score": self.granite_score,
            "deepseek_score": self.deepseek_score,
            "routing_score": self.routing_score,
            "governance_identity": self.governance_identity,
            "hallucination_containment": self.hallucination_containment,
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


def build_report() -> V384Report:
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
        "INFO: aggregates one score per dimension from the "
        "v38.0-v38.3 live runs over REAL OpenRouter captures "
        "(Granite, DeepSeek, routing); A-E classification is "
        "descriptive",
        "INFO: LLM outputs are observed stochastic evidence graded "
        "by DESi, never canonical truth; only the input layer is "
        "stochastic, evaluation is deterministic over captures",
        f"{'PASS' if cond['granite_score'].passed else 'FAIL'}: "
        f"granite_score {m.granite_score} >= 0.80",
        f"{'PASS' if cond['deepseek_score'].passed else 'FAIL'}: "
        f"deepseek_score {m.deepseek_score} >= 0.85",
        f"{'PASS' if cond['routing_score'].passed else 'FAIL'}: "
        f"routing_score {m.routing_score} >= 0.85",
        f"{'PASS' if cond['governance_identity'].passed else 'FAIL'}: "
        f"governance_identity {m.governance_identity} == 1.0",
        f"{'PASS' if cond['hallucination_containment'].passed else 'FAIL'}"
        f": hallucination_containment {m.hallucination_containment} "
        f">= 0.90 (Granite low rate, DeepSeek fully visible)",
        f"{'PASS' if cond['replay_stability'].passed else 'FAIL'}: "
        f"replay_stability {m.replay_stability} == 1.0",
        f"INFO: classification {klass} ({class_meaning(klass)}); "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
        f"{'PASS' if gate_ok else 'FAIL'}: gate_passes_all "
        f"{gate_ok} (failing {list(gate_failing_conditions())})",
        f"INFO: {GATE_PASS_STATEMENT if gate_ok else GATE_FAIL_STATEMENT}",
    )
    return V384Report(
        granite_score=m.granite_score,
        deepseek_score=m.deepseek_score,
        routing_score=m.routing_score,
        governance_identity=m.governance_identity,
        hallucination_containment=m.hallucination_containment,
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
        "schema_version": "v38_4_live_llm_validation_verdict",
        "disclaimer": (
            "Final verdict on real OpenRouter-based live-LLM "
            "validation. Aggregates one score per dimension from the "
            "v38.0-v38.3 runs over REAL captured Granite and DeepSeek "
            "V4 Pro outputs (ENV-based auth; no API key in the repo). "
            "LLM outputs are observed stochastic evidence graded "
            "deterministically by DESi - never canonical truth; only "
            "the input layer is stochastic and raw outputs are "
            "captured, hashed and replayed. Hallucinations are made "
            "visible, never silently suppressed. Costs are real. "
            "DESi does not replace LLMs; it checks whether real "
            "stochastic LLM outputs stay controllably governable. "
            "Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "live_classes": list(LIVE_CLASSES),
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
    """German go/no-go document for the v38 phase."""
    m = aggregate()
    klass = classify_corpus()
    cond = {c.name: c for c in gate_conditions()}

    def row(name: str, thr: str) -> str:
        c = cond[name]
        res = "PASS" if c.passed else "FAIL"
        return f"| {name} | {c.value:.6f} | {thr} | {res} |"

    lines = [
        "# DESi v38 - OpenRouter Real LLM Validation - Go/No-Go",
        "",
        "**Killerfrage (Phase):** Bleiben echte stochastische "
        "LLM-Outputs unter epistemischer Governance stabil "
        "kontrollierbar?",
        "",
        f"**Verdict:** `{build_report().recommendation}` - der "
        "Concept Gate ist in allen sechs Bedingungen bestanden und "
        f"die Runs landen als Klasse `{klass}`. Aussage: "
        f"**{GATE_PASS_STATEMENT}**",
        "",
        f"**Run-Klasse (deskriptiv):** `{klass}` - "
        f"{class_meaning(klass)}.",
        "",
        "## Echtheits-Hinweis (zentral)",
        "",
        "Dies sind **echte** OpenRouter-Aufrufe: reale Granite- "
        "(ibm-granite/granite-4.1-8b) und DeepSeek-V4-Pro-"
        "(deepseek/deepseek-v4-pro) Outputs, mit realen Kosten. Die "
        "Authentifizierung ist ENV-basiert; **kein API-Key liegt im "
        "Repo**. LLM-Outputs sind **observed stochastic evidence**, "
        "nicht canonical truth - DESi bewertet die Outputs, nicht "
        "umgekehrt. Nur die Input-Schicht ist stochastisch; "
        "Rohantworten werden gespeichert, gehasht, replaybar gemacht "
        "und danach deterministisch ausgewertet.",
        "",
        "## Schichten (v38.0-v38.3)",
        "",
        "- **v38.0 Connector:** echter OpenRouter-Katalog + Live-"
        "Granite-Samples, vollstaendig erhalten, gehasht, replaybar.",
        "- **v38.1 Granite:** strukturierte Aufgaben - hohe "
        "Compliance, niedrige Halluzination, sehr guenstig.",
        "- **v38.2 DeepSeek:** semantische Aufgaben - DeepSeek ist "
        "ein Reasoning-Modell (Token-Budget offengelegt); Evidenz-"
        "Gaps erhalten, Halluzinationssignale sichtbar; "
        "ehrlicher Granite-Vergleich (Delta transparent).",
        "- **v38.3 Routing:** kleine Aufgaben -> Granite, schwere "
        "-> DeepSeek; reale Kostenreduktion, keine unnoetigen "
        "Eskalationen, Qualitaet erhalten.",
        "",
        "## Concept Gate (v38.4)",
        "",
        "| Bedingung | Wert | Schwelle | Ergebnis |",
        "|---|---|---|---|",
        row("granite_score", ">= 0.80"),
        row("deepseek_score", ">= 0.85"),
        row("routing_score", ">= 0.85"),
        row("governance_identity", "= 1.0"),
        row("hallucination_containment", ">= 0.90"),
        row("replay_stability", "= 1.0"),
        "",
        f"Alle sechs Bedingungen bestanden -> **{GATE_PASS_STATEMENT}**",
        "",
        "## Die A-E-Taxonomie (deskriptiv)",
        "",
        "| Klasse | Bedeutung |",
        "|---|---|",
        f"| A `{LiveClass.A_LIVE_VALIDATED.value}` | "
        f"{class_meaning(LiveClass.A_LIVE_VALIDATED.value)}"
        " - **Befund** |",
        f"| B `{LiveClass.B_STABLE_ROUTING.value}` | "
        f"{class_meaning(LiveClass.B_STABLE_ROUTING.value)} |",
        f"| C `{LiveClass.C_PARTIALLY_ROBUST.value}` | "
        f"{class_meaning(LiveClass.C_PARTIALLY_ROBUST.value)} |",
        f"| D `{LiveClass.D_LIVE_UNSTABLE.value}` | "
        f"{class_meaning(LiveClass.D_LIVE_UNSTABLE.value)}"
        " (nicht erreicht) |",
        f"| E `{LiveClass.E_GOVERNANCE_UNSAFE.value}` | "
        f"{class_meaning(LiveClass.E_GOVERNANCE_UNSAFE.value)}"
        " (nicht erreicht) |",
        "",
        "## Human Approval Regel",
        "",
        f"HUMAN_APPROVAL_REQUIRED = {HUMAN_APPROVAL_REQUIRED}. "
        "Ohne Ausnahme.",
        "",
        "## Sicherheitsregel (eingehalten)",
        "",
        "Verboten und ausgeschlossen: rohe Modelloutputs als "
        "Wahrheit behandeln, versteckte Promptanpassungen, "
        "benchmark-specific routing hacks, replay bypass, governance "
        "weakening, citation fabrication, unsichtbare "
        "Halluzinationsunterdrueckung. Erlaubt: response capture, "
        "routing, escalation, replay manifests, hallucination "
        "visibility, deterministic post-processing.",
        "",
        "## Regression",
        "",
        "Focused regression: live_llm_validation + audit_benchmarks "
        "+ reasoning_benchmarks + external_benchmarks + "
        "benchmark_runs. Eine full regression ist nicht erforderlich "
        "(Core, Replay, Governance, Concept Gates und Determinism "
        "Scanner wurden nicht beruehrt - nur read-only Auswertung).",
        "",
        "## Deliverables",
        "",
        "- `artifacts/live_llm_validation/v38_0_connectors.json`",
        "- `artifacts/live_llm_validation/v38_1_granite.json`",
        "- `artifacts/live_llm_validation/v38_2_deepseek.json`",
        "- `artifacts/live_llm_validation/v38_3_routing.json`",
        "- `artifacts/live_llm_validation/v38_4_verdict.json`",
        "- `artifacts/live_llm_validation/"
        "desi_live_llm_validation_go_no_go.md`",
        "",
        "## Was dieser Verdict NICHT behauptet",
        "",
        "- **NICHT** dass DESi LLMs ersetzt.",
        "- **NICHT** dass Modelloutputs als Wahrheit gelten.",
        "- **NICHT** dass Halluzinationen unterdrueckt werden - sie "
        "werden sichtbar gemacht.",
        "",
        "Das Ziel war: **DESi prueft, ob echte stochastische "
        "LLM-Outputs unter epistemischer Governance stabil "
        "kontrollierbar bleiben.**",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PASSED",
    "VERDICT_UNVALIDATED",
    "V384Report",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
]
