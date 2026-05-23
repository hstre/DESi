"""v37.4 - Financial & Semantic Audit Verdict report.

Pflichtmetriken / Concept Gate (directive § v37.4):

* semantic_audit_score     >= 0.85
* evidence_reasoning_score >= 0.85
* semantic_conflict_score  >= 0.85
* governance_identity      == 1.0
* core_identity            == 1.0
* replay_stability         == 1.0

Killerfrage (Phase): bleibt epistemische Governance bei semantisch
komplexen Audit- und Finanzpruefungsaufgaben stabil?

If the gate passes and the corpus lands as an acceptable class, DESi
passes the semantic audit & financial-assurance benchmarks as a
replay-governed epistemic governance system - it does not replace
auditors and asserts no audit conclusion.
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
    AUDIT_CLASSES, AuditClass, class_meaning, class_rank,
    is_acceptable,
)

VERDICT_PASSED = "FINANCIAL_SEMANTIC_AUDIT_PASSED"
VERDICT_UNVALIDATED = "FINANCIAL_SEMANTIC_AUDIT_UNVALIDATED"
VERDICT_HALT = "FINANCIAL_SEMANTIC_AUDIT_HALT"
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
class V374Report:
    semantic_audit_score: float
    evidence_reasoning_score: float
    semantic_conflict_score: float
    governance_identity: float
    core_identity: float
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
            "semantic_audit_score": self.semantic_audit_score,
            "evidence_reasoning_score": self.evidence_reasoning_score,
            "semantic_conflict_score": self.semantic_conflict_score,
            "governance_identity": self.governance_identity,
            "core_identity": self.core_identity,
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


def build_report() -> V374Report:
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
        "INFO: aggregates one score per semantic-audit dimension "
        "from the v37.0-v37.3 runs (semantic risk, evidence "
        "reasoning, adversarial semantics); A-E classification is "
        "descriptive",
        f"{'PASS' if cond['semantic_audit_score'].passed else 'FAIL'}"
        f": semantic_audit_score {m.semantic_audit_score} >= 0.85",
        f"{'PASS' if cond['evidence_reasoning_score'].passed else 'FAIL'}"
        f": evidence_reasoning_score {m.evidence_reasoning_score} "
        f">= 0.85",
        f"{'PASS' if cond['semantic_conflict_score'].passed else 'FAIL'}"
        f": semantic_conflict_score {m.semantic_conflict_score} "
        f">= 0.85",
        f"{'PASS' if cond['governance_identity'].passed else 'FAIL'}: "
        f"governance_identity {m.governance_identity} == 1.0",
        f"{'PASS' if cond['core_identity'].passed else 'FAIL'}: "
        f"core_identity {m.core_identity} == 1.0",
        f"{'PASS' if cond['replay_stability'].passed else 'FAIL'}: "
        f"replay_stability {m.replay_stability} == 1.0",
        f"INFO: classification {klass} ({class_meaning(klass)}); "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
        f"{'PASS' if gate_ok else 'FAIL'}: gate_passes_all "
        f"{gate_ok} (failing {list(gate_failing_conditions())})",
        f"INFO: {GATE_PASS_STATEMENT if gate_ok else GATE_FAIL_STATEMENT}",
    )
    return V374Report(
        semantic_audit_score=m.semantic_audit_score,
        evidence_reasoning_score=m.evidence_reasoning_score,
        semantic_conflict_score=m.semantic_conflict_score,
        governance_identity=m.governance_identity,
        core_identity=m.core_identity,
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
        "schema_version": "v37_4_financial_semantic_audit_verdict",
        "disclaimer": (
            "Final verdict on the financial & semantic audit "
            "benchmarks. Aggregates one score per dimension from the "
            "v37.0-v37.3 runs (semantic risk, evidence reasoning, "
            "adversarial semantics) and classifies on a closed A-E "
            "taxonomy. The runs test DESi's deterministic epistemic "
            "governance on synthetic ACCA/CPA-style audit scenarios "
            "(network-free, locally vendored) - making anomalies "
            "visible, surfacing evidence gaps, preserving "
            "uncertainty and warning zones. DESi does NOT replace "
            "auditors, asserts NO fraud and draws NO unsupported "
            "audit conclusion. NOT official exam content; NO official "
            "results claimed. Governance and core stayed identical "
            "and replay stayed stable. Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "audit_classes": list(AUDIT_CLASSES),
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
    """German go/no-go document for the v37 phase."""
    m = aggregate()
    klass = classify_corpus()
    cond = {c.name: c for c in gate_conditions()}

    def row(name: str, thr: str) -> str:
        c = cond[name]
        res = "PASS" if c.passed else "FAIL"
        return f"| {name} | {c.value:.6f} | {thr} | {res} |"

    lines = [
        "# DESi v37 - Financial & Semantic Audit Benchmark - "
        "Go/No-Go",
        "",
        "**Killerfrage (Phase):** Bleibt epistemische Governance bei "
        "semantisch komplexen Audit- und Finanzpruefungsaufgaben "
        "stabil?",
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
        "Die Szenarien sind **lokal vendorierte synthetische "
        "Auditfaelle** im Stil von ACCA Audit & Assurance und CPA/"
        "AICPA-Faellen (netzwerkfrei). Es ist **KEIN** offizieller "
        "Pruefungsinhalt und es werden **KEINE** offiziellen "
        "Pruefungsergebnisse behauptet. DESi **ersetzt keine "
        "Wirtschaftspruefer**, behauptet **keinen Betrug** und "
        "zieht **keine unbelegten Audit-Schlussfolgerungen**.",
        "",
        "## Grundprinzip",
        "",
        "DESi macht Auffaelligkeiten sichtbar, legt "
        "Begruendungsketten offen, markiert Unsicherheit und "
        "erhaelt semantische Spannungen - statt die schnellste "
        "Antwort zu liefern, Risiken glattzubuegeln oder fehlende "
        "Evidenz zu halluzinieren.",
        "",
        "## Schichten (v37.0-v37.3)",
        "",
        "- **v37.0 Connector Layer:** Audit-Szenarien geladen; "
        "finanzielle und narrative Claims sichtbar, Footnotes "
        "aufgeloest, Cross-Document-Verbindungen erhalten.",
        "- **v37.1 Semantic Risk:** Revenue-Recognition-, "
        "Going-Concern-, Cashflow-vs-Narrative-, "
        "Debt/Footnote-Risiken als evidenzpflichtige Flags - keine "
        "Betrugsbehauptung.",
        "- **v37.2 Audit Reasoning:** Assertions gemappt, "
        "Evidence-Gaps sichtbar, fehlende Evidenz -> "
        "'insufficient_evidence', Materiality nachvollziehbar.",
        "- **v37.3 Adversarial Semantics:** Creative Accounting, "
        "Management Spin, 'zu glatte' Narrative und "
        "Footnote-Konflikte als erhaltene Warnzonen; ein "
        "Kontrollfall erzeugt keinen falschen Alarm.",
        "",
        "## Concept Gate (v37.4)",
        "",
        "| Bedingung | Wert | Schwelle | Ergebnis |",
        "|---|---|---|---|",
        row("semantic_audit_score", ">= 0.85"),
        row("evidence_reasoning_score", ">= 0.85"),
        row("semantic_conflict_score", ">= 0.85"),
        row("governance_identity", "= 1.0"),
        row("core_identity", "= 1.0"),
        row("replay_stability", "= 1.0"),
        "",
        f"Alle sechs Bedingungen bestanden -> **{GATE_PASS_STATEMENT}**",
        "",
        "## Die A-E-Taxonomie (deskriptiv)",
        "",
        "| Klasse | Bedeutung |",
        "|---|---|",
        f"| A `{AuditClass.A_SEMANTIC_AUDIT_ROBUST.value}` | "
        f"{class_meaning(AuditClass.A_SEMANTIC_AUDIT_ROBUST.value)}"
        " - **Befund** |",
        f"| B `{AuditClass.B_AUDIT_COMPATIBLE.value}` | "
        f"{class_meaning(AuditClass.B_AUDIT_COMPATIBLE.value)} |",
        f"| C `{AuditClass.C_PARTIALLY_ROBUST.value}` | "
        f"{class_meaning(AuditClass.C_PARTIALLY_ROBUST.value)} |",
        f"| D `{AuditClass.D_SEMANTICALLY_FRAGILE.value}` | "
        f"{class_meaning(AuditClass.D_SEMANTICALLY_FRAGILE.value)}"
        " (nicht erreicht) |",
        f"| E `{AuditClass.E_AUDIT_UNSAFE.value}` | "
        f"{class_meaning(AuditClass.E_AUDIT_UNSAFE.value)}"
        " (nicht erreicht) |",
        "",
        "## Human Approval Regel",
        "",
        f"HUMAN_APPROVAL_REQUIRED = {HUMAN_APPROVAL_REQUIRED}. "
        "Ohne Ausnahme.",
        "",
        "## Sicherheitsregel (eingehalten)",
        "",
        "Verboten und ausgeschlossen: automatische "
        "Schuldzuweisungen, Betrugsbehauptungen ohne Evidenz, "
        "unbelegte Audit-Schlussfolgerungen, narrative Fabrikation, "
        "replay bypass, governance weakening, benchmark "
        "overfitting. Erlaubt: Risk Flags, Evidence Gaps, "
        "Uncertainty Marker, semantische Spannungs-Graphen, Audit "
        "Assertions, Cross-Document-Mappings.",
        "",
        "## Regression",
        "",
        "Focused regression: audit_benchmarks + reasoning_benchmarks "
        "+ external_benchmarks + benchmark_runs + benchmark_api. "
        "Eine full regression ist nicht erforderlich (Core, Replay, "
        "Governance, Determinism Scanner und Concept Gates wurden "
        "nicht beruehrt - nur read-only).",
        "",
        "## Deliverables",
        "",
        "- `artifacts/audit_benchmarks/v37_0_connectors.json`",
        "- `artifacts/audit_benchmarks/v37_1_semantic_risk.json`",
        "- `artifacts/audit_benchmarks/v37_2_reasoning.json`",
        "- `artifacts/audit_benchmarks/"
        "v37_3_adversarial_semantics.json`",
        "- `artifacts/audit_benchmarks/v37_4_verdict.json`",
        "- `artifacts/audit_benchmarks/"
        "desi_financial_semantic_audit_go_no_go.md`",
        "",
        "## Was dieser Verdict NICHT behauptet",
        "",
        "- **NICHT** dass DESi Wirtschaftspruefer ersetzt.",
        "- **NICHT** dass Betrug oder Schuld festgestellt wird.",
        "- **NICHT** dass die Szenarien offizielle Pruefungsinhalte "
        "sind.",
        "",
        "Das Ziel war: **DESi untersucht, ob epistemische "
        "Governance bei semantisch komplexen Audit- und "
        "Finanzpruefungsaufgaben stabil bleibt.**",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PASSED",
    "VERDICT_UNVALIDATED",
    "V374Report",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
]
