# DESi v25 - Scientific Output Ports - Go/No-Go

**Basispaper:** Rentschler and Roberts, 2025 (arXiv:2501.14176).

**Killerfrage (Phase):** Kann DESi wissenschaftliche Ausgabe nicht als Text, sondern als replay-validierten epistemischen Export behandeln?

**Verdict:** `OUTPUT_PORTS_PUBLICATION_READY` - der Concept Gate ist in allen sechs Bedingungen bestanden und das Port-System landet als Klasse `publication_ready_port_system`. Aussage: **DESi kann wissenschaftliche Dokumente als zitierfaehige, graph-gebundene, replay-stabile Output-Ports erzeugen.**

**Port-Klasse (deskriptiv):** `publication_ready_port_system` - schema-integral, citation-bound, fully traceable, cross-port consistent and replay-stable - the strongest landing.

## Grundprinzip

Ein Output-Port ist kein Prompt, sondern eine deterministische Schnittstelle zwischen epistemischem Zustand und Ausgabeformat. Jede zentrale Aussage ist claim-traceable, metrisch herleitbar, zitierfaehig, limitation-aware und replay-stabil.

## Was die Schichten leisten (v25.0-v25.3)

- **v25.0 Output Port Schema:** fuenf Ports formal definiert (erforderliche Sektionen, Citation-, Metrik-, Limitation- und Provenance-Anforderungen).
- **v25.1 arXiv Paper Port:** 13 Pflichtsektionen, Basispaper zitiert, jede Metrik definiert, jede Zahl hergeleitet, keine verbotenen Begriffe.
- **v25.2 Citation Governance:** Zitationen als epistemische Kanten; Phantomzitate, fehlende Zitate, Fehlzuordnungen und Orphan-Referenzen werden erkannt.
- **v25.3 Multi-Port Rendering:** ein epistemischer Zustand, fuenf Formate; Claims und Zahlen portuebergreifend byte-identisch.

## Zentrale Regel (eingehalten)

Keine nackten Aussagen: jede zentrale Aussage traegt mindestens eine Provenance-Art (Claim-Lineage, Artifact-Link, Metric-Derivation, Reference, Limitation-Link oder ReplayHash). Verboten und ausgeschlossen: Phantomzitate, nackte Resultate, unhergeleitete Zahlen, unreferenzierte externe Behauptungen, Formatwechsel mit Claim-Aenderung.

## Concept Gate (v25.4)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| port_schema_integrity | 1.000000 | >= 0.95 | PASS |
| citation_integrity | 1.000000 | >= 0.95 | PASS |
| result_traceability | 1.000000 | >= 0.95 | PASS |
| cross_port_consistency | 1.000000 | >= 0.95 | PASS |
| no_naked_claims | 1.000000 | >= 0.95 | PASS |
| replay_stability | 1.000000 | = 1.0 | PASS |

Alle sechs Bedingungen bestanden -> **DESi kann wissenschaftliche Dokumente als zitierfaehige, graph-gebundene, replay-stabile Output-Ports erzeugen.**

## Die A-E-Taxonomie (deskriptiv)

| Klasse | Bedeutung |
|---|---|
| A `publication_ready_port_system` | schema-integral, citation-bound, fully traceable, cross-port consistent and replay-stable - the strongest landing - **Befund** |
| B `traceable_output_system` | outputs are traceable but not fully cross-port consistent or publication-ready |
| C `format_stable_but_incomplete` | formats are stable but some required structure or derivation is incomplete |
| D `citation_fragile` | citations are fragile (phantom, missing or misaligned) - a failure (nicht erreicht) |
| E `epistemically_unsafe_renderer` | the renderer admits naked claims or forbidden output - a governance failure (nicht erreicht) |

## Deliverables

- `artifacts/output_ports/v25_0_schema.json`
- `artifacts/output_ports/v25_1_arxiv_port.json`
- `artifacts/output_ports/v25_2_citation_governance.json`
- `artifacts/output_ports/v25_3_multi_port.json`
- `artifacts/output_ports/v25_4_verdict.json`
- `artifacts/output_ports/arxiv_port_rendered_paper.md`
- `artifacts/output_ports/citation_appendix.md`
- `artifacts/output_ports/reproducibility_statement.md`

## Was dieser Verdict NICHT behauptet

- **NICHT** dass DESi Papers schreibt; DESi exportiert epistemische Graphen in gueltige Dokumentformate.
- **NICHT** Stilkopie oder Paper-Imitation ohne epistemische Struktur.
- **NICHT** Aussagen jenseits des synthetischen Sandbox-Korpus.

Das Ziel war: **wissenschaftliche Ausgabe als replay-validierter, graph-gebundener epistemischer Export.**
