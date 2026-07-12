# Strukturelle Konflikte — MarCognity / Muse Spark 1.1

*Auto-generiert von `python -m desi.case_studies.marcognity_muse_spark`. DESis Detektor `desi.self_audit.contradictions.find_contradictions` findet diese als Schlüssel/Wert-Inkonsistenzen — nicht von Prosa behauptet. Nicht jeder ist ein logischer Widerspruch: die Spalte „Art“ hält die unterschiedliche Stärke fest (Widerspruch / Pipeline-Inkonsistenz / unbelegte Unabhängigkeit).*

## C1 — Prompt ↔ Methode

- **Art:** Widerspruch (logisch)
- **Scope (Detektor):** `document:muse`
- **Konfligierende Werte:** 'none: no verification/sources/stages', 'required: >=5 references, direct citations, citation-check, six phases'
- **Claim-IDs (Detektor):** cl_04cc6b9fc834, cl_c859e464e204

Die Methode (muse:L206) sagt, das Modell habe keine Anweisungen zu Verifikation, Quellen oder Stufen erhalten. Der abgedruckte Prompt verlangt genau diese: ≥5 wissenschaftliche Quellen mit Direktzitaten (muse:L56-58), eine Zitationskonsistenzprüfung (muse:L64), Datenbanksuchen (muse:L24-27) und sechs benannte Phasen (muse:L29-47). Das ist ein echter logischer Widerspruch: beide Aussagen können nicht zugleich wahr sein. (Audit-Vorbehalt R1: der Abschnittstitel muse:L12 nennt den Prompt „prompt used on chatgpt (taken from marcognity)“; die Methode muse:L205-206 sagt jedoch, Muse Spark erhalte „a complex prompt“ ohne epistemische Instruktionen — der Widerspruch hält auf den eigenen Angaben des Versuchs, die Prompt-Herkunft bleibt eine kleine Restunsicherheit.)

## C2 — VERIFIED ohne zitierbare Evidenz

- **Art:** Pipeline-Inkonsistenz
- **Scope (Detektor):** `document:muse`
- **Konfligierende Werte:** "asserted: claims supported by 'the PubMed document'", 'found: no citable/verifiable reference, no named source or passage'
- **Claim-IDs (Detektor):** cl_c4823e724dea, cl_c78e74762bdd

„VERIFIED“ und „No citations found“ können theoretisch beide zugleich zutreffen — es ist kein strikter logischer Widerspruch. Der eigentliche Fehler ist eine unaufgelöste Pipeline-Inkonsistenz: der Skeptical Agent behauptet Quellenunterstützung (muse:L170-198), nennt aber keine Quelle und keine Passage (nur „das PubMed-Dokument“); der Citation Checker erkennt zugleich keine überprüfbaren Referenzen (muse:L201-202) — obwohl der Text acht Referenzen trägt (muse:L154-161). Beide Resultate werden ohne Konsistenzprüfung zusammengefügt (code:agent_metacognition L48-66).

## C3 — „Independent external validation“ ↔ keine dokumentierte Unabhängigkeit

- **Art:** Unbelegte Unabhängigkeit
- **Scope (Detektor):** `artifact:marcognity_validator`
- **Konfligierende Werte:** 'claimed: independent external validation', 'documented independence: none (evidence-side dependent on the generation documents; not adversarial; not reproducibly specified)'
- **Claim-IDs (Detektor):** cl_2a0392a586f0, cl_c773ddb31b5d

Dass der Validator technisch nur ein einzelnes llm.invoke ist (code:skeptical_agent L62), widerlegt Unabhängigkeit nicht per se — ein externer LLM-Aufruf könnte formal unabhängig sein. Der Konflikt ist enger: die Methode behauptet „independent external validation“ (muse:L208; muse:L10), ohne dass auf irgendeiner Achse Unabhängigkeit dokumentiert wäre — organisatorisch, modellseitig oder evidenzseitig. Der Validator erhält genau die Dokumente, die schon die Generierung speisten (code:evaluator_prompt L24-28), ist nicht adversarial abgesichert und nicht reproduzierbar spezifiziert; das README räumt die geteilte Verzerrung selbst ein (doc:readme L133). Die Unabhängigkeit ist behauptet, nicht etabliert — eine methodische Fehlklassifikation.

## Selbstabdichtung (Aufgabe 7)

**Self-sealing:** True — Both a working and a failing validator are interpreted as confirming the Epistemic Boundary, and no outcome is designated as disconfirming. As run, the hypothesis is self-sealing. (MarCognity's own Boundary doc is more careful — doc:epistemic_boundary L119-122 asks for controlled validation — so the self-sealing is in the forum conclusion, not necessarily the underlying construct.)

**Was würde die Hypothese stützen?**
- Validator flags unverifiable claims -> the confidence/verifiability gap is 'made visible' (the stated goal).
- Validator fails / mis-attributes sources -> read as the Boundary 'even within the validator' (muse:L237).

**Was würde sie schwächen?**
- A pre-registered outcome where the validator, given domain-correct sources, verifies claims with quoted passages — NOT provided.

**Was würde sie widerlegen?**
- A control showing the residual failures vanish under proper source-gating and provenance (i.e. the failures are a pipeline defect, not an 'intrinsic architecture' property) — NOT provided.

**Falsifikationsbedingungen im Originalversuch angegeben?** nein.
