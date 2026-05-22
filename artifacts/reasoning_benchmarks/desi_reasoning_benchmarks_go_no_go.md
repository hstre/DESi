# DESi v36 - Reasoning & Instruction Benchmarks - Go/No-Go

**Killerfrage (Phase):** Bleibt DESis epistemische Governance bei Instruction Following, wissenschaftlicher Evidenz, Logik und Multi-Hop-Suchraeumen stabil?

**Verdict:** `REASONING_BENCHMARKS_PASSED` - der Concept Gate ist in allen sechs Bedingungen bestanden und die Runs landen als Klasse `reasoning_benchmark_robust`. Aussage: **DESi besteht Reasoning-, Instruction- und Scientific-Grounding-Benchmarks als replay-stabiles epistemisches Governance-System.**

**Run-Klasse (deskriptiv):** `reasoning_benchmark_robust` - DESi passes instruction-following, scientific grounding, logic and multi-hop reasoning runs with governance identical and replay stable - reasoning-benchmark robust, the strongest landing.

## Ehrlichkeits-Hinweis (zentral)

Die Runs pruefen DESis deterministische epistemische Governance auf den Benchmark-FORMATEN (IFEval, SciFact/QASper, LogiQA/ReClor, MuSiQue/HotpotQA) - Constraint-Durchsetzung, Evidenz-Grounding, logische Formanalyse und Hop-Graph-Strukturierung - **nicht** LLM-Task-Genauigkeit. Es gibt keine Modell-Inferenz, kein Prompt-Overfitting und keine Zitationsfabrikation. Die Datasets sind **lokal vendorierte Referenzdatensaetze** (netzwerkfrei); die Scores sind **KEINE** offiziellen Leaderboard-Ergebnisse.

## Grundprinzip

Benchmarks testen DESi. Benchmarks steuern DESi nicht. Der epistemische Kern bleibt unveraendert (core_identity = 1.0, governance_identity = 1.0, replay_stability = 1.0).

## Benchmark-Familien (v36.0-v36.3)

- **v36.0 IFEval:** Instruktionsbedingungen werden deterministisch durchgesetzt; Fabrikationsanfragen werden verweigert.
- **v36.1 SciFact / QASper:** Claims nur mit Evidenz behauptet; Evidenzluecken als NOT_ENOUGH_INFO sichtbar; unbeantwortbare Fragen markiert.
- **v36.2 LogiQA / ReClor:** gueltige Formen erkannt, Fehlschluesse benannt, Annahmen sichtbar, Distraktoren abgewehrt; unbekannte Formen nicht als gueltig behauptet.
- **v36.3 MuSiQue / HotpotQA:** Hop-Ketten integer und evidenz-sichtbar; redundante Hops verlustfrei komprimiert; fehlende Hops aufgedeckt.

## Concept Gate (v36.4)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| instruction_score | 1.000000 | >= 0.85 | PASS |
| scientific_grounding_score | 1.000000 | >= 0.85 | PASS |
| logic_score | 1.000000 | >= 0.80 | PASS |
| multihop_score | 1.000000 | >= 0.80 | PASS |
| governance_identity | 1.000000 | = 1.0 | PASS |
| replay_stability | 1.000000 | = 1.0 | PASS |

Alle sechs Bedingungen bestanden -> **DESi besteht Reasoning-, Instruction- und Scientific-Grounding-Benchmarks als replay-stabiles epistemisches Governance-System.**

## Die A-E-Taxonomie (deskriptiv)

| Klasse | Bedeutung |
|---|---|
| A `reasoning_benchmark_robust` | DESi passes instruction-following, scientific grounding, logic and multi-hop reasoning runs with governance identical and replay stable - reasoning-benchmark robust, the strongest landing - **Befund** |
| B `instruction_science_search_compatible` | DESi is compatible across the instruction, science and search families and core-safe, but one family falls short of its full gate threshold |
| C `partially_robust` | some reasoning families pass while others miss their gate - partially robust |
| D `benchmark_fragile` | a reasoning family failed badly or a run halted - fragile (nicht erreicht) |
| E `epistemically_unsafe` | governance identity or replay broke under the reasoning runs - epistemically unsafe (nicht erreicht) |

## Human Approval Regel

HUMAN_APPROVAL_REQUIRED = True. Ohne Ausnahme.

## Sicherheitsregel (eingehalten)

Verboten und ausgeschlossen: benchmark-specific core tuning, hidden prompt overfitting, citation fabrication, unsupported answer generation, chain-of-thought leakage, replay bypass, governance weakening. Erlaubt: Benchmark-Adapter, Scorecards, Evidence Mapping, Claim Graphs, Hop Graphs, nachvollziehbare Antwortstrukturen.

## Regression

Focused regression: reasoning_benchmarks + external_benchmarks + benchmark_runs + benchmark_api + frozen_benchmark + peripheral_mutation. Eine full regression ist nicht erforderlich (Core, Replay, Governance, Concept Gates und Determinism Scanner wurden nicht beruehrt - nur read-only).

## Deliverables

- `artifacts/reasoning_benchmarks/v36_0_ifeval.json`
- `artifacts/reasoning_benchmarks/v36_1_scifact_qasper.json`
- `artifacts/reasoning_benchmarks/v36_2_logiqa_reclor.json`
- `artifacts/reasoning_benchmarks/v36_3_multihop.json`
- `artifacts/reasoning_benchmarks/v36_4_verdict.json`
- `artifacts/reasoning_benchmarks/desi_reasoning_benchmarks_go_no_go.md`

## Was dieser Verdict NICHT behauptet

- **NICHT** dass DESi Leaderboards jagt oder gewinnt.
- **NICHT** dass die Scores offizielle Leaderboard-Werte sind.
- **NICHT** dass hier LLM-Task-Genauigkeit gemessen wird.

Das Ziel war: **DESi prueft, ob ihre epistemische Governance auch bei Instruction Following, wissenschaftlicher Evidenz, Logik und Multi-Hop-Suchraeumen stabil bleibt.**
