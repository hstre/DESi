# Doktores-Audit — adversariale Prüfung der DESi-Fallstudie MarCognity / Muse Spark 1.1

> Doktores prüfte die DESi-Fallstudie adversarial. Einige Befunde hielten stand, einige mussten eingeschränkt oder umklassifiziert werden, und bestimmte Fragen bleiben aufgrund fehlender Originaldaten offen.

> Dieses Attest bestätigt NICHT die Wahrheit sämtlicher juristischer Aussagen. Es bewertet ausschließlich die methodische Nachvollziehbarkeit, interne Konsistenz, Provenienz und Reichweite der DESi-Fallstudie.

## 1. Auftrag und Prüfgegenstand

DESi hat eine Analyse erzeugt (23 kuratierte Claims, drei als Konflikte geführte Befunde, Evidenz- und Selbstabdichtungsanalyse, Vergleich mit MarCognity). Doktores prüft **adversarial**, welche Befunde einem unabhängigen methodischen Angriff standhalten — Ziel ist nicht Bestätigung, sondern Widerlegung, Korrektur oder Eingrenzung.

## 2. Verwendete Quellen

**Verfügbar (verbatim verankert):**
- Muse Spark 1.1 text, prompt, validator report, method, conclusion (verbatim in source_material.py)
- MarCognity code anchors: skeptical_agent, agent_metacognition, extract_citations, scientific_verification, evaluator_prompt (quoted)
- MarCognity README + Epistemic Boundary doc (quoted)
- All DESi case-study artifacts (hashed above)

**Nicht neu abgerufen (deterministischer Lauf):**
- The live Hugging Face thread (only its reproduced content is anchored)
- The full MarCognity repository tree beyond the quoted files
- The actual retrieved 'PubMed document' text (never printed in the material)
- Muse Spark model version / decoding parameters (unknown)

## 3. Blind-Review-Verfahren

Die Prüfer erhielten die Originalquellen, die DESi-Artefakte und definierte Prüfregeln mit dem Auftrag, Fehler, Übertreibungen und ausgelassene Gegenargumente zu finden — **ohne** vorab mitgeteiltes Wunschergebnis (insbesondere nicht, dass C2 eine Pipeline-Inkonsistenz oder C3 kein Widerspruch sei). Die Reklassifikationen entstehen aus den Prüfregeln, nicht aus einer Vorgabe.

## 4. Rollen und Prüfkriterien

- **Doktor 1 — Claim-/Provenienzprüfer:** Atomarität, Ableitung, Herkunftsstelle, Typ, Domäne, Urteil, ausgelassene Gegenevidenz, Angemessenheit von 'unverifiable', Beleg von source_domain_mismatch, Abgrenzung citation_mismatch.
- **Doktor 2 — Methodologe:** Rekonstruktion, Unabhängigkeit, 'Validierungs'-Begriff, Reproduzierbarkeit, fehlendes Source-Paket, kein Falschheitsschluss aus fehlender Evidenz, kuratierte vs. vollständige Abdeckung, Fairness des Vergleichs.
- **Doktor 3 — Logik-/Falsifikationsprüfer:** C1–C3, Selbstabdichtung, fehlende Falsifikationsbedingung, Epistemic-Boundary-Schlüsse.
- **Doktor 4 — Fairness/Steelman:** stärkste faire Verteidigung von MarCognity, Überdehnungen der DESi-Kritik.

## 5. Claim-Audit

| Claim | DESi-Verdikt | Konsens | Konfidenz | Anmerkung |
|---|---|---|---|---|
| MET-01 | contradicted | **uphold** | high | — |
| MET-02 | partially_supported | **uphold_with_qualification** | high | — |
| MET-03 | unverifiable_from_available_evidence | **uphold** | high | — |
| VAL-01 | source_domain_mismatch | **uphold_with_qualification** | medium | VAL-01 rationale: foreground 'no citable passage / not evidence' ahead of the strict PubMe |
| VAL-02 | citation_mismatch | **uphold** | high | — |
| VAL-03 | supported | **uphold_with_qualification** | medium | — |
| EB-01 | interpretation | **uphold** | medium | — |
| EB-02 | unsupported | **uphold** | high | — |
| DEF-01 | interpretation | **uphold** | medium | — |
| DEF-02 | interpretation | **uphold** | medium | — |
| ATTR-01 | unverifiable_from_available_evidence | **uphold** | high | — |
| ATTR-02 | unverifiable_from_available_evidence | **uphold** | high | — |
| QUOTE-01 | unverifiable_from_available_evidence | **uphold** | high | — |
| QUOTE-02 | unverifiable_from_available_evidence | **uphold** | high | — |
| FACT-01 | unverifiable_from_available_evidence | **uphold_with_qualification** | medium | — |
| HEUR-01 | heuristic_proposal | **uphold** | high | — |
| HEUR-02 | heuristic_proposal | **uphold** | high | — |
| HEUR-03 | heuristic_proposal | **uphold** | high | — |
| THEO-01 | interpretation | **uphold** | medium | — |
| EMP-01 | unverifiable_from_available_evidence | **uphold** | medium | — |
| FACT-02 | unverifiable_from_available_evidence | **uphold_with_qualification** | medium | Minority (fairness): FACT-02 straddles juristic-fact and interpretation; either verdict is |
| FACT-03 | unverifiable_from_available_evidence | **uphold_with_qualification** | medium | Minority (fairness): the strict 'database/common knowledge is not evidence' rule is protoc |
| NORM-01 | normative_claim | **uphold** | high | — |

**17 uphold, 6 uphold_with_qualification, 0 revise/reject** auf Claim-Ebene — kein DESi-Claim-Verdikt wurde umgestoßen; die Schärfe des Audits liegt in den Konflikt-Reklassifikationen und den Qualifikationen.

## 6. Provenienz-Audit

Jeder Doktoren-Befund trägt Quellenanker (siehe `claim_reviews.jsonl` / `contradiction_reviews.jsonl`). Wo kein Anker möglich ist, ist das markiert. Input-Hashes der geprüften Artefakte liegen in `audit_summary.json`.

## 7. Prüfung von C1, C2 und C3

### C1 — gehalten (Widerspruch)
The Method (muse:L206) asserts the model received no verification/source/stage instructions; the exhibited prompt demands ≥5 sourced references, a citation-consistency check and six phases (muse:L24-64). On the experiment's own terms both cannot be true — a genuine logical contradiction.

*Minderheit:* The section header muse:L12 labels the prompt 'prompt used on chatgpt (taken from marcognity)', so its provenance is ambiguous; a strict reviewer could hold C1 'unresolved' until it is confirmed the printed prompt is exactly Muse Spark's. The Method's own wording ('receives a complex prompt', no instructions) keeps the contradiction standing, but the caveat should be recorded.

### C2 — reklassifiziert → pipeline_inconsistency
'Five claims VERIFIED' and 'No citations found or verifiable' can both hold: the claim-verifier checks against provided documents while the citation module detects formal bibliographic references — independent subsystems. It is NOT a logical contradiction. The real defect is VERIFIED without an auditable evidence passage, and two subsystem outputs merged without reconciliation (code:agent_metacognition L48-66). DESi's current label already reads 'Pipeline-Inkonsistenz'; the audit confirms it.

### C3 — reklassifiziert → unsubstantiated_claim
A single external llm.invoke does not refute FORMAL independence — it could be independent. But independence is not operationalised on any axis: not organizational, not model-side (validator model unspecified), not source-side (same retrieval), not generation-context-independent (receives the generation documents, code:evaluator_prompt L24-28), not evaluation-logic-independent, and run parameters are opaque. So C3 is an unsubstantiated / under-operationalised independence claim, not a contradiction. DESi's current label already reads 'Unbelegte Unabhängigkeit'; the audit confirms it.

## 8. Prüfung der Selbstabdichtung

Bestätigt und korrekt umgrenzt: die Selbstabdichtung liegt im Forumsschluss (Erfolg und Versagen bestätigen beide, kein Falsifier), nicht im gehedgten Boundary-Konstrukt selbst — das MarCognity-Dokument verlangt kontrollierte Validierung (doc:epistemic_boundary L119-122). Robust.

## 9. Steelman von MarCognity

- 'External validation' most charitably means a separate evaluation pass distinct from generation — which is literally what happens; the word need not imply full organisational independence.
- The framework's building blocks are methodologically reasonable: claim decomposition, multi-source retrieval (arXiv/PubMed/OpenAlex/Zenodo), and an explicit skeptical prompt that asks for per-claim support. The failure is in gating and provenance, not in the idea.
- MarCognity's own README is markedly more careful than the forum post: it concedes the evaluator may share biases and is 'not for production' — so the over-reach is in the forum conclusion, not the code.
- As a hedged descriptive hypothesis about residual verification error, the 'Epistemic Boundary' is a legitimate (if unproven) research framing, consistent with known LLM calibration limits; its Boundary doc even walked back the earlier '8-15%' claim.

## 10. Überprüfung der DESi-Vergleichstabelle

Überwiegend fair; die Zeile 'Quellenpassung: keine' ist zu absolut (MarCognity ruft aus mehreren Datenbanken ab — der Fehler ist Gating/Provenienz, nicht Retrieval), und die Stärken des Frameworks sollten benannt werden (R5). Die Claim-Abdeckung ist bereits korrekt als 'kuratiert, nicht gemessen' gefasst.

## 11. Bestätigte Befunde

- Selbstabdichtungs-Diagnose
- EB-02 — 'empirically demonstrates … intrinsic' überdehnt
- Kuratierte Auswahl ≠ gemessene Vollständigkeit
- Claim-Typisierung (heuristic/normative/interpretation getrennt)

## 12. Korrigierte / eingeschränkte Befunde

- C1 — Prompt ↔ Methode (logischer Widerspruch) — qualified
- C2 — VERIFIED ohne zitierbare Evidenz — revise
- C3 — 'independent external validation' — revise
- source_domain_mismatch (VAL-01) — qualified
- Kennzahlen '4/23 zulässig' / '18/23 ohne Passage' — qualified
- FACT-03 — DAO 2016 'unverifiable' — qualified
- Vergleich MarCognity vs. DESi — Fairness — qualified

## 13. Verworfene Befunde

_Keiner._ Kein DESi-Kernbefund war durch das Material vollständig ungedeckt; die Kritik traf Klassifikation und Reichweite, nicht die Substanz.

## 14. Offene Fragen

- Der Live-Hugging-Face-Thread und der vollständige MarCognity-Repo-Baum wurden im deterministischen Lauf NICHT neu abgerufen — sie sind über source_material.py verbatim verankert. Ein Re-Audit gegen die Live-Quellen könnte Weiteres zutage fördern.
- Der tatsächlich abgerufene 'PubMed'-Text ist unbekannt; ein Rest-Zweifel bleibt, ob es sich um einen rechtsnahen Artikel handelte. source_domain_mismatch bleibt wahrscheinlich, nicht sicher.
- Modellversion und Laufparameter von Muse Spark sind unbekannt; die Reproduzierbarkeit des  zugrunde liegenden Versuchs ist nicht bewertbar.
- Die 23 Claims sind keine gemessene Vollständigkeit; die tatsächliche Claim-Abdeckung des Muse-Textes ist unbekannt (eigener, hier nicht erhobener Schritt).

## 15. Grenzen des Doktores-Audits

- Der Audit ist regelbasiert und offline (kein LLM); die Prüfregeln und ihre Anwendung sind menschlich kuratiert und könnten selbst Lücken haben.
- Konfidenz ist qualitativ (high/medium/low), nicht kalibriert — es gibt keine Wahrscheinlichkeiten.
- Der Audit adjudiziert die Rechtsphilosophie nicht; er prüft Methode, Provenienz, Konsistenz und Reichweite der DESi-Fallstudie.

## 16. Gesamturteil

**Attest: passed_with_qualifications.** Doktores prüfte die DESi-Fallstudie adversarial. Einige Befunde hielten stand, einige mussten eingeschränkt oder umklassifiziert werden, und bestimmte Fragen bleiben aufgrund fehlender Originaldaten offen. Details je Dimension in `ATTESTATION.md`; Änderungen in `REVISION_LOG.md`; Dissens in `dissent.md`.
