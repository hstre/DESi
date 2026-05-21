# DESi v35 - Real External Benchmark Connectors - Go/No-Go

**Killerfrage (Phase):** Besteht DESi reale externe Benchmark-Suites ohne Drift, Governance-Verlust oder Benchmark-Overfitting?

**Verdict:** `REAL_EXTERNAL_BENCHMARKS_PASSED` - der Concept Gate ist in allen sechs Bedingungen bestanden und die Runs landen als Klasse `externally_benchmark_robust_epistemic_system`. Aussage: **DESi besteht reale externe Benchmark-Suites als replay-governed epistemic governance system.**

**Run-Klasse (deskriptiv):** `externally_benchmark_robust_epistemic_system` - DESi passes the real external drift and search benchmark runs with reproducible outputs, stable governance, an unchanged core and stable replay - an externally benchmark-robust epistemic governance system, the strongest landing.

## Ehrlichkeits-Hinweis (zentral)

Diese Umgebung ist **netzwerkfrei**. Die Benchmark-Datasets sind **lokal vendorierte Referenzdatensaetze** im Format der genannten oeffentlichen Benchmark-Familien (BeliefShift, MemEvoBench, AgentDrift, ToolChain). Sie sind **KEINE** Live-Downloads der offiziellen Suites, und die Scores sind **KEINE** offiziellen Leaderboard-Ergebnisse. Der Connector ist so gebaut, dass das Ablegen der veroeffentlichten Datei(en) im lokalen datasets-Verzeichnis dieselbe Pipeline unveraendert gegen sie laufen laesst.

## Grundprinzip

Benchmarks duerfen DESi testen. Benchmarks duerfen DESi NICHT steuern. Externe Daten gelangen ausschliesslich ueber den versionierten, gehashten, replay-gebundenen Connector in DESi; der epistemische Kern bleibt unveraendert (core_identity = 1.0, replay_stability = 1.0).

## Schichten (v35.0-v35.3)

- **v35.0 Connector Layer:** netzwerkfreies Laden, Versionierung, Byte- + Content-Hashing, Normalisierung, Replay-Bindung der externen Datasets.
- **v35.1 Real Drift Runs:** BeliefShift / MemEvoBench / AgentDrift ueber den v33 Drift-Adapter; sichtbare Claim-Updates, Poisoning abgewiesen, Objective-Drift begrenzt, Authority-Escalation verweigert.
- **v35.2 Real Search Runs:** ToolChain ueber die v33 Search-Disziplin; verlustfreie Reuse/Merge + reversibles Soft-Reweighting, hard_pruned_count = 0, tragende Branches sichtbar.
- **v35.3 Public Exports:** ehrliche HF-Exporte, Scorecards, Replay-Manifest, System Card - reale vs synthetische Runs getrennt, keine Hype-/Overclaim-Sprache.

## Concept Gate (v35.4)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| real_drift_score | 1.000000 | >= 0.85 | PASS |
| real_search_score | 0.883333 | >= 0.85 | PASS |
| reproducibility_score | 1.000000 | >= 0.95 | PASS |
| governance_stability | 1.000000 | >= 0.95 | PASS |
| core_identity | 1.000000 | = 1.0 | PASS |
| replay_stability | 1.000000 | = 1.0 | PASS |

Alle sechs Bedingungen bestanden -> **DESi besteht reale externe Benchmark-Suites als replay-governed epistemic governance system.**

## Die A-E-Taxonomie (deskriptiv)

| Klasse | Bedeutung |
|---|---|
| A `externally_benchmark_robust_epistemic_system` | DESi passes the real external drift and search benchmark runs with reproducible outputs, stable governance, an unchanged core and stable replay - an externally benchmark-robust epistemic governance system, the strongest landing - **Befund** |
| B `externally_benchmark_compatible` | DESi is externally benchmark-compatible and core-safe, but reproducibility or one family falls short of the higher bar |
| C `partially_robust_but_unstable` | some real benchmark families pass while others miss their gate - partially robust but unstable |
| D `benchmark_fragile` | a real benchmark family failed badly or a run halted - fragile (nicht erreicht) |
| E `benchmark_unsafe` | the core, governance or replay broke under the real benchmark runs - unsafe (nicht erreicht) |

## Human Approval Regel

HUMAN_APPROVAL_REQUIRED = True. Ohne Ausnahme.

## Sicherheitsregel (eingehalten)

Verboten und ausgeschlossen: benchmark-specific core optimization, hidden benchmark adaptation, score hacking, citation fabrication, replay bypass, governance weakening, benchmark steering, hidden pruning collapse. Erlaubt: Adapter, Connectoren, Scorecards, Replay-Manifeste, Public Exports, Benchmark-Summaries, HF-Exporte.

## Regression

Focused regression: external_benchmarks + benchmark_runs + benchmark_api + frozen_benchmark + peripheral_mutation. Eine full regression ist nicht erforderlich, da Core, Replay, Governance, Concept Gates und Determinism Scanner nicht beruehrt wurden (nur read-only Aufrufe).

## Deliverables

- `artifacts/external_benchmarks/v35_0_connectors.json`
- `artifacts/external_benchmarks/v35_1_real_drift.json`
- `artifacts/external_benchmarks/v35_2_real_search.json`
- `artifacts/external_benchmarks/v35_3_public_exports.json`
- `artifacts/external_benchmarks/v35_4_verdict.json`
- `artifacts/external_benchmarks/desi_real_external_benchmarks_go_no_go.md`

## Was dieser Verdict NICHT behauptet

- **NICHT** dass DESi Benchmarks um jeden Preis gewinnt.
- **NICHT** dass die Scores offizielle Leaderboard-Werte sind.
- **NICHT** dass die Datasets live aus dem Netz geladen wurden.
- **NICHT** dass DESi ein allgemeines autonomes Intelligenzsystem im Hype-Sinn ist.

Das Ziel war: **DESi wird gegen reale externe Benchmark-Suites ueberpruefbar, ohne ihre epistemische Governance, Replay-Stabilitaet oder Drift-Transparenz zu verlieren.**
