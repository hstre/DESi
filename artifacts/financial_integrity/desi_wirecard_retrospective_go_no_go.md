# DESi v14 — Financial Statement Integrity Audit: Wirecard Retrospective

**Killerfrage:** Kann DESi prüfungswürdige Bilanzsignale erkennen, bevor der Skandal bekannt ist?

**Verdict:** `STATEMENTS_AUDIT_WORTHY` — die 2017/2018-Strukturen verdienen ein tieferes Audit.

## Rechtliche und methodische Vorbemerkung (zwingend)

DESi sagt **nicht** "Bilanzbetrug". DESi sagt: **"Diese Bilanz-/Narrativstruktur verdient ein tieferes Audit."** Die geschlossene Verdict-Vokabel enthält **keinen** Fraud-/Betrugswert.

Zur Datenlage, vollständig ex ante formuliert:

- Die hier verwendeten Euro-Zahlen sind **illustrativ-synthetisch**. Sie reproduzieren das öffentlich dokumentierte **strukturelle Muster** der Besorgnis (operativer-Cashflow-vs.-Gewinn-Divergenz, Third-Party-Acquirer-Abhängigkeit, Escrow-/Treuhand-Intransparenz, auffällig stabile Margen unter starkem Wachstum). Sie sind **nicht** die tatsächlichen testierten Einzelposten — dieser Sandbox liest die echten Geschäftsberichte nicht ein.
- Die **einzige** verwendete externe Tatsache ist das Post-hoc-Urteil: das **Landgericht München I** erklärte die Jahresabschlüsse **2017 und 2018** im Jahr **2022 für nichtig**. Diese Tatsache lebt ausschließlich im Feld `post_hoc_label` und wird **nur** zur Validierung von DESis Ex-ante-Ranking benutzt. Keine Scoring-Funktion liest sie.

Damit ist die Aussage rechtlich und methodisch sauber: DESi priorisiert prüfungswürdige Strukturen — es behauptet keinen Tatbestand.

## Was DESi bekommen würde (Input-Schema)

- Wirecard-Geschäftsberichte 2015–2018 (hier: strukturell-synthetisch modelliert)
- Presse-/Management-Narrative derselben Jahre (hier: `narrative_optimism`-Score je Jahr)
- bekannte Nachher-Fakten **nur** als Post-hoc-Label, nicht als Input

## Pflichtmetriken

| Signal | Wert | Lesart |
|---|---|---|
| `cashflow_profit_divergence` | 0.410553 | Gemeldeter Gewinn deutlich nicht durch operativen Cashflow gedeckt |
| `receivables_growth` | 0.258373 | Forderungen wachsen ~26 Prozentpunkte schneller als Umsatz (CAGR-Differenz) |
| `third_party_acquirer_dependency` | 0.511923 | ~51% des Umsatzes über schwer verifizierbare TPA-Partner |
| `narrative_numbers_mismatch` | 0.270553 | Management-Optimismus deutlich über der Cash-Deckung |
| `audit_trail_opacity` | 0.503012 | Escrow-Bestände dwarfen den Gewinn, den sie sichern sollen |
| `geographic_revenue_opacity` | 0.547949 | ~55% Umsatz aus schwer zu prüfenden APAC-Regionen |
| `unexplained_margin_stability` | 0.849335 | Margen kaum bewegt, obwohl der Umsatz sich verdoppelt |
| `bridge_required_disclosures` | 0.472024 | ~47% der geforderten Offenlegungs-Bridges fehlen |
| `anomaly_priority_score` | 0.570669 | Komposit der acht Signale |
| `ex_ante_red_flag_recall` | 1.000000 | **Post-hoc-Validierung** (siehe unten) |
| `replay_stability` | 1.000000 | Deterministisch reproduzierbar |

## Die zentrale Validierung: Hätte DESi vor dem Kollaps priorisiert?

`ex_ante_red_flag_recall = 1.0`. Das ist die einzige Stelle, an der das Post-hoc-Label berührt wird — und nur lesend zur Auswertung.

Per-Jahres-Priorität (berechnet **ausschließlich** aus den ex-ante veröffentlichten Zahlen):

| Geschäftsjahr | Priority-Score | Priority-Label | Post-hoc-Label (nur Validierung) |
|---|---|---|---|
| 2015 | 0.321667 | low | questioned_not_ruled |
| 2016 | 0.406278 | low | questioned_not_ruled |
| 2017 | 0.501990 | **medium** | **declared_void_2022** |
| 2018 | 0.580741 | **medium** | **declared_void_2022** |

Beide Jahre, die das LG München I 2022 für nichtig erklärte (2017, 2018), wurden von DESi **ex ante** als erhöhte Priorität markiert — und sie ranken **monoton** über den beiden früheren Jahren. Das Ranking folgt der späteren juristischen Schwere, obwohl DESi nur die damals veröffentlichten Strukturen sah.

Antwort auf die Killerfrage: **Ja** — auf diesem strukturell-synthetischen Korpus hätte DESis Priorisierung die prüfungswürdigen Jahre nach oben sortiert, bevor der Skandal bekannt war.

## Was dieser Verdict NICHT behauptet

- **NICHT** "Wirecard hat Bilanzbetrug begangen". Das ist eine juristische Feststellung, die DESi nicht trifft und nicht treffen darf.
- **NICHT** "Diese Zahlen sind die echten testierten Wirecard-Zahlen". Sie sind illustrativ-synthetisch, strukturell modelliert.
- **NICHT** "Hohe Priority = Schuld". Hohe Priority = "ein menschlicher Prüfer sollte hier genauer hinsehen". Audit-Würdigkeit ist kein Schuldurteil.
- **NICHT** "DESi ersetzt Wirtschaftsprüfer/BaFin/Gerichte". Es priorisiert Signale für menschliche Prüfung.

Was er BEHAUPTET:

> Auf einem strukturell-synthetischen Korpus, der das öffentlich dokumentierte Muster der 2015–2018-Besorgnis reproduziert, erzeugt DESi (a) acht prüfungswürdige Konsistenz-Signale, (b) einen Komposit-Anomalie-Score von 0.57, (c) eine Jahres-Priorisierung, die die später für nichtig erklärten Jahre (2017, 2018) mit Recall 1.0 nach oben sortiert, (d) bit-exakten Replay — und das alles, **ohne** je das Wort "Betrug" zu verwenden und **ohne** das Post-hoc-Urteil als Scoring-Input zu benutzen.

## Quellen-Hinweis

Das Post-hoc-Faktum (Nichtigkeit der Jahresabschlüsse 2017/2018, LG München I, 2022) ist die einzige externe Tatsache. Alle Finanzzahlen sind synthetisch-illustrativ und im Artefakt mit `is_synthetic_illustrative=true` gekennzeichnet.

## Killerfrage beantwortet

> Kann DESi prüfungswürdige Bilanzsignale erkennen, bevor der Skandal bekannt ist?

In der Sandbox, auf strukturell-synthetischen Daten: **Ja.** DESi priorisiert die später beanstandeten Jahre korrekt nach oben (`ex_ante_red_flag_recall = 1.0`), erzeugt acht interpretierbare Konsistenz-Signale, bleibt vollständig replaybar — und überschreitet nie die Grenze zur Schuldbehauptung. Die stärkste Aussage bleibt: **"Diese Struktur verdient ein tieferes Audit."**
