"""Render the MarCognity / Muse Spark 1.1 case-study findings (with data) to PDF.

Produces an English and a German version from the committed artifacts
(summary.json, claims.jsonl, evidence.jsonl) produced by
``python -m desi.case_studies.marcognity_muse_spark`` — so both PDFs reflect
exactly the generated data:

    marcognity_muse_spark_findings_en.pdf
    marcognity_muse_spark_findings_de.pdf

Kept in ``scripts/`` (not inside the importable ``desi`` package) on purpose:
``reportlab`` is not a DESi dependency, and nothing in the package or the test
suite should import it. Run explicitly:

    python scripts/reproduce_marcognity_pdf.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CS = (Path(__file__).resolve().parents[1]
      / "src/desi/case_studies/marcognity_muse_spark")

# All human-facing prose, per language. Data tokens (verdict/type/domain names)
# stay as-is; only the labels and narrative are translated.
TR = {
    "en": {
        "title": "Epistemic Case Study — Findings, with Data",
        "subtitle": "The “epistemic validation” of a Muse Spark 1.1 text by "
                    "MarCognity-AI, analysed with DESi",
        "source": "Source: Hugging Face post <i>“Epistemic Stress Test — Muse "
                  "Spark 1.1 validated by MarCognity-AI”</i> (user elly99, 2026-07-10; "
                  "Zenodo 10.5281/zenodo.20509721) and github.com/elly99-AI/MarCognity-AI. "
                  "Regenerated offline &amp; deterministically with <font face='Courier'>"
                  "python -m desi.case_studies.marcognity_muse_spark</font>. Every number "
                  "below comes from <font face='Courier'>summary.json / claims.jsonl / "
                  "evidence.jsonl</font>.",
        "tiles": [
            "atomic claims<br/>typed &amp; anchored",
            "claims with domain-<br/>admissible evidence",
            "structural<br/>contradictions (detector)",
            "self-sealing<br/>conclusion; falsifier: no",
        ],
        "verdicts_h2": "Distribution of verdicts (23 claims)",
        "verdicts_p": "No binary VERIFIED/FAILURE stamps: heuristics, interpretations and "
                      "normative statements get their own categories; “unverifiable” "
                      "is a first-class verdict, not a fallback.",
        "evidence_h2": "Evidence strength — where concrete support is missing",
        "evidence_note": "<b>{n} of 23</b> claims have no concrete evidence passage at all "
                         "— the validator referred throughout to “the PubMed "
                         "document” with no title or locus. (Audit R4: these counts describe "
                         "the experiment's supplied evidence over 23 curated claims, not a "
                         "measured groundedness of the Muse text.)",
        "contra_h1": "The three structural conflicts",
        "contra_sub": "Found by DESi's own detector <font face='Courier'>desi.self_audit."
                      "contradictions.find_contradictions</font> as key/value "
                      "inconsistencies — not asserted by prose. Not every one is a "
                      "logical contradiction; the label names its strength.",
        "contra": [
            ("C1", "Logical contradiction: Prompt ↔ Method",
             "The Method (muse:L206): “No epistemic instructions (verification, sources, "
             "stages)”. The printed prompt demands ≥5 references with direct "
             "citations (L56–58), a citation-consistency check (L64) and six named "
             "Phases (L29–47). A genuine contradiction: both cannot be true at once. "
             "(Audit caveat R1: the prompt header muse:L12 reads 'prompt used on chatgpt "
             "(taken from marcognity)', so its provenance is slightly ambiguous; the "
             "contradiction holds on the Method's own wording.)"),
            ("C2", "Pipeline inconsistency: VERIFIED without citable evidence",
             "“VERIFIED” and “No citations found” can in principle both hold — this is "
             "not a strict logical contradiction. The real fault is an unresolved "
             "pipeline inconsistency: the Skeptical Agent asserts source support "
             "(L170–198) but names no source and no passage (only “the PubMed "
             "document”); the citation checker meanwhile finds no verifiable references "
             "(L201–202) — although the text carries eight (L154–161). Both results "
             "are merged without a consistency check (agent_metacognition L48–66)."),
            ("C3", "Unsubstantiated independence: “independent” ↔ no documented independence",
             "That the validator is technically a single <font face='Courier'>llm.invoke"
             "</font> (skeptical_agent L62) does not by itself refute independence — an "
             "external LLM call could be formally independent. The conflict is narrower: "
             "“independent external validation” (L208) is claimed with no documented "
             "independence on any axis — organizational, model-side or evidence-side. The "
             "validator receives exactly the documents that fed generation "
             "(evaluator_prompt L24–28), is non-adversarial and not reproducibly "
             "specified. Asserted, not established — a methodological misclassification."),
        ],
        "selfseal_h2": "Self-sealing &amp; falsifiability",
        "ss_rows": [
            ("Would support", "Validator flags the unverifiable → the gap is made "
             "visible; OR the validator fails → the Boundary “within the validator "
             "itself” (L237). Both outcomes confirm."),
            ("Would weaken", "A pre-registered run in which the validator, given "
             "domain-correct sources, confirms claims with quoted passages — not provided."),
            ("Would refute", "A control in which the residual failures vanish under proper "
             "source-gating (a pipeline defect, not an “intrinsic architecture”) "
             "— not provided."),
            ("Falsification condition stated?", "<b>No.</b> Since success and failure both "
             "confirm and no outcome is designated disconfirming, the hypothesis is "
             "unfalsifiable <i>as run</i>."),
        ],
        "claims_h1": "All 23 claims — the data",
        "claims_sub": "A <b>curated selection</b> (incl. previously missed claim classes), "
                      "<b>not</b> a measured complete claim coverage of the Muse text. "
                      "Line-by-line auditable in <font face='Courier'>claims.jsonl</font> / "
                      "<font face='Courier'>evidence.jsonl</font>. Column “Evidence” = "
                      "provenance kind of the source actually available.",
        "claims_head": ["ID", "Type", "Domain", "Verdict", "Evidence"],
        "prov_short": {"none": "none", "semantic_similarity_only": "semantic-only",
                       "primary": "primary", "secondary": "secondary"},
        "comp_h1": "MarCognity vs. DESi — what differs",
        "comp_sub": "Not a sales pitch: DESi does not prevent errors, it makes visible the "
                    "point at which an error, an omission or an inadmissible inference arises.",
        "comp_head": ["Dimension", "MarCognity (Skeptical Agent)", "DESi"],
        "comp": [
            ("Claim coverage", "5 general claims", "23 curated, typed claims (incl. missed classes); not measured completeness"),
            ("Source fit", "none (PubMed ↔ law)", "source_domain_gate → mismatch, not VERIFIED"),
            ("Concrete provenance", "“the PubMed document”", "exact anchor (doc:line) or none"),
            ("Contradiction detection", "misses C1, produces C2", "C1/C2/C3 via find_contradictions"),
            ("Interpretation/heuristic", "binary VERIFIED/FAILURE", "heuristic_proposal / interpretation / normative"),
            ("Uncertainty", "global prose", "per claim: verdict + uncertainty + strength"),
            ("Falsifiability", "no condition", "names support/weaken/refute + missing falsifier"),
            ("Auditability", "one concatenated text", "jsonl per line + optional hash-ledger"),
            ("Evaluator self-check", "none; failure = confirmation", "the report is itself under test (VAL-01..03)"),
        ],
        "core_h2": "Core finding",
        "core_p": "The demonstration is not that Muse Spark makes mistakes. It is: the claimed "
                  "validation <b>confirms general legal statements with unsuitable, "
                  "non-transparent sources</b> (PubMed for legal philosophy, without "
                  "title/passage), <b>overlooks a direct contradiction in the setup</b> (C1) and "
                  "then <b>reads its own failure as confirmation of the theory</b> (self-sealing, "
                  "with no falsification condition).",
        "limits_h2": "Limits of DESi (honestly)",
        "limits_p": "DESi is not infallible: the claim fixture is a curated selection (no "
                    "auto-extractor), <b>not measured complete coverage</b> of the Muse text; "
                    "the legal philosophy is <i>not</i> adjudicated on the merits here (many "
                    "claims deliberately end on “unverifiable”); source_domain_gate and "
                    "the self-sealing analysis are small, general extensions. MarCognity's own "
                    "README/Boundary document are more careful than the forum conclusion — "
                    "the over-reach is in the conclusion, not in the hedged hypothesis. "
                    "In fairness (R5), MarCognity's approach has real strengths — claim "
                    "decomposition, multi-source retrieval, an explicit skeptical pass; the "
                    "fault is in gating and provenance, not the idea.",
        "footer": "DESi case study · marcognity_muse_spark · regenerated offline "
                  "&amp; deterministically",
        "page": "Page",
        "doc_title": "DESi case study MarCognity / Muse Spark 1.1 — findings",
        "audit_h1": "Part II — Doktores audit (adversarial)",
        "audit_sub": "Four source-anchored reviewers (provenance, methodology, logic, fairness) "
                     "attacked the DESi analysis — deterministic, offline, no LLM. The result is "
                     "mixed: most findings survived, some were qualified, C2/C3 were confirmed as "
                     "NON-contradictions, and dissent is preserved.",
        "audit_disclaimer": "This attestation does NOT certify the truth of the legal statements. "
                            "It rates only the method, provenance, consistency and reach of the "
                            "DESi case study.",
        "audit_tiles_labels": ["claims reviewed", "survived (uphold / +qualification)",
                               "verdicts overturned", "findings with dissent"],
        "audit_reclass_h": "The three conflicts under adversarial review",
        "audit_reclass": [
            ("C1", "upheld — logical contradiction", "prompt ↔ method; both cannot be true "
             "(with a small prompt-provenance caveat, R1)"),
            ("C2", "reclassified → pipeline inconsistency", "VERIFIED and 'no citations' can "
             "co-occur; not a logical contradiction"),
            ("C3", "reclassified → unsubstantiated independence", "one LLM call does not refute "
             "independence; it is simply not documented on any axis"),
        ],
        "att_h": "Attestation — twelve dimensions, separately rated (no blanket seal)",
        "att_rating": {"passed": "passed", "passed_with_qualifications": "with qualifications",
                       "needs_revision": "needs revision", "failed": "failed",
                       "not_assessable": "n/a"},
        "att_labels": ["Reproducibility", "Provenance", "Claim derivation", "Claim coverage",
                       "Source fit", "Verdict logic", "Conflict classification", "Falsifiability",
                       "Fairness to MarCognity", "DESi over-reach", "Auditability",
                       "Open objections"],
        "audit_open_h": "Open questions (missing original data)",
        "audit_open": [
            "The live Hugging Face thread and full MarCognity repo were not re-fetched — only "
            "their reproduced content is anchored.",
            "The actually retrieved 'PubMed document' text is unknown; the domain mismatch stays "
            "probable, not certain.",
            "Muse Spark's version / parameters are unknown; the underlying experiment's "
            "reproducibility is not assessable.",
            "The 23 claims are not measured coverage; the true claim coverage of the Muse text is "
            "unknown.",
        ],
        "audit_note": "Overall attestation: <b>{att}</b>. Most findings survived because the "
                      "artifact was already tight; the audit's teeth are in the reclassifications "
                      "(C2/C3) and the qualifications (R1/R2/R4/R5), not in a rubber stamp.",
    },
    "de": {
        "title": "Epistemische Fallstudie — Befunde mit Daten",
        "subtitle": "Die „epistemische Validierung“ eines Muse-Spark-1.1-Textes durch "
                    "MarCognity-AI, analysiert mit DESi",
        "source": "Quelle: Hugging-Face-Beitrag <i>„Epistemic Stress Test — Muse Spark "
                  "1.1 validated by MarCognity-AI“</i> (User elly99, 2026-07-10; Zenodo "
                  "10.5281/zenodo.20509721) und github.com/elly99-AI/MarCognity-AI. Regeneriert "
                  "offline &amp; deterministisch mit <font face='Courier'>python -m "
                  "desi.case_studies.marcognity_muse_spark</font>. Jede Zahl unten stammt aus "
                  "<font face='Courier'>summary.json / claims.jsonl / evidence.jsonl</font>.",
        "tiles": [
            "atomare Claims<br/>typisiert &amp; verankert",
            "Claims mit domänen-<br/>zulässiger Evidenz",
            "strukturelle Wider-<br/>sprüche (Detektor)",
            "selbstabdichtender<br/>Schluss; Falsifier: nein",
        ],
        "verdicts_h2": "Verteilung der Urteile (23 Claims)",
        "verdicts_p": "Keine binären VERIFIED/FAILURE-Stempel: Heuristiken, Interpretationen "
                      "und normative Aussagen bekommen eigene Kategorien; „unverifiable“ "
                      "ist ein erstklassiges Urteil, keine Notlösung.",
        "evidence_h2": "Evidenzstärke — wo konkrete Belege fehlen",
        "evidence_note": "<b>{n} von 23</b> Claims haben gar keine konkrete Evidenzpassage "
                         "— der Validator nannte durchweg „das PubMed-Dokument“ "
                         "ohne Titel oder Fundstelle. (Audit R4: diese Zahlen beschreiben die "
                         "bereitgestellte Evidenz über 23 kuratierte Claims, keine gemessene "
                         "Fundierung des Muse-Textes.)",
        "contra_h1": "Drei strukturelle Konflikte",
        "contra_sub": "Gefunden von DESis eigenem Detektor <font face='Courier'>desi.self_audit."
                      "contradictions.find_contradictions</font> als Schlüssel/Wert-"
                      "Inkonsistenzen — nicht von Prosa behauptet. Nicht jeder ist ein "
                      "logischer Widerspruch; die „Art“ hält die Stärke fest.",
        "contra": [
            ("C1", "Logischer Widerspruch: Prompt ↔ Methode",
             "Die Methode (muse:L206): „No epistemic instructions (verification, sources, "
             "stages)“. Der abgedruckte Prompt verlangt ≥5 Quellen mit Direktzitaten "
             "(L56–58), eine Zitationskonsistenzprüfung (L64) und sechs benannte Phasen "
             "(L29–47). Ein echter Widerspruch: beide Aussagen können nicht zugleich "
             "wahr sein. (Audit-Vorbehalt R1: der Prompt-Titel muse:L12 nennt „prompt "
             "used on chatgpt (taken from marcognity)“ — Herkunft leicht unklar; der "
             "Widerspruch hält auf den eigenen Angaben der Methode.)"),
            ("C2", "Pipeline-Inkonsistenz: VERIFIED ohne zitierbare Evidenz",
             "„VERIFIED“ und „No citations found“ können theoretisch beide zutreffen — "
             "kein strikter logischer Widerspruch. Der eigentliche Fehler: der Skeptical "
             "Agent behauptet Quellenunterstützung (L170–198), nennt aber keine Quelle "
             "und keine Passage (nur „das PubMed-Dokument“); der Citation Checker findet "
             "zugleich keine überprüfbaren Referenzen (L201–202) — obwohl der Text acht "
             "trägt (L154–161). Beide werden ohne Konsistenzprüfung zusammengefügt "
             "(agent_metacognition L48–66)."),
            ("C3", "Unbelegte Unabhängigkeit: „independent“ ↔ keine dokumentierte Unabhängigkeit",
             "Dass der Validator technisch ein einzelnes <font face='Courier'>llm.invoke"
             "</font> ist (skeptical_agent L62), widerlegt Unabhängigkeit nicht per se — "
             "ein externer LLM-Aufruf könnte formal unabhängig sein. Der Konflikt ist "
             "enger: „independent external validation“ (L208) wird behauptet, ohne dass "
             "auf irgendeiner Achse Unabhängigkeit dokumentiert wäre — organisatorisch, "
             "modellseitig oder evidenzseitig. Der Validator erhält genau die "
             "Generierungsdokumente (evaluator_prompt L24–28), ist nicht adversarial und "
             "nicht reproduzierbar spezifiziert. Behauptet, nicht etabliert — eine "
             "methodische Fehlklassifikation."),
        ],
        "selfseal_h2": "Selbstabdichtung &amp; Falsifizierbarkeit",
        "ss_rows": [
            ("Würde stützen", "Validator markiert Unverifizierbares → Lücke "
             "sichtbar; ODER Validator scheitert → Boundary „im Validator selbst“ "
             "(L237). Beide Ausgänge bestätigen."),
            ("Würde schwächen", "Ein vorregistrierter Lauf, in dem der Validator mit "
             "domänenkorrekten Quellen Claims mit zitierten Passagen bestätigt — "
             "nicht bereitgestellt."),
            ("Würde widerlegen", "Eine Kontrolle, in der die Residualfehler unter sauberem "
             "Source-Gating verschwinden (Pipeline-Defekt statt „intrinsische "
             "Architektur“) — nicht bereitgestellt."),
            ("Falsifikationsbedingung im Versuch?", "<b>Nein.</b> Da Erfolg und Versagen beide "
             "bestätigen und kein Ausgang als widerlegend benannt ist, ist die Hypothese "
             "<i>as run</i> unfalsifizierbar."),
        ],
        "claims_h1": "Alle 23 Claims — die Daten",
        "claims_sub": "Eine <b>kuratierte Auswahl</b> (inkl. zuvor übersehener Claim-Klassen), "
                      "<b>keine</b> gemessene vollständige Claim-Abdeckung des Muse-Textes. Je "
                      "Zeile auditierbar in <font face='Courier'>claims.jsonl</font> / "
                      "<font face='Courier'>evidence.jsonl</font>. Spalte „Evidenz“ = "
                      "Provenienzart der tatsächlich verfügbaren Quelle.",
        "claims_head": ["ID", "Typ", "Domäne", "Urteil", "Evidenz"],
        "prov_short": {"none": "keine", "semantic_similarity_only": "nur semantisch",
                       "primary": "primär", "secondary": "sekundär"},
        "comp_h1": "MarCognity vs. DESi — was anders ist",
        "comp_sub": "Kein Werbetext: DESi verhindert Fehler nicht, es macht die Stelle sichtbar, "
                    "an der ein Fehler, eine Auslassung oder ein unzulässiger Schluss entsteht.",
        "comp_head": ["Dimension", "MarCognity (Skeptical Agent)", "DESi"],
        "comp": [
            ("Claim-Abdeckung", "5 allgemeine Claims", "23 kuratierte, typisierte Claims (inkl. übersehener Klassen); keine gemessene Vollständigkeit"),
            ("Quellenpassung", "keine (PubMed ↔ Recht)", "source_domain_gate → Mismatch statt VERIFIED"),
            ("Konkrete Provenienz", "„das PubMed-Dokument“", "exakter Anker (doc:Zeile) oder none"),
            ("Widerspruchserkennung", "übersieht C1, erzeugt C2", "C1/C2/C3 via find_contradictions"),
            ("Interpret./Heuristik", "binär VERIFIED/FAILURE", "heuristic_proposal / interpretation / normative"),
            ("Unsicherheit", "globaler Fließtext", "pro Claim verdict + uncertainty + strength"),
            ("Falsifizierbarkeit", "keine Bedingung", "benennt support/weaken/refute + fehlende Falsifier"),
            ("Auditierbarkeit", "konkatenierter Freitext", "jsonl je Zeile + optional Hash-Ledger"),
            ("Evaluator-Selbstprüfung", "keine; Fehler = Bestätigung", "Report ist selbst Prüfobjekt (VAL-01..03)"),
        ],
        "core_h2": "Kernbefund",
        "core_p": "Der Demonstrationsfall ist nicht, dass Muse Spark Fehler macht. Er ist: die "
                  "behauptete Validierung <b>bestätigt allgemeine juristische Aussagen mit "
                  "ungeeigneten, intransparenten Quellen</b> (PubMed für Rechtsphilosophie, "
                  "ohne Titel/Passage), <b>übersieht einen direkten Widerspruch im "
                  "Versuchsaufbau</b> (C1) und <b>deutet das eigene Versagen als Bestätigung "
                  "der Theorie</b> (Selbstabdichtung, ohne Falsifikationsbedingung).",
        "limits_h2": "Grenzen von DESi (ehrlich)",
        "limits_p": "DESi ist nicht unfehlbar: die Claim-Fixierung ist eine kuratierte Auswahl "
                    "(kein Auto-Extraktor), <b>keine gemessene vollständige Abdeckung</b> des "
                    "Muse-Textes; die Rechtsphilosophie wird hier <i>nicht</i> inhaltlich "
                    "adjudiziert (viele Claims enden bewusst auf „unverifiable“); "
                    "source_domain_gate und die Selbstabdichtungs-Analyse sind kleine, allgemeine "
                    "Erweiterungen. MarCognitys eigenes README/Boundary-Dokument sind vorsichtiger "
                    "als der Forumsschluss — die Überdehnung liegt im Schluss, nicht in "
                    "der gehedgten Hypothese. Fairnesshalber (R5): MarCognitys Ansatz hat "
                    "echte Stärken — Claim-Zerlegung, Multi-Source-Retrieval, ein expliziter "
                    "skeptischer Pass; der Fehler liegt in Gating/Provenienz, nicht in der Idee.",
        "footer": "DESi-Fallstudie · marcognity_muse_spark · regeneriert offline "
                  "&amp; deterministisch",
        "page": "Seite",
        "doc_title": "DESi-Fallstudie MarCognity / Muse Spark 1.1 — Befunde",
        "audit_h1": "Teil II — Doktores-Audit (adversarial)",
        "audit_sub": "Vier quell-verankerte Prüfer (Provenienz, Methodik, Logik, Fairness) griffen "
                     "die DESi-Analyse an — deterministisch, offline, kein LLM. Das Ergebnis ist "
                     "gemischt: die meisten Befunde hielten stand, einige wurden eingeschränkt, "
                     "C2/C3 als NICHT-Widersprüche bestätigt, Dissens bleibt erhalten.",
        "audit_disclaimer": "Dieses Attest bestätigt NICHT die Wahrheit der juristischen Aussagen. "
                            "Es bewertet nur Methode, Provenienz, Konsistenz und Reichweite der "
                            "DESi-Fallstudie.",
        "audit_tiles_labels": ["Claims geprüft", "überlebt (uphold / +Auflage)",
                               "Verdikte umgestoßen", "Befunde mit Dissens"],
        "audit_reclass_h": "Die drei Konflikte unter adversarialer Prüfung",
        "audit_reclass": [
            ("C1", "gehalten — logischer Widerspruch", "Prompt ↔ Methode; beide nicht zugleich "
             "wahr (kleiner Prompt-Provenienz-Vorbehalt, R1)"),
            ("C2", "reklassifiziert → Pipeline-Inkonsistenz", "VERIFIED und „keine Zitate“ können "
             "koexistieren; kein logischer Widerspruch"),
            ("C3", "reklassifiziert → unbelegte Unabhängigkeit", "ein LLM-Call widerlegt "
             "Unabhängigkeit nicht; sie ist nur auf keiner Achse dokumentiert"),
        ],
        "att_h": "Attest — zwölf Dimensionen, getrennt bewertet (kein Gütesiegel)",
        "att_rating": {"passed": "bestanden", "passed_with_qualifications": "mit Auflagen",
                       "needs_revision": "revidieren", "failed": "gescheitert",
                       "not_assessable": "n/a"},
        "att_labels": ["Reproduzierbarkeit", "Provenienz", "Claim-Ableitung", "Claim-Abdeckung",
                       "Quellenpassung", "Urteilslogik", "Widerspruchsklassifikation",
                       "Falsifizierbarkeit", "Fairness ggü. MarCognity", "DESi-Überdehnung",
                       "Auditierbarkeit", "Offene Einwände"],
        "audit_open_h": "Offene Fragen (fehlende Originaldaten)",
        "audit_open": [
            "Der Live-HF-Thread und der volle MarCognity-Repo-Baum wurden nicht neu abgerufen — "
            "nur ihr wiedergegebener Inhalt ist verankert.",
            "Der tatsächlich abgerufene „PubMed“-Text ist unbekannt; der Domänen-Mismatch bleibt "
            "wahrscheinlich, nicht sicher.",
            "Muse Sparks Version / Parameter sind unbekannt; die Reproduzierbarkeit des "
            "zugrunde liegenden Versuchs ist nicht bewertbar.",
            "Die 23 Claims sind keine gemessene Abdeckung; die wahre Claim-Abdeckung des "
            "Muse-Textes ist unbekannt.",
        ],
        "audit_note": "Gesamtattest: <b>{att}</b>. Die meisten Befunde hielten, weil das Artefakt "
                      "schon straff war; die Schärfe des Audits liegt in den Reklassifikationen "
                      "(C2/C3) und den Auflagen (R1/R2/R4/R5), nicht in einem Stempel.",
    },
}

# German attestation dimension keys, in the order engine.ATTESTATION emits them.
_ATT_ORDER = (
    "Reproduzierbarkeit", "Provenienz", "Claim-Ableitung", "Claim-Abdeckung", "Quellenpassung",
    "Urteilslogik", "Widerspruchsklassifikation", "Falsifizierbarkeit",
    "Fairness gegenüber MarCognity", "Überdehnung der DESi-Schlussfolgerungen", "Auditierbarkeit",
    "Offene Einwände",
)


def _build(lang, tr, data, rl):  # noqa: C901 - one linear layout routine
    (colors, mm, A4, ParagraphStyle, getSampleStyleSheet, TA_LEFT, Drawing, String,
     HorizontalBarChart, HRFlowable, KeepTogether, PageBreak, Paragraph,
     SimpleDocTemplate, Spacer, Table, TableStyle) = rl
    summary, claims, evidence, audit = data

    INK = colors.HexColor("#1a1a1a")
    MUTE = colors.HexColor("#5b6570")
    RULE = colors.HexColor("#d5dae0")
    BG_TILE = colors.HexColor("#f2f5f8")
    RED = colors.HexColor("#c0392b")
    AMBER = colors.HexColor("#d98a00")
    BLUE = colors.HexColor("#2c6fbb")
    GREEN = colors.HexColor("#2e8b57")
    SLATE = colors.HexColor("#5a6b82")
    TEAL = colors.HexColor("#1c8a8a")

    VERDICT_COLOR = {
        "contradicted": RED, "citation_mismatch": RED, "source_domain_mismatch": RED,
        "unsupported": RED, "unverifiable_from_available_evidence": AMBER,
        "interpretation": BLUE, "heuristic_proposal": SLATE, "normative_claim": SLATE,
        "partially_supported": TEAL, "supported": GREEN,
    }
    VERDICT_LABEL = {
        "contradicted": "contradicted", "citation_mismatch": "citation_mismatch",
        "source_domain_mismatch": "source_domain_mismatch", "unsupported": "unsupported",
        "unverifiable_from_available_evidence": "unverifiable",
        "interpretation": "interpretation", "heuristic_proposal": "heuristic_proposal",
        "normative_claim": "normative_claim", "supported": "supported",
    }

    styles = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=INK, fontSize=17,
                        leading=21, spaceAfter=2, spaceBefore=8)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=INK, fontSize=12.5,
                        leading=16, spaceBefore=12, spaceAfter=4)
    BODY = ParagraphStyle("Body", parent=styles["BodyText"], textColor=INK, fontSize=9.3,
                          leading=13.2, alignment=TA_LEFT, spaceAfter=4)
    SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8, leading=10.5, textColor=MUTE)
    TILE_N = ParagraphStyle("TileN", parent=BODY, fontSize=20, leading=22, textColor=INK,
                            alignment=1)
    TILE_L = ParagraphStyle("TileL", parent=BODY, fontSize=7.6, leading=9.5, textColor=MUTE,
                            alignment=1)
    CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8, leading=10)

    def bar_chart(pairs, color_fn, width=170 * mm, row_h=13):
        vals = [v for _, v in pairs]
        labels = [k for k, _ in pairs]
        n = len(pairs)
        h = row_h * n + 26
        d = Drawing(width, h)
        bc = HorizontalBarChart()
        bc.x, bc.y = 116, 8
        bc.height = row_h * n
        bc.width = width - 150
        bc.data = [vals]
        bc.strokeColor = None
        bc.bars.strokeColor = None
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = max(vals) + (1 if max(vals) < 10 else 2)
        bc.valueAxis.valueStep = max(1, (max(vals) + 1) // 5)
        bc.valueAxis.labels.fontSize = 7
        bc.valueAxis.labels.fillColor = MUTE
        bc.categoryAxis.labels.boxAnchor = "e"
        bc.categoryAxis.labels.fontSize = 7.6
        bc.categoryAxis.labels.fillColor = INK
        bc.categoryAxis.labels.dx = -3
        bc.categoryAxis.categoryNames = labels
        bc.categoryAxis.strokeColor = RULE
        bc.valueAxis.strokeColor = RULE
        bc.valueAxis.gridStrokeColor = colors.HexColor("#eef1f4")
        bc.valueAxis.visibleGrid = True
        for i in range(n):
            bc.bars[(0, i)].fillColor = color_fn(labels[i])
        bc.barLabels.fontSize = 7.5
        bc.barLabels.fillColor = INK
        bc.barLabelFormat = "%d"
        bc.barLabels.dx = 6
        d.add(bc)
        return d

    def tiles(items):
        cells = []
        for big, lab in items:
            inner = Table([[Paragraph(big, TILE_N)], [Paragraph(lab, TILE_L)]],
                          rowHeights=[24, 20])
            inner.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
            cells.append(inner)
        t = Table([cells], colWidths=[42.5 * mm] * len(items))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_TILE),
            ("BOX", (0, 0), (-1, -1), 0.5, RULE),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        return t

    def data_table(header, rows, col_widths, verdict_col=None):
        head = [Paragraph(f"<b>{hh}</b>", ParagraphStyle("th", parent=CELL, fontSize=8,
                textColor=colors.white)) for hh in header]
        body = [head] + [[Paragraph(str(c), CELL) for c in r] for r in rows]
        t = Table(body, colWidths=col_widths, repeatRows=1)
        st = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#33414f")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
        ]
        if verdict_col is not None:
            for i, r in enumerate(rows, start=1):
                v = r[verdict_col]
                key = next((k for k, lab in VERDICT_LABEL.items() if lab == v or k == v), None)
                st.append(("TEXTCOLOR", (verdict_col, i), (verdict_col, i),
                           VERDICT_COLOR.get(key, MUTE)))
                st.append(("FONTNAME", (verdict_col, i), (verdict_col, i), "Helvetica-Bold"))
        t.setStyle(TableStyle(st))
        return t

    story: list = []

    def hr():
        story.append(Spacer(1, 3))
        story.append(HRFlowable(width="100%", thickness=0.6, color=RULE))
        story.append(Spacer(1, 3))

    # Page 1
    story.append(Paragraph(tr["title"], H1))
    story.append(Paragraph(tr["subtitle"], ParagraphStyle(
        "sub", parent=BODY, fontSize=10.5, textColor=MUTE, spaceAfter=6)))
    story.append(Paragraph(tr["source"], SMALL))
    hr()
    story.append(tiles([
        (str(summary["claims_total"]), tr["tiles"][0]),
        (f"{summary['source_gate_admissible']}/{summary['source_gate_total']}", tr["tiles"][1]),
        (str(len(summary["structural_contradictions"])), tr["tiles"][2]),
        ("yes" if lang == "en" and summary["self_sealing"]["is_self_sealing"] else
         ("ja" if summary["self_sealing"]["is_self_sealing"] else "no"), tr["tiles"][3]),
    ]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(tr["verdicts_h2"], H2))
    story.append(Paragraph(tr["verdicts_p"], BODY))
    vdist = sorted(summary["verdict_distribution"].items(), key=lambda kv: (-kv[1], kv[0]))
    story.append(bar_chart(
        [(VERDICT_LABEL.get(k, k), v) for k, v in vdist],
        lambda lab: VERDICT_COLOR.get(
            next((k for k, lb in VERDICT_LABEL.items() if lb == lab), lab), MUTE)))
    story.append(Spacer(1, 6))
    story.append(Paragraph(tr["evidence_h2"], H2))
    esd = summary["evidence_strength_distribution"]
    edist = [("none", esd.get("none", 0)), ("weak", esd.get("weak", 0)),
             ("moderate", esd.get("moderate", 0)), ("strong", esd.get("strong", 0))]
    escol = {"none": RED, "weak": AMBER, "moderate": BLUE, "strong": GREEN}
    story.append(bar_chart(edist, lambda lab: escol.get(lab, MUTE)))
    story.append(Paragraph(tr["evidence_note"].format(n=esd.get("none", 0)), SMALL))
    story.append(PageBreak())

    # Page 2
    story.append(Paragraph(tr["contra_h1"], H1))
    story.append(Paragraph(tr["contra_sub"], SMALL))
    hr()
    for cid, title, txt in tr["contra"]:
        story.append(KeepTogether([
            Paragraph(f"<b>{cid} — {title}</b>", ParagraphStyle(
                "c", parent=BODY, fontSize=10, textColor=RED, spaceAfter=1)),
            Paragraph(txt, BODY), Spacer(1, 4)]))
    story.append(Paragraph(tr["selfseal_h2"], H2))
    t = Table([[Paragraph(f"<b>{a}</b>", CELL), Paragraph(b, CELL)] for a, b in tr["ss_rows"]],
              colWidths=[45 * mm, 125 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), BG_TILE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    story.append(t)
    story.append(PageBreak())

    # Page 3
    story.append(Paragraph(tr["claims_h1"], H1))
    story.append(Paragraph(tr["claims_sub"], SMALL))
    hr()
    rows = []
    for c in claims:
        ev = evidence.get(c["claim_id"], {})
        rows.append([c["claim_id"], c["claim_type"].replace("_", " "),
                     c["domain"].replace("_", " "),
                     VERDICT_LABEL.get(c["verdict"], c["verdict"]),
                     tr["prov_short"].get(ev.get("provenance_kind", ""),
                                          ev.get("provenance_kind", ""))])
    story.append(data_table(tr["claims_head"], rows,
                            [18 * mm, 34 * mm, 34 * mm, 52 * mm, 32 * mm], verdict_col=3))
    story.append(PageBreak())

    # Page 4
    story.append(Paragraph(tr["comp_h1"], H1))
    story.append(Paragraph(tr["comp_sub"], SMALL))
    hr()
    story.append(data_table(tr["comp_head"], tr["comp"], [40 * mm, 62 * mm, 68 * mm]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(tr["core_h2"], H2))
    story.append(Paragraph(tr["core_p"], BODY))
    story.append(Paragraph(tr["limits_h2"], H2))
    story.append(Paragraph(tr["limits_p"], SMALL))

    # ---- Part II: Doktores audit (only if the audit summary is available) ---- #
    if audit:
        _rating_color = {"passed": GREEN, "passed_with_qualifications": AMBER,
                         "needs_revision": RED, "failed": RED, "not_assessable": SLATE}
        cons = audit.get("consensus_distribution", {})
        survived = cons.get("uphold", 0) + cons.get("uphold_with_qualification", 0)
        story.append(PageBreak())
        story.append(Paragraph(tr["audit_h1"], H1))
        story.append(Paragraph(tr["audit_sub"], ParagraphStyle(
            "asub", parent=BODY, fontSize=9.6, textColor=MUTE, spaceAfter=5)))
        story.append(Paragraph(tr["audit_disclaimer"], SMALL))
        hr()
        story.append(tiles([
            (str(audit.get("claims_reviewed", "")), tr["audit_tiles_labels"][0]),
            (str(survived), tr["audit_tiles_labels"][1]),
            (str(audit.get("claims_overturned", "")), tr["audit_tiles_labels"][2]),
            (str(audit.get("claims_with_dissent", "")), tr["audit_tiles_labels"][3]),
        ]))
        story.append(Spacer(1, 10))

        # the three conflicts under review
        story.append(Paragraph(tr["audit_reclass_h"], H2))
        contra = audit.get("contradictions", {})
        rc_rows = []
        for cid, verdict, note in tr["audit_reclass"]:
            upheld = contra.get(cid, {}).get("upheld_as_structural", False)
            rc_rows.append([cid, verdict, note, "✓" if upheld else "→"])
        rct = data_table(["", "", "", ""], rc_rows,
                         [14 * mm, 62 * mm, 82 * mm, 12 * mm])
        # recolor: C1 green (upheld), C2/C3 amber (reclassified)
        rc_style = [("TEXTCOLOR", (1, i + 1), (1, i + 1),
                     GREEN if rc_rows[i][3] == "✓" else AMBER) for i in range(len(rc_rows))]
        rc_style += [("FONTNAME", (1, i + 1), (1, i + 1), "Helvetica-Bold")
                     for i in range(len(rc_rows))]
        rct.setStyle(TableStyle(rc_style))
        story.append(rct)
        story.append(Spacer(1, 10))

        # attestation — 12 dimensions
        story.append(Paragraph(tr["att_h"], H2))
        att = audit.get("attestation", {})
        att_rows = []
        for i, key in enumerate(_ATT_ORDER):
            rating = att.get(key, "not_assessable")
            att_rows.append([tr["att_labels"][i], tr["att_rating"].get(rating, rating)])
        att_t = data_table(["Dimension", "Rating"], att_rows, [92 * mm, 78 * mm])
        att_style = []
        for i, key in enumerate(_ATT_ORDER):
            rating = att.get(key, "not_assessable")
            att_style.append(("TEXTCOLOR", (1, i + 1), (1, i + 1),
                              _rating_color.get(rating, SLATE)))
            att_style.append(("FONTNAME", (1, i + 1), (1, i + 1), "Helvetica-Bold"))
        att_t.setStyle(TableStyle(att_style))
        story.append(att_t)
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            tr["audit_note"].format(att=audit.get("overall_attestation", "")), BODY))

        story.append(Paragraph(tr["audit_open_h"], H2))
        for q in tr["audit_open"]:
            story.append(Paragraph(f"• {q}", SMALL))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTE)
        foot = tr["footer"].replace("&amp;", "&")
        canvas.drawString(18 * mm, 10 * mm, foot)
        canvas.drawRightString(192 * mm, 10 * mm, f"{tr['page']} {doc.page}")
        canvas.restoreState()

    out = CS / f"marcognity_muse_spark_findings_{lang}.pdf"
    doc = SimpleDocTemplate(
        str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=16 * mm, title=tr["doc_title"],
        author="DESi case study")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out


def main() -> int:
    try:
        from reportlab.graphics.charts.barcharts import HorizontalBarChart
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            HRFlowable,
            KeepTogether,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        print("reportlab is required: pip install reportlab", file=sys.stderr)
        return 2

    rl = (colors, mm, A4, ParagraphStyle, getSampleStyleSheet, TA_LEFT, Drawing, String,
          HorizontalBarChart, HRFlowable, KeepTogether, PageBreak, Paragraph,
          SimpleDocTemplate, Spacer, Table, TableStyle)

    summary = json.loads((CS / "summary.json").read_text())
    claims = [json.loads(x) for x in (CS / "claims.jsonl").read_text().splitlines() if x]
    evidence = {json.loads(x)["claim_id"]: json.loads(x)
                for x in (CS / "evidence.jsonl").read_text().splitlines() if x}
    audit_path = CS / "doktores" / "audit_summary.json"
    audit = json.loads(audit_path.read_text()) if audit_path.exists() else None
    data = (summary, claims, evidence, audit)

    for lang in ("en", "de"):
        out = _build(lang, TR[lang], data, rl)
        print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
