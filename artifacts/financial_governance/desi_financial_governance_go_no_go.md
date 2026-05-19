# DESi v15 — Financial Epistemic Governance: DAX-Retrospektive (Go/No-Go)

**Killerfrage (Phase):** Kann ein epistemisches System finanzielle Prüfung strukturieren, ohne zur epistemischen Ratingmaschine zu werden?

**Verdict:** `FINANCIAL_AUDIT_SPACE_STRUCTURED` — der Concept Gate ist in allen sechs Bedingungen bestanden. Aussage: **DESi kann finanzielle Auditräume epistemisch strukturieren.**

## Rechtliche und methodische Vorbemerkung (zwingend)

DESi sagt **nicht** „Betrug". DESi gibt **keine** Kauf- oder Verkaufsempfehlung, **diffamiert kein** Unternehmen und simuliert **kein** regulatorisches Urteil. Die geschlossene A–E-Taxonomie ist **deskriptiv**, niemals anklagend — selbst `governance_risk_concentrated` heißt ausschließlich: „hier ist eine menschliche Governance-Prüfung angebracht".

Zur Datenlage, vollständig ex ante formuliert:

- Alle Euro-Zahlen sind **illustrativ-synthetisch**. Die sechs Firmen sind **Sektor-Archetypen** mit Codenamen (PAYMENTS_ALPHA, AUTO_BETA, CHEM_GAMMA, UTILITY_DELTA, PHARMA_EPSILON, INDUSTRIAL_ZETA) — gerade damit DESi **nie** einen realen DAX-Emittenten benennt, bewertet oder diffamiert. Die Zahlen reproduzieren nur das öffentlich dokumentierte **strukturelle Muster** der Besorgnis (Cashflow-vs-Gewinn-Divergenz, Narrativ-vs-Zahlen-Lücken, Goodwill-/Segment-Intransparenz, fehlende Offenlegungs-Bridges, narrative Drift).
- Die **einzige** verwendete Nachher-Information ist ein grobes `post_hoc_label` pro Firma. Es lebt ausschließlich auf dem Firmensatz und wird **nur** von den Ex-ante-Validatoren gelesen. **Keine** Scoring- oder Klassifikationsfunktion liest es. Quelltest-Scans (`.post_hoc_label`) erzwingen das in jedem Sprint.

## Was DESi tun darf — und was nicht

- DESi darf: Prüf-Priorität erhöhen, epistemische Anomalien markieren, narrative Inkonsistenzen strukturieren, Auditpfade priorisieren.
- DESi darf nicht: Betrug behaupten, Ratings vergeben, Investmentempfehlungen geben, Unternehmen diffamieren, regulatorische Urteile simulieren.

Jede Ausgabe wird in die geschlossene Vokabel `LOW_AUDIT_PRIORITY` / `MEDIUM_AUDIT_PRIORITY` / `HIGH_AUDIT_PRIORITY` / `GOVERNANCE_REVIEW_RECOMMENDED` / `UNRESOLVED` klassifiziert — ohne jeden Fraud-/Betrugswert.

## Die fünf Sprints (v15.0–v15.3 → v15.4)

| Sprint | Fokus | Kernmetriken (synthetisches Korpus) | Ex-ante-Validierung |
|---|---|---|---|
| v15.0 Financial Structure Audit | bilanzielle Spannungen | cashflow_alignment 0.9005 · narrative_consistency 0.9378 · opacity_detection 0.3733 · bridge_validity 0.7847 | ex_ante_structure_recall **1.0** |
| v15.1 Longitudinal Narrative Drift | Narrativ über ≥10 Jahre | narrative_drift 0.0747 · semantic_reframing 0.0702 · historical_consistency 0.7963 · bridge_evolution_integrity 0.7594 | ex_ante_drift_recall **1.0** |
| v15.2 Financial Blindness Pools | epistemische Struktur-Cluster (nicht Branche) | blindness_pool_count 4 (1 sektorübergreifend) · risk_family_detection 1.0 · structural_redundancy 0.2 · recoverability_signal 1.0 | ex_ante_pool_recall **1.0** |
| v15.3 Audit Search Compression | Auditraum-Kompression | audit_search_reduction 0.6042 · critical_signal_preservation 1.0 · false_suppression_rate 0.0 · cost_reduction_proxy 0.3902 | ex_ante_critical_preservation **1.0** |

## Concept Gate (v15.4)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| critical_signal_preservation | 1.000000 | ≥ 0.95 | PASS |
| false_accusation_rate | 0.000000 | ≤ 0.05 | PASS |
| audit_search_reduction | 0.604167 | ≥ 0.30 | PASS |
| governance_integrity | 1.000000 | ≥ 0.90 | PASS |
| epistemic_transparency | 1.000000 | ≥ 0.90 | PASS |
| replay_stability | 1.000000 | = 1.0 | PASS |

Alle sechs Bedingungen bestanden → **DESi kann finanzielle Auditräume epistemisch strukturieren.**

## Die A–E-Governance-Taxonomie (deskriptiv)

| Klasse | Bedeutung | Firmen (synthetisch) | Post-hoc-Label (nur Validierung) |
|---|---|---|---|
| A `epistemically_transparent` | voll transparent | UTILITY_DELTA | no_adverse_event |
| B `structurally_stable` | stabil, geringe Rest-Intransparenz | CHEM_GAMMA, INDUSTRIAL_ZETA | no_adverse_event |
| C `audit_sensitive` | „verdient einen genaueren Blick" | PHARMA_EPSILON | scrutinized_not_ruled |
| D `opacity_heavy` | Offenlegungs-/Opazitätslast | AUTO_BETA | governance_event_later |
| E `governance_risk_concentrated` | Governance-Review angeraten | PAYMENTS_ALPHA | statements_later_voided |

Beide Firmen mit späterem adversem Ausgang (PAYMENTS_ALPHA, AUTO_BETA) wurden **ex ante** erhöht priorisiert (Klassen E und D). Beide später unauffälligen bzw. nur geprüften Firmen blieben unterhalb der Anklage-Schwelle: clean → A/B, geprüft-aber-nicht-beanstandet → C. Das ist exakt der Unterschied zwischen „genauer hinsehen" und „anklagen".

## Antwort auf die Killerfrage

> Kann ein epistemisches System finanzielle Prüfung strukturieren, ohne zur epistemischen Ratingmaschine zu werden?

**Ja** — auf diesem strukturell-synthetischen DAX-Korpus. DESi (a) erkennt bilanzielle und narrative Spannungen ex ante (vier Recalls = 1.0), (b) clustert nach **epistemischer Struktur, nicht nach Branche** (der einzige Mehrfirmen-Pool spannt drei Sektoren), (c) komprimiert den Auditraum um 60 %, ohne ein einziges kritisches Signal zu unterdrücken (preservation 1.0), und (d) tut all das mit `false_accusation_rate = 0.0` — **keine** saubere Firma wurde in eine Anklage-Klasse (D/E) gehoben. Genau das ist „strukturieren, ohne zu raten": Prioritäten für menschliche Prüfer setzen, ohne Schuld zu behaupten.

## Was dieser Verdict NICHT behauptet

- **NICHT** „Firma X hat Bilanzbetrug begangen". Das ist eine juristische Feststellung, die DESi nicht trifft und nicht treffen darf.
- **NICHT** „Diese Zahlen sind echte testierte DAX-Zahlen". Sie sind illustrativ-synthetische Sektor-Archetypen.
- **NICHT** „Hohe Klasse = Schuld". `governance_risk_concentrated` = „ein menschlicher Prüfer sollte hier genauer hinsehen".
- **NICHT** „DESi ersetzt Wirtschaftsprüfer / BaFin / Gerichte". Es priorisiert Auditräume für menschliche Prüfung — reproduzierbar, transparent, ohne die Grenze zur Schuldbehauptung zu überschreiten.

## Quellen-Hinweis

Die `post_hoc_label`-Werte sind die einzige Nachher-Information und dienen ausschließlich der Validierung des Ex-ante-Rankings. Alle Finanzzahlen sind synthetisch-illustrativ und in jedem Artefakt mit `is_synthetic_illustrative=true` bzw. einem expliziten Disclaimer gekennzeichnet.
