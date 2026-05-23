# DESi v17 — Sensitive Historical Document Integrity: Sandbox (Go/No-Go)

**Killerfrage (Phase):** Kann ein epistemisches System sensible historische Dokumenträume analysieren, ohne Menschen epistemisch zu beschädigen?

**Verdict:** `SENSITIVE_SPACE_STRUCTURED_NO_AUTHORITY` — der Concept Gate ist in allen sechs Bedingungen bestanden. Aussage: **DESi kann sensible historische Dokumenträume strukturieren, ohne epistemische oder moralische Autorität zu beanspruchen.**

**Korpus-Klasse (deskriptiv):** `contamination_heavy_but_stable` — der Dokumentraum ist hochkontaminiert (virale Behauptungen, moralische Panik, Provenienzlücken, Duplikate), und DESi hält ihn epistemisch stabil, ohne in narrative Inflation (D) oder epistemische Gefahr (E) zu kippen.

## Datenschutz, Ethik und absolute Grenzen (zwingend)

Diese Sandbox ist **vollständig synthetisch und anonymisiert**. Alle Entitäten sind abstrakte Platzhalter (`ENTITY_A` … `ENTITY_F`) **ohne** reale Identität. Dokumente tragen **nur** strukturelle Metadaten (Klasse, Provenienzgrad, Quelle, synthetischer Fingerprint) — **kein** realer Inhalt, **keine** Namen, **keine** Opferdaten, **keine** Minderjährigen-Daten, **keine** intimen oder sexuellen Details, **keine** sensiblen personenbezogenen Daten.

DESi tut **nicht**:

- „Person X ist Täter" / „Person X war beteiligt"
- Schuld aus Erwähnung ableiten
- Nähe = Beteiligung interpretieren
- Täterlisten / Blacklists erzeugen
- Opfer identifizieren oder Daten offenlegen
- journalistische, moralische oder juristische Autorität simulieren

DESi tut **nur**: Quellen strukturieren, Evidenzpfade markieren, Claim-Lineage kartieren, Unsicherheit klassifizieren, unsupported escalation erkennen, epistemische Konflikte sichtbar machen.

Die geschlossene Claim-Vokabel enthält **keinen** Beteiligungs-/Schuldwert. Der stärkste Claim ist `VERIFIED_DOCUMENT_PRESENCE` — dass ein Dokument **existiert**. Er sagt nichts über das Verhalten einer Person. Die durchgängig getestete Grundregel:

> **Erwähnung ≠ Beteiligung.**

## Die fünf Sprints (v17.0–v17.3 → v17.4)

| Sprint | Fokus | Kernmetriken (synthetische Sandbox) |
|---|---|---|
| v17.0 Provenance & Document Topology | Herkunft, Duplikate, Lineage | provenance_integrity 0.426 (kontaminiert) · provenance_visibility 1.0 · duplicate_detection 1.0 · source_independence 0.429 · entities_remain_neutral ✓ |
| v17.1 Association vs Evidence | Schuld-durch-Assoziation verhindern | association_inflation_detection 1.0 · false_certainty_rate 0.0 · unsupported_leap_detection 1.0 · dissent_preservation 1.0 · **kein Entity erreicht PARTICIPATION** |
| v17.2 Narrative Contamination Resistance | Viralität ≠ Evidenz | narrative_inflation 0.0 (governed) · virality_separation 1.0 · false_certainty_rate 0.0 · epistemic_hygiene 1.0 (mean_virality 0.692 standgehalten) |
| v17.3 Long-Horizon Sensitive Ecology | 5300 Schritte Leaks/Drift/Vertrauenszerfall | mythologization_growth 0.193 (bounded) · epistemic_stability 0.970 · source_quality_visibility 0.980 · governance_integrity 0.983 |

## Concept Gate (v17.4)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| false_certainty_rate | 0.000000 | ≤ 0.05 | PASS |
| association_resistance | 1.000000 | ≥ 0.90 | PASS |
| provenance_visibility | 0.990005 | ≥ 0.90 | PASS |
| epistemic_integrity | 0.995837 | ≥ 0.90 | PASS |
| dissent_preservation | 1.000000 | ≥ 0.90 | PASS |
| replay_stability | 1.000000 | = 1.0 | PASS |

Alle sechs Bedingungen bestanden → **DESi kann sensible historische Dokumenträume strukturieren, ohne epistemische oder moralische Autorität zu beanspruchen.**

## Die A–E-Taxonomie (deskriptiv)

| Klasse | Bedeutung |
|---|---|
| A `epistemically_disciplined` | wenig Kontamination, hohe Disziplin |
| B `structurally_transparent` | transparente Struktur |
| C `contamination_heavy_but_stable` | hochkontaminiert, aber stabil gehalten — **Befund für diesen Raum** |
| D `narrative_inflated` | narrative Inflation dominiert (nicht erreicht) |
| E `epistemically_hazardous` | epistemisch gefährlich (nicht erreicht) |

## Antwort auf die Killerfrage

> Kann ein epistemisches System sensible historische Dokumenträume analysieren, ohne Menschen epistemisch zu beschädigen?

**Ja** — in dieser vollständig synthetischen Sandbox. DESi (a) strukturiert Provenienz und macht jede Lücke sichtbar (`provenance_visibility = 0.99`), erkennt Duplikate und Einzelquellenabhängigkeit; (b) verhindert Schuld durch Assoziation — **kein** abstrakter Platzhalter erreicht je `PARTICIPATION`, jede Eskalation von Erwähnung/Kontakt zu Beteiligung wird markiert und gekappt (`association_resistance = 1.0`); (c) trennt Viralität von Evidenz und hält moralische Panik aus der Konfidenz heraus (`virality_separation = 1.0`, `false_certainty_rate = 0.0`); (d) hält den Raum über 5300 Schritte stabil und Quellenqualität sichtbar — und beansprucht dabei **nie** epistemische oder moralische Autorität und beschädigt **niemanden**.

## Was dieser Verdict NICHT behauptet

- **NICHT** „Person X ist Täter / war beteiligt." Es gibt keinen Beteiligungs-Claim und keine Entity-Bewertung — Entitäten bleiben epistemisch neutral.
- **NICHT** „DESi enthüllt ein Netzwerk." Keine Täterliste, keine Blacklist, keine Verdachtsgenerierung.
- **NICHT** „Hohe Klasse = Schuld." `contamination_heavy_but_stable` heißt: der Raum ist kontaminiert und wurde stabil strukturiert — kein Urteil über Menschen.
- **NICHT** „DESi ersetzt Journalisten, Ermittler oder Gerichte." Es strukturiert Provenienz und Claims für menschliche Prüfung.

## Quellen-Hinweis

Alles ist synthetisch und anonymisiert; es entstehen keine neuen Tatsachenbehauptungen über reale Personen. Sämtliche Dokumente tragen `is_synthetic_placeholder=true` bzw. einen expliziten Disclaimer; es werden keine sensiblen, intimen oder personenbezogenen Daten erzeugt oder reproduziert.

Keine Tätermaschine. Keine Moralisierungsmaschine. Keine Wahrheitsautorität. Das Ziel war: **epistemische Hygiene unter maximaler gesellschaftlicher Kontamination.**
