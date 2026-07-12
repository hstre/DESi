# REVISION_LOG — audit-getriebene Änderungen an der Fallstudie

*Erst nach dem Audit angewandt, nicht vorab hartcodiert. Jede Änderung mit vorheriger/neuer Formulierung, Auditbefund, betroffenen Dateien und Grund.*

## R1

- **Betroffene Dateien:** analysis.py, REPORT.md, contradiction_reviews.jsonl
- **Auditbefund:** Doktor 3 minority opinion on C1 (prompt-provenance ambiguity).
- **Grund:** C1 survives as a logical contradiction, but the audit requires the provenance caveat to be transparent about the one residual uncertainty.
- **Vorher:** C1 explanation ends: '... Ein echter Widerspruch: beide Aussagen können nicht zugleich wahr sein.'
- **Nachher:** Adds an audit caveat: the prompt section header (muse:L12) labels the prompt 'prompt used on chatgpt (taken from marcognity)', so its provenance is ambiguous; the contradiction still holds on the Method's own wording, but the caveat is recorded.

## R2

- **Betroffene Dateien:** claims.py, claims.jsonl, evidence.jsonl
- **Auditbefund:** Doktor 1 + Doktor 4: source_domain_mismatch overstates domain-certainty for an unnamed source.
- **Grund:** Foregrounds the decisive, uncontested defect; keeps the verdict but lowers the certainty of the domain claim.
- **Vorher:** VAL-01 rationale leads with 'PubMed indexes biomedical literature ... domain-mismatched source'.
- **Nachher:** VAL-01 rationale leads with the unassailable point — no named source or passage, so not evidence — and treats the domain-mismatch as the probable, secondary reason.

## R4

- **Betroffene Dateien:** REPORT.md
- **Auditbefund:** Doktor 2 + Doktor 4 over-reach flag on the headline statistics.
- **Grund:** Prevents the numbers being read as a measured coverage/groundedness property.
- **Vorher:** §4 opens: 'Von 23 Claims haben nur 4 eine domänenzulässige ... Evidenz'.
- **Nachher:** Adds a caveat that '4/23 admissible' and '18/23 no passage' describe the experiment's SUPPLIED evidence over the 23 CURATED claims — not a measured groundedness of the Muse text.

## R5

- **Betroffene Dateien:** REPORT.md, fairness_review.md
- **Auditbefund:** Doktor 4 steelman.
- **Grund:** Fairness: the case study should name what the framework gets right before what it gets wrong.
- **Vorher:** The comparison and fairness sections do not explicitly credit MarCognity's genuine design strengths.
- **Nachher:** Adds a sentence crediting MarCognity's real strengths (claim decomposition, multi-source retrieval, an explicit skeptical pass) and locating the fault in gating and provenance, not in the idea.
