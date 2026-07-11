# Methodologischer Review (Doktor 2)

*Prüft Versuchsaufbau und DESi-Fallstudie. Jede Zeile mit Anker.*

### Rekonstruktion des Originalversuchs
**uphold** — Purpose, prompt, generated text, validator report, method and conclusion are reconstructed faithfully and verbatim-anchored (source_material.py). — Anker: source_material.py

### Ist die MarCognity-Validierung extern/unabhängig?
**uphold_with_qualification** — 'External' yes (a separate pass, different model family); 'independent' is not operationalised (C3). DESi's partially_supported verdict is the fair reading. — Anker: muse:L208, code:evaluator_prompt L24-28

### Fairer Umgang mit dem Begriff 'Validierung'
**uphold** — DESi does not strawman 'validation'; it credits the README's own caution and targets the forum conclusion, not the framework wholesale. — Anker: doc:readme L133

### Reproduzierbarkeitsbehauptung
**uphold** — DESi's 'unverifiable' for the reproducibility claim is fair — no params are given. — Anker: muse:L10

### Schluss von fehlender Evidenz auf Falschheit?
**uphold** — Crucially NO: DESi uses 'unverifiable_from_available_evidence', never 'false', for unsourced content claims. This is the correct epistemic move. — Anker: claims.jsonl:ATTR-01, claims.jsonl:QUOTE-01

### Kuratierte Auswahl vs. suggerierte Vollständigkeit
**uphold_with_qualification** — The artifacts now state 'curated selection, not measured completeness'. Residual risk: the headline statistics ('only 4/23 admissible', '18/23 no passage') can still read as a measured property of the Muse text. A framing caveat is warranted. — Anker: REPORT.md, summary.json:source_gate_admissible

### Fairness des Vergleichs MarCognity vs. DESi
**uphold_with_qualification** — Mostly fair, but the 'Quellenpassung: keine' cell is absolute: MarCognity DOES retrieve from multiple databases — the failure is gating/provenance, not retrieval. Credit the genuine design strengths. — Anker: comparison.md

### Werden DESis eigene Grenzen dargestellt?
**uphold** — Yes — REPORT.md §8 states them explicitly (curated fixture, no adjudication, small extensions). — Anker: REPORT.md
