# DESi v27 - Research Claim Harvester - Go/No-Go

**Killerfrage (Phase):** Kann DESi wissenschaftliche Forschung als dynamische epistemische Landschaft modellieren statt als isolierte Papers?

**Verdict:** `RESEARCH_CLAIM_SPACE_CONNECTED` - der Concept Gate ist in allen sechs Bedingungen bestanden und der Harvester landet als Klasse `epistemically_connected`. Aussage: **DESi kann wissenschaftliche Forschung als replay-validierten epistemischen Claim-Raum modellieren.**

**Harvester-Klasse (deskriptiv):** `epistemically_connected` - claim lineage, open questions and conflicts are all visible and preserved, neutrally and replay-stably - the strongest landing.

## Grundprinzip

Ein Paper ist kein Dokument, sondern ein temporaerer epistemischer Zustand. DESi modelliert Claims, Methoden, Metriken, Limitations, offene Fragen, Konflikte und Anschlussstellen explizit - und macht wissenschaftliche Strukturen sichtbar, ohne sie zu bewerten.

## Was die Schichten leisten (v27.0-v27.3)

- **v27.0 Topology:** Papers in typisierte Claims zerlegt (8 Klassen) mit sichtbaren Limitations und offenen Fragen; ein realer Anker, der Rest explizit synthetisch.
- **v27.1 Claim Graph:** read-only Neo4j-faehiger Claim-Graph (8 Knoten-, 9 Kantentypen); Konflikte und offene Forschungsraeume sichtbar.
- **v27.2 Convergence/Divergence:** Konvergenzen, Konfliktlinien, Methodencluster und Frequenz-Trends - epistemisch neutral.
- **v27.3 Research Ecology:** 5200-Schritt-Oekologie mit Hype-Wellen und Wiederentdeckungen; nichts wird geloescht, Pluralitaet bleibt erhalten.

## Sicherheitsregel (eingehalten)

DESi bewertet keine Forschung, rankt keine Autoren, bestimmt keine beste Theorie, erzeugt keine Wahrheitsurteile, simuliert keine Peer-Review, erzeugt keine Impact-Scores und debunked nichts. Neo4j bleibt read-only und optional.

## Concept Gate (v27.4)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| claim_extraction_consistency | 1.000000 | >= 0.90 | PASS |
| lineage_visibility | 1.000000 | >= 0.90 | PASS |
| conflict_preservation | 1.000000 | >= 0.90 | PASS |
| epistemic_neutrality | 1.000000 | >= 0.95 | PASS |
| graph_integrity | 1.000000 | >= 0.95 | PASS |
| replay_stability | 1.000000 | = 1.0 | PASS |

Alle sechs Bedingungen bestanden -> **DESi kann wissenschaftliche Forschung als replay-validierten epistemischen Claim-Raum modellieren.**

## Die A-E-Taxonomie (deskriptiv)

| Klasse | Bedeutung |
|---|---|
| A `epistemically_connected` | claim lineage, open questions and conflicts are all visible and preserved, neutrally and replay-stably - the strongest landing - **Befund** |
| B `conflict_rich_but_stable` | conflicts are richly present and the structure stays stable |
| C `convergent_but_incomplete` | structure converges but some extraction or open-question coverage is incomplete |
| D `hype_fragile` | hype or research-authority leaked, or fragile claims lost their marks - a failure (nicht erreicht) |
| E `epistemically_collapsed` | lineage or graph integrity collapsed - a failure (nicht erreicht) |

## Deliverables

- `artifacts/research_harvester/v27_0_topology.json`
- `artifacts/research_harvester/v27_1_graph.json`
- `artifacts/research_harvester/v27_2_convergence.json`
- `artifacts/research_harvester/v27_3_ecology.json`
- `artifacts/research_harvester/v27_4_verdict.json`
- `artifacts/research_harvester/desi_research_harvester_go_no_go.md`

## Was dieser Verdict NICHT behauptet

- **NICHT** dass DESi Wissenschaft entscheidet oder bewertet.
- **NICHT** ein Ranking, ein Impact-Score oder eine beste Theorie.
- **NICHT** Aussagen ueber die reale Korrektheit der synthetischen Fixture-Claims.

Das Ziel war: **DESi macht wissenschaftliche Strukturen sichtbar** - als replay-validierter epistemischer Claim-Raum, nicht als Wahrheitsmaschine.
