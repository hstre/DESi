# Vergleich — MarCognity-Validierung vs. DESi-Analyse

*Auto-generiert. Kein Werbetext: DESi verhindert Fehler nicht, es macht die Stelle sichtbar, an der ein Fehler, eine Auslassung oder ein unzulässiger Schluss entsteht.*

| Dimension | MarCognity (Skeptical Agent) | DESi |
|---|---|---|
| **Claim-Abdeckung** | 5 sehr allgemeine Definitions-Claims geprüft; Zitate, Attributionen, Formeln, empirische & normative Aussagen ausgelassen. | 23 kuratierte, typisierte Claims (inkl. zuvor übersehener Claim-Klassen) — eine kuratierte Auswahl, KEINE gemessene Vollständigkeit des Muse-Textes. |
| **Quellenpassung (Source-Gating)** | Keine. Rechtsphilosophie gegen 'das PubMed-Dokument' geprüft (code: kein Domain-Gate). | `source_domain_gate`: biomedizinische Quelle ist für Rechtsphilosophie nicht zulässig → SOURCE_DOMAIN_MISMATCH, nicht 'VERIFIED'. |
| **Konkrete Provenienz** | 'das PubMed-Dokument' — kein Titel, keine Passage. | Jede Bewertung zeigt exakten Anker (doc:Zeile + Wortlaut); fehlt eine Passage, wird `provenance_kind=none` protokolliert, nicht kaschiert. |
| **Widerspruchserkennung** | Übersieht den Prompt/Methode-Widerspruch; produziert selbst den 'alle VERIFIED' ↔ 'keine Zitate' Widerspruch. | 3 strukturelle Widersprüche über `find_contradictions` (C1 Prompt↔Methode, C2 verifiziert↔keine Zitate, C3 'unabhängig'↔ein LLM-Call). |
| **Umgang mit Interpretationen/Heuristiken** | Binär VERIFIED/EPISTEMIC FAILURE; Formeln würden fälschlich verifizierbar/scheitern. | Eigene Verdikte `heuristic_proposal`, `interpretation`, `normative_claim`: die Formeln sind heuristische Eigenkonstruktionen, weder wahr noch falsch. |
| **Unsicherheitsdarstellung** | Autoritativer VERIFIED-Stempel; Unsicherheit nur global im Fließtext. | Pro Claim `verdict` + `uncertainty` + `evidence_strength`; `unverifiable_from_available_evidence` ist ein erstklassiges Urteil. |
| **Falsifizierbarkeit** | Keine Falsifikationsbedingung; Erfolg UND Versagen bestätigen die Theorie. | `self_sealing_analysis` benennt would_support/weaken/refute und stellt fest, dass keine Falsifikationsbedingung angegeben ist. |
| **Auditierbarkeit** | Ein konkatenierter Freitext-Report; zwei Subsysteme ohne Abgleich. | claims.jsonl + evidence.jsonl (je Zeile auditierbar) + optionaler hash-verketteter Layer-9-Ledger (`desi_router.ledger`). |
| **Evaluator-Selbstprüfung** | Der Skeptical Agent prüft den Text, aber nicht sich selbst; sein Domainfehler wird als Theoriebestätigung umgedeutet. | Der MarCognity-Report ist hier selbst Prüfobjekt (VAL-01..03); DESis eigene Grenzen werden im Report offen benannt. |
