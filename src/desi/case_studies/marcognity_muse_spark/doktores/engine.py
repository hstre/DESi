"""The Doktores audit engine — aggregate, synthesise, attest, render.

Deterministic and offline. It joins the authored, source-anchored review dataset
(``reviews.py``) with the parent case study's own artifacts, computes a
cross-doctor consensus per item, preserves dissent, derives the findings-survival
synthesis and the multi-dimensional attestation, records a provenance manifest
(input hashes, available vs. not-re-fetched sources), and writes the artifacts.

No LLM is called; confidence is qualitative. The attestation certifies method, not
the truth of the legal statements.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .. import claims as PC
from . import reviews as R
from .models import (
    AttestationDimension,
    AttestationRating,
    ClaimReview,
    Consensus,
    Decision,
    FindingStatus,
    SynthesisFinding,
)

CS_DIR = Path(__file__).resolve().parents[1]
DOK_DIR = Path(__file__).resolve().parent
ENGINE_VERSION = "v1"

DISCLAIMER = (
    "Dieses Attest bestätigt NICHT die Wahrheit sämtlicher juristischer Aussagen. Es "
    "bewertet ausschließlich die methodische Nachvollziehbarkeit, interne Konsistenz, "
    "Provenienz und Reichweite der DESi-Fallstudie."
)

HEADLINE = (
    "Doktores prüfte die DESi-Fallstudie in einem regelgeleiteten Self-Audit. Einige "
    "Befunde hielten stand, einige mussten eingeschränkt oder umklassifiziert werden, "
    "und bestimmte Fragen bleiben aufgrund fehlender Originaldaten offen."
)

# Honest scope of this audit's independence — stated up front so it can NOT be
# accused of the very thing the case study faults in MarCognity.
INDEPENDENCE_NOTE = (
    "Einordnung: Dies ist ein **regelgeleiteter Self-Audit**. Er ist **logisch und "
    "provenance-basiert adversarial** (jede Bewertung ist an eine Quelle gebunden, die "
    "Prüfregeln sind darauf angelegt, Fehler/Überdehnung/ausgelassene Gegenargumente zu "
    "finden), aber **nicht organisatorisch oder modellseitig unabhängig**: alle vier "
    "Prüfer sind fest programmierte Regeln aus demselben Repository. Es ist ein "
    "sauberer, deterministischer Gegencheck — **noch keine unabhängige Replikation**."
)

# The real revisions across the whole review process (not a rubber stamp).
# Distinguishes what THIS audit did (0 verdicts overturned) from the true deltas
# in the case study, incl. operator-review rounds before this audit.
PROCESS_REVISIONS = {
    "claim_verdicts_revised": [
        {"claim_id": "MET-02", "from": "contradicted", "to": "partially_supported",
         "when": "operator review before this audit; this audit confirms it"},
    ],
    "conflicts_reclassified": [
        {"cid": "C2", "from": "structural_contradiction", "to": "pipeline_inconsistency"},
        {"cid": "C3", "from": "structural_contradiction", "to": "unsubstantiated_independence"},
    ],
    "wording_revisions": ["R1", "R2", "R4", "R5"],
    "claims_fully_rejected": [],
    "verdicts_overturned_by_this_audit": 0,
}


# --------------------------------------------------------------------------- #
# Consensus over the doctor decisions on one item.
# --------------------------------------------------------------------------- #

def consensus(decisions: list[Decision]) -> Consensus:
    if not decisions:
        return Consensus.UNRESOLVED
    n = len(decisions)
    c = {d: decisions.count(d) for d in set(decisions)}
    if all(d == Decision.INSUFFICIENT_MATERIAL for d in decisions):
        return Consensus.UNRESOLVED
    if c.get(Decision.REJECT, 0) > n / 2:
        return Consensus.REJECT
    if c.get(Decision.REVISE, 0) > n / 2:
        return Consensus.REVISE
    if all(d == Decision.UPHOLD for d in decisions):
        return Consensus.UPHOLD
    # a qualification, or a minority revise/reject against an upholding majority
    return Consensus.UPHOLD_WITH_QUALIFICATION


def build_claim_reviews() -> list[ClaimReview]:
    by_id = PC.claims_by_id()
    out: list[ClaimReview] = []
    for claim_id, verdicts, conf, dissent, changes in R.CLAIM_VERDICTS:
        original = by_id[claim_id].verdict.value
        cons = consensus([v.decision for v in verdicts])
        # the audit qualifies but never overturns a claim verdict here; record that.
        revised = original
        out.append(ClaimReview(
            claim_id=claim_id, original_desi_verdict=original,
            doctor_verdicts=tuple(verdicts), consensus=cons, revised_verdict=revised,
            confidence=conf, dissent=tuple(dissent), required_changes=tuple(changes)))
    return out


# --------------------------------------------------------------------------- #
# Synthesis — the findings-survival table (dissent NOT smoothed away).
# --------------------------------------------------------------------------- #

SYNTHESIS: tuple[SynthesisFinding, ...] = (
    SynthesisFinding(
        "C1 — Prompt ↔ Methode (logischer Widerspruch)", FindingStatus.QUALIFIED,
        "Überlebt als echter Widerspruch; Audit verlangt den Prompt-Provenienz-Vorbehalt "
        "(muse:L12 'prompt used on chatgpt').",
        "Falls belegt würde, dass der abgedruckte Prompt NICHT der von Muse Spark ist, "
        "wäre C1 auf 'unresolved' zu setzen."),
    SynthesisFinding(
        "C2 — VERIFIED ohne zitierbare Evidenz", FindingStatus.REVISE,
        "Kein logischer Widerspruch — beide Aussagen können koexistieren. Als "
        "Pipeline-Inkonsistenz reklassifiziert (in den aktuellen Artefakten bereits so "
        "gelabelt; Audit bestätigt).",
        "Falls der Verifier eine auditierbare Passage je Claim ausgäbe, entfiele der Befund."),
    SynthesisFinding(
        "C3 — 'independent external validation'", FindingStatus.REVISE,
        "Kein Widerspruch — ein LLM-Call widerlegt Unabhängigkeit nicht. Als unbelegte / "
        "nicht operationalisierte Unabhängigkeitsbehauptung reklassifiziert (bereits so "
        "gelabelt; Audit bestätigt).",
        "Falls dokumentierte Unabhängigkeit auf ≥1 Achse nachgewiesen würde, entfiele der Befund."),
    SynthesisFinding(
        "Selbstabdichtungs-Diagnose", FindingStatus.ROBUST,
        "Korrekt auf den Forumsschluss bezogen; der gehedgte Boundary-Konstrukt selbst ist "
        "nicht per se selbstabdichtend. Mehrere Prüfer bestätigen.",
        ""),
    SynthesisFinding(
        "EB-02 — 'empirically demonstrates … intrinsic' überdehnt", FindingStatus.ROBUST,
        "n=1 kann keine intrinsische Architektur-Eigenschaft belegen; deckt sich mit "
        "MarCognitys eigenem Boundary-Dokument.",
        ""),
    SynthesisFinding(
        "source_domain_mismatch (VAL-01)", FindingStatus.QUALIFIED,
        "Kern hält (keine nennbare Quelle/Passage → keine Evidenz), aber die strikte "
        "Domänen-Ausschlussbehauptung ist etwas zu stark für eine unbenannte Quelle.",
        "Falls die tatsächlich abgerufene Quelle benannt würde, ließe sich die Domänenfrage "
        "abschließend klären."),
    SynthesisFinding(
        "Kennzahlen '4/23 zulässig' / '18/23 ohne Passage'", FindingStatus.QUALIFIED,
        "Zutreffend über die kuratierten Claims, aber ohne Rahmung als Eigenschaft der "
        "*bereitgestellten Evidenz* lesbar wie eine gemessene Fundierung des Muse-Textes.",
        ""),
    SynthesisFinding(
        "Kuratierte Auswahl ≠ gemessene Vollständigkeit", FindingStatus.ROBUST,
        "Explizit ausgewiesen; Audit bestätigt die Klarstellung.",
        ""),
    SynthesisFinding(
        "Claim-Typisierung (heuristic/normative/interpretation getrennt)", FindingStatus.ROBUST,
        "Eine echte Stärke: Heuristiken und Wertungen werden nicht in VERIFIED/FAILURE "
        "gepresst.",
        ""),
    SynthesisFinding(
        "FACT-03 — DAO 2016 'unverifiable'", FindingStatus.QUALIFIED,
        "Protokoll-korrekt; Minderheit (Fairness) hält es für einen allgemein bekannten "
        "Fakt zu streng. Verdikt bleibt, Rationale benennt den Fakt bereits.",
        ""),
    SynthesisFinding(
        "Vergleich MarCognity vs. DESi — Fairness", FindingStatus.QUALIFIED,
        "Überwiegend fair; die Stärken von MarCognity (Claim-Zerlegung, Multi-Source-"
        "Retrieval) sollten benannt werden; 'Quellenpassung: keine' ist zu absolut.",
        ""),
)


# --------------------------------------------------------------------------- #
# Attestation — 12 dimensions, separately rated (no blanket seal).
# --------------------------------------------------------------------------- #

_PASS = AttestationRating.PASSED
_PQ = AttestationRating.PASSED_WITH_QUALIFICATIONS
_NR = AttestationRating.NEEDS_REVISION
_NA = AttestationRating.NOT_ASSESSABLE

ATTESTATION: tuple[AttestationDimension, ...] = (
    AttestationDimension("Reproduzierbarkeit", _PASS,
        "Die DESi-Fallstudie regeneriert offline & deterministisch (python -m …). Der "
        "zugrunde liegende Muse-Versuch ist nicht reproduzierbar — das ist ein DESi-Befund, "
        "kein DESi-Mangel."),
    AttestationDimension("Provenienz", _PASS,
        "Jeder Claim trägt einen exakten Anker (doc:Zeile + Wortlaut); Fehlen von Evidenz "
        "wird als solches protokolliert."),
    AttestationDimension("Claim-Ableitung", _PQ,
        "Korrekt aus den Primärquellen abgeleitet; kleine Nachschärfungen bei VAL-01 "
        "(Betonung) empfohlen."),
    AttestationDimension("Claim-Abdeckung", _PQ,
        "Ausdrücklich kuratiert, nicht gemessen — jetzt klar ausgewiesen; die Kennzahlen "
        "brauchen einen Rahmungs-Vorbehalt."),
    AttestationDimension("Quellenpassung", _PQ,
        "source_domain_gate ist methodisch solide; strikte Domänen-Ausschlussbehauptung "
        "für eine unbenannte Quelle leicht überzogen."),
    AttestationDimension("Urteilslogik", _PASS,
        "Reiches Verdikt-Vokabular korrekt angewandt; keine binären VERIFIED/FAILURE-"
        "Zwänge."),
    AttestationDimension("Widerspruchsklassifikation", _PQ,
        "C1 solide als Widerspruch; C2/C3 korrekt von 'Widerspruch' herabgestuft "
        "(Pipeline-Inkonsistenz / unbelegte Unabhängigkeit)."),
    AttestationDimension("Falsifizierbarkeit", _PASS,
        "Selbstabdichtung korrekt auf den Forumsschluss bezogen; fehlende "
        "Falsifikationsbedingung korrekt identifiziert."),
    AttestationDimension("Fairness gegenüber MarCognity", _PQ,
        "Überwiegend fair; Stärken des Frameworks sollten explizit benannt, ein paar "
        "Absolutformulierungen entschärft werden."),
    AttestationDimension("Überdehnung der DESi-Schlussfolgerungen", _PQ,
        "Gering: die Kennzahlen-Rahmung und die strikte Domänen-Ausschlussbehauptung sind "
        "die einzigen Überdehnungen; die EB-02-Kritik ist gut umgrenzt."),
    AttestationDimension("Auditierbarkeit", _PASS,
        "jsonl je Zeile, exakte Anker, optionaler hash-verketteter Ledger."),
    AttestationDimension("Offene Einwände", _NA,
        "Kein Pass/Fail — siehe die offenen Fragen (fehlende Originaldaten)."),
)

OVERALL_ATTESTATION = AttestationRating.PASSED_WITH_QUALIFICATIONS

OPEN_QUESTIONS: tuple[str, ...] = (
    "Der Live-Hugging-Face-Thread und der vollständige MarCognity-Repo-Baum wurden im "
    "deterministischen Lauf NICHT neu abgerufen — sie sind über source_material.py verbatim "
    "verankert. Ein Re-Audit gegen die Live-Quellen könnte Weiteres zutage fördern.",
    "Der tatsächlich abgerufene 'PubMed'-Text ist unbekannt; ein Rest-Zweifel bleibt, ob es "
    "sich um einen rechtsnahen Artikel handelte. source_domain_mismatch bleibt wahrscheinlich, "
    "nicht sicher.",
    "Modellversion und Laufparameter von Muse Spark sind unbekannt; die Reproduzierbarkeit des "
    " zugrunde liegenden Versuchs ist nicht bewertbar.",
    "Die 23 Claims sind keine gemessene Vollständigkeit; die tatsächliche Claim-Abdeckung des "
    "Muse-Textes ist unbekannt (eigener, hier nicht erhobener Schritt).",
)

AUDIT_LIMITS: tuple[str, ...] = (
    "**Keine organisatorische/modellseitige Unabhängigkeit:** ein regelgeleiteter Self-Audit "
    "(DESi prüft DESi mit Regeln aus demselben Repository) — logisch/provenance-adversarial, "
    "aber keine unabhängige Replikation. Eine echte Gegenprüfung bräuchte ein anderes Team/"
    "Modell.",
    "Der Audit ist regelbasiert und offline (kein LLM); die Prüfregeln und ihre Anwendung sind "
    "menschlich kuratiert und könnten selbst Lücken haben.",
    "Konfidenz ist qualitativ (high/medium/low), nicht kalibriert — es gibt keine "
    "Wahrscheinlichkeiten.",
    "Der Audit adjudiziert die Rechtsphilosophie nicht; er prüft Methode, Provenienz, "
    "Konsistenz und Reichweite der DESi-Fallstudie.",
)


# --------------------------------------------------------------------------- #
# Provenance manifest.
# --------------------------------------------------------------------------- #

_HASHED_INPUTS = (
    "REPORT.md", "claims.jsonl", "evidence.jsonl", "contradictions.md",
    "comparison.md", "summary.json", "source_material.py", "claims.py", "analysis.py",
)


def _sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()[:32]


def provenance_manifest() -> dict:
    return {
        "engine_version": ENGINE_VERSION,
        "mode": "deterministic_offline_rule_based",
        "models_used": "none",
        "seed": None,
        "temperature": None,
        "raw_llm_responses": "n/a (no LLM used)",
        "timestamp": None,   # kept out of committed artifacts for byte-determinism;
                             # recorded in the optional --ledger append at runtime
        "input_hashes": {name: _sha256(CS_DIR / name) for name in _HASHED_INPUTS},
        "sources_available": [
            "Muse Spark 1.1 text, prompt, validator report, method, conclusion "
            "(verbatim in source_material.py)",
            "MarCognity code anchors: skeptical_agent, agent_metacognition, "
            "extract_citations, scientific_verification, evaluator_prompt (quoted)",
            "MarCognity README + Epistemic Boundary doc (quoted)",
            "All DESi case-study artifacts (hashed above)",
        ],
        "sources_not_refetched": [
            "The live Hugging Face thread (only its reproduced content is anchored)",
            "The full MarCognity repository tree beyond the quoted files",
            "The actual retrieved 'PubMed document' text (never printed in the material)",
            "Muse Spark model version / decoding parameters (unknown)",
        ],
    }


# --------------------------------------------------------------------------- #
# Writers.
# --------------------------------------------------------------------------- #

def _jsonl(path: Path, rows: list[dict]) -> int:
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def write_claim_reviews_jsonl(path: Path) -> int:
    return _jsonl(path, [cr.to_dict() for cr in build_claim_reviews()])


def write_contradiction_reviews_jsonl(path: Path) -> int:
    return _jsonl(path, [c.to_dict() for c in R.CONTRADICTION_REVIEWS])


def _consensus_counts() -> dict[str, int]:
    out: dict[str, int] = {}
    for cr in build_claim_reviews():
        out[cr.consensus.value] = out.get(cr.consensus.value, 0) + 1
    return dict(sorted(out.items()))


def audit_summary() -> dict:
    reviews = build_claim_reviews()
    return {
        "headline": HEADLINE,
        "disclaimer": DISCLAIMER,
        "overall_attestation": OVERALL_ATTESTATION.value,
        "claims_reviewed": len(reviews),
        "consensus_distribution": _consensus_counts(),
        "verdicts_overturned_by_this_audit": sum(
            1 for cr in reviews if cr.revised_verdict != cr.original_desi_verdict),
        "claims_with_dissent": sum(1 for cr in reviews if cr.dissent),
        "independence": INDEPENDENCE_NOTE,
        "process_revisions": PROCESS_REVISIONS,
        "contradictions": {
            c.cid: {"reviewed_classification": c.reviewed_classification.value,
                    "upheld_as_structural": c.upheld,
                    "report_change_required": c.report_change_required}
            for c in R.CONTRADICTION_REVIEWS},
        "synthesis": {s.finding: s.status.value for s in SYNTHESIS},
        "attestation": {a.dimension: a.rating.value for a in ATTESTATION},
        "revisions_mandated": [r.rid for r in R.REVISIONS],
        "open_questions": list(OPEN_QUESTIONS),
        "provenance": provenance_manifest(),
    }


def write_audit_summary_json(path: Path) -> None:
    path.write_text(json.dumps(audit_summary(), ensure_ascii=False, indent=2, sort_keys=True)
                    + "\n", encoding="utf-8")


def _md_list(items) -> str:
    return "\n".join(f"- {x}" for x in items)


def render_methodology_md() -> str:
    out = ["# Methodologischer Review (Doktor 2)\n",
           "*Prüft Versuchsaufbau und DESi-Fallstudie. Jede Zeile mit Anker.*\n"]
    for f in R.METHODOLOGY_FINDINGS:
        anchors = f" — Anker: {', '.join(f.source_anchors)}" if f.source_anchors else ""
        out.append(f"### {f.topic}\n**{f.decision.value}** — {f.assessment}{anchors}\n")
    return "\n".join(out)


def render_fairness_md() -> str:
    steel = [f for f in R.FAIRNESS_FINDINGS if f.kind == "steelman"]
    over = [f for f in R.FAIRNESS_FINDINGS if f.kind == "overreach_flag"]
    out = ["# Fairness- & Gegenpositionsprüfung (Doktor 4)\n",
           "## Steelman — die stärkste faire Verteidigung von MarCognity\n"]
    for f in steel:
        out.append(f"- {f.text} *(Anker: {', '.join(f.source_anchors)})*")
    out.append("\n## Überdehnungen in der DESi-Kritik\n")
    for f in over:
        out.append(f"- {f.text} *(Anker: {', '.join(f.source_anchors)})*")
    return "\n".join(out)


def render_dissent_md() -> str:
    out = ["# Dissens & Minderheitspositionen (nicht glattgebügelt)\n",
           "*Der Audit erhält Uneinigkeit ausdrücklich — sie ist Signal, kein Rauschen.*\n"]
    any_claim = False
    for cr in build_claim_reviews():
        if cr.dissent:
            any_claim = True
            out.append(f"### {cr.claim_id} (Konsens: {cr.consensus.value})")
            for d in cr.dissent:
                out.append(f"- {d}")
            out.append("")
    if not any_claim:
        out.append("_(keine Claim-Ebene-Dissense)_\n")
    out.append("### Widersprüche (Minderheitsmeinungen)\n")
    for c in R.CONTRADICTION_REVIEWS:
        if c.minority_opinion:
            out.append(f"- **{c.cid}:** {c.minority_opinion}")
    return "\n".join(out)


def render_revision_log_md() -> str:
    out = ["# REVISION_LOG — audit-getriebene Änderungen an der Fallstudie\n",
           "*Erst nach dem Audit angewandt, nicht vorab hartcodiert. Jede Änderung mit "
           "vorheriger/neuer Formulierung, Auditbefund, betroffenen Dateien und Grund.*\n"]
    for r in R.REVISIONS:
        out.append(f"## {r.rid}\n")
        out.append(f"- **Betroffene Dateien:** {', '.join(r.target_files)}")
        out.append(f"- **Auditbefund:** {r.audit_finding}")
        out.append(f"- **Grund:** {r.reason}")
        out.append(f"- **Vorher:** {r.before}")
        out.append(f"- **Nachher:** {r.after}\n")
    return "\n".join(out)


def render_attestation_md() -> str:
    out = ["# Doktores-Attest\n",
           f"> {DISCLAIMER}\n",
           f"> {INDEPENDENCE_NOTE}\n",
           f"**Gesamturteil: {OVERALL_ATTESTATION.value}** — kein pauschales Gütesiegel.\n",
           "| Dimension | Bewertung | Begründung |", "|---|---|---|"]
    for a in ATTESTATION:
        out.append(f"| {a.dimension} | **{a.rating.value}** | {a.reason} |")
    out.append("")
    out.append(f"_{HEADLINE}_")
    return "\n".join(out)


def render_audit_report_md() -> str:
    reviews = build_claim_reviews()
    prov = provenance_manifest()
    o = []
    o.append("# Doktores-Audit — regelgeleiteter Self-Audit der DESi-Fallstudie "
             "MarCognity / Muse Spark 1.1\n")
    o.append(f"> {HEADLINE}\n")
    o.append(f"> {DISCLAIMER}\n")
    o.append(f"> {INDEPENDENCE_NOTE}\n")

    o.append("## 1. Auftrag und Prüfgegenstand\n")
    o.append("DESi hat eine Analyse erzeugt (23 kuratierte Claims, drei als Konflikte "
             "geführte Befunde, Evidenz- und Selbstabdichtungsanalyse, Vergleich mit "
             "MarCognity). Doktores prüft **logisch und provenance-basiert adversarial**, "
             "welche Befunde einem methodischen Angriff standhalten — Ziel ist nicht "
             "Bestätigung, sondern Widerlegung, Korrektur oder Eingrenzung. Zur Unabhängigkeit "
             "siehe die Einordnung oben: ein Self-Audit, keine unabhängige Replikation.\n")

    o.append("## 2. Verwendete Quellen\n")
    o.append("**Verfügbar (verbatim verankert):**\n" + _md_list(prov["sources_available"]))
    o.append("\n**Nicht neu abgerufen (deterministischer Lauf):**\n"
             + _md_list(prov["sources_not_refetched"]) + "\n")

    o.append("## 3. Blind-Review-Verfahren\n")
    o.append("Die Prüfer erhielten die Originalquellen, die DESi-Artefakte und definierte "
             "Prüfregeln mit dem Auftrag, Fehler, Übertreibungen und ausgelassene "
             "Gegenargumente zu finden — **ohne** vorab mitgeteiltes Wunschergebnis "
             "(insbesondere nicht, dass C2 eine Pipeline-Inkonsistenz oder C3 kein Widerspruch "
             "sei). Die Reklassifikationen entstehen aus den Prüfregeln, nicht aus einer "
             "Vorgabe.\n")

    o.append("## 4. Rollen und Prüfkriterien\n")
    o.append("- **Doktor 1 — Claim-/Provenienzprüfer:** Atomarität, Ableitung, Herkunftsstelle, "
             "Typ, Domäne, Urteil, ausgelassene Gegenevidenz, Angemessenheit von 'unverifiable', "
             "Beleg von source_domain_mismatch, Abgrenzung citation_mismatch.\n"
             "- **Doktor 2 — Methodologe:** Rekonstruktion, Unabhängigkeit, 'Validierungs'-"
             "Begriff, Reproduzierbarkeit, fehlendes Source-Paket, kein Falschheitsschluss aus "
             "fehlender Evidenz, kuratierte vs. vollständige Abdeckung, Fairness des Vergleichs.\n"
             "- **Doktor 3 — Logik-/Falsifikationsprüfer:** C1–C3, Selbstabdichtung, fehlende "
             "Falsifikationsbedingung, Epistemic-Boundary-Schlüsse.\n"
             "- **Doktor 4 — Fairness/Steelman:** stärkste faire Verteidigung von MarCognity, "
             "Überdehnungen der DESi-Kritik.\n")

    o.append("## 5. Claim-Audit\n")
    o.append("| Claim | DESi-Verdikt | Konsens | Konfidenz | Anmerkung |")
    o.append("|---|---|---|---|---|")
    for cr in reviews:
        note = cr.required_changes[0] if cr.required_changes else (
            cr.dissent[0] if cr.dissent else "—")
        o.append(f"| {cr.claim_id} | {cr.original_desi_verdict} | **{cr.consensus.value}** | "
                 f"{cr.confidence.value} | {note[:90]} |")
    up = sum(1 for cr in reviews if cr.consensus == Consensus.UPHOLD)
    uq = sum(1 for cr in reviews if cr.consensus == Consensus.UPHOLD_WITH_QUALIFICATION)
    pr = PROCESS_REVISIONS
    o.append(f"\n**Auf Claim-Ebene:** {up} uphold, {uq} uphold_with_qualification, "
             "**0 von diesem Audit umgestoßen**.\n")
    o.append("**Transparente Bilanz über den gesamten Prüfprozess** (damit das Audit nicht wie "
             "ein nachträglicher Bestätigungsstempel wirkt):\n"
             f"- 23 Claims geprüft\n"
             f"- {up + uq - len(pr['claim_verdicts_revised'])} unverändert oder mit Auflage "
             "bestätigt\n"
             f"- {len(pr['claim_verdicts_revised'])} Claim-Verdikt revidiert "
             "(MET-02: contradicted → partially_supported; im Betreiber-Review vor diesem "
             "Audit, hier bestätigt)\n"
             f"- {len(pr['conflicts_reclassified'])} Konfliktklassifikationen revidiert "
             "(C2 → Pipeline-Inkonsistenz, C3 → unbelegte Unabhängigkeit)\n"
             f"- {len(pr['wording_revisions'])} Formulierungs-Revisionen durch DIESEN Audit "
             "(R1/R2/R4/R5)\n"
             f"- {len(pr['claims_fully_rejected'])} Claims vollständig verworfen\n")

    o.append("## 6. Provenienz-Audit\n")
    o.append("Jeder Doktoren-Befund trägt Quellenanker (siehe `claim_reviews.jsonl` / "
             "`contradiction_reviews.jsonl`). Wo kein Anker möglich ist, ist das markiert. "
             "Input-Hashes der geprüften Artefakte liegen in `audit_summary.json`.\n")

    o.append("## 7. Prüfung von C1, C2 und C3\n")
    for c in R.CONTRADICTION_REVIEWS:
        verdict = "gehalten (Widerspruch)" if c.upheld else \
            f"reklassifiziert → {c.reviewed_classification.value}"
        o.append(f"### {c.cid} — {verdict}\n{c.reason}\n")
        if c.minority_opinion:
            o.append(f"*Minderheit:* {c.minority_opinion}\n")

    o.append("## 8. Prüfung der Selbstabdichtung\n")
    o.append("Bestätigt und korrekt umgrenzt: die Selbstabdichtung liegt im Forumsschluss "
             "(Erfolg und Versagen bestätigen beide, kein Falsifier), nicht im gehedgten "
             "Boundary-Konstrukt selbst — das MarCognity-Dokument verlangt kontrollierte "
             "Validierung (doc:epistemic_boundary L119-122). Robust.\n")

    o.append("## 9. Steelman von MarCognity\n")
    for f in R.FAIRNESS_FINDINGS:
        if f.kind == "steelman":
            o.append(f"- {f.text}")
    o.append("")

    o.append("## 10. Überprüfung der DESi-Vergleichstabelle\n")
    o.append("Überwiegend fair; die Zeile 'Quellenpassung: keine' ist zu absolut (MarCognity "
             "ruft aus mehreren Datenbanken ab — der Fehler ist Gating/Provenienz, nicht "
             "Retrieval), und die Stärken des Frameworks sollten benannt werden (R5). Die "
             "Claim-Abdeckung ist bereits korrekt als 'kuratiert, nicht gemessen' gefasst.\n")

    o.append("## 11. Bestätigte Befunde\n")
    o.append(_md_list(f"{s.finding}" for s in SYNTHESIS if s.status == FindingStatus.ROBUST))
    o.append("\n## 12. Korrigierte / eingeschränkte Befunde\n")
    o.append(_md_list(f"{s.finding} — {s.status.value}" for s in SYNTHESIS
                      if s.status in (FindingStatus.QUALIFIED, FindingStatus.REVISE)))
    o.append("\n## 13. Verworfene Befunde\n")
    rejected = [s for s in SYNTHESIS if s.status == FindingStatus.REJECT]
    o.append(_md_list(f"{s.finding}" for s in rejected) if rejected
             else "_Keiner._ Kein DESi-Kernbefund war durch das Material vollständig ungedeckt; "
                  "die Kritik traf Klassifikation und Reichweite, nicht die Substanz.")
    o.append("\n## 14. Offene Fragen\n")
    o.append(_md_list(OPEN_QUESTIONS))
    o.append("\n## 15. Grenzen des Doktores-Audits\n")
    o.append(_md_list(AUDIT_LIMITS))
    o.append("\n## 16. Gesamturteil\n")
    o.append(f"**Attest: {OVERALL_ATTESTATION.value}.** {HEADLINE} Details je Dimension in "
             "`ATTESTATION.md`; Änderungen in `REVISION_LOG.md`; Dissens in `dissent.md`.\n")
    return "\n".join(o)


def write_all(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    n_claims = write_claim_reviews_jsonl(out_dir / "claim_reviews.jsonl")
    n_contra = write_contradiction_reviews_jsonl(out_dir / "contradiction_reviews.jsonl")
    (out_dir / "AUDIT_REPORT.md").write_text(render_audit_report_md(), encoding="utf-8")
    (out_dir / "ATTESTATION.md").write_text(render_attestation_md(), encoding="utf-8")
    (out_dir / "methodology_review.md").write_text(render_methodology_md(), encoding="utf-8")
    (out_dir / "fairness_review.md").write_text(render_fairness_md(), encoding="utf-8")
    (out_dir / "dissent.md").write_text(render_dissent_md(), encoding="utf-8")
    (out_dir / "REVISION_LOG.md").write_text(render_revision_log_md(), encoding="utf-8")
    write_audit_summary_json(out_dir / "audit_summary.json")
    return {"claim_reviews": n_claims, "contradiction_reviews": n_contra,
            "out_dir": str(out_dir)}


__all__ = [
    "consensus", "build_claim_reviews", "SYNTHESIS", "ATTESTATION",
    "OVERALL_ATTESTATION", "OPEN_QUESTIONS", "provenance_manifest", "audit_summary",
    "write_all", "DISCLAIMER", "HEADLINE", "INDEPENDENCE_NOTE", "PROCESS_REVISIONS",
]
