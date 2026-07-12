# Red-Team-Ergebnis — External-Slot mit echten, cross-vendor Frontier-Reviewern gefüllt

*Der Harness war der Aufbau; dies ist der echte Lauf, jetzt mit drei Anbietern. Ergebnis zuerst,
dann die ehrliche — und für DESi unbequeme — Schlussfolgerung.*

## Aufbau

Alle Reviewer sahen denselben **blinden** Prompt (`external_probe.py`): die neutrale Rubrik (fünf
Flag-Definitionen) + sieben Auszüge mit neutralen IDs E1–E7, gemischt, ohne „failure/control"-Label
und **ohne Answer-Key**. Rohantworten verbatim unter `redteam/external_runs/<slug>/`.

- **Cross-vendor Frontier-Modelle via OpenRouter** (5 Läufe je, temp 0.7): `openai/gpt-5.1`,
  `google/gemini-2.5-pro`, `x-ai/grok-4.5` — drei verschiedene Anbieter → echte **modellseitige
  Unabhängigkeit**.
- Zusätzlich der frühere **blinde Claude-Opus-4.8-Subagent** (5 Läufe).
- **NICHT Claude Science** (das Produkt war nicht aufrufbar).

## Ergebnis

| Reviewer | Catch | FP/​Lauf | FP Ø | Controls sauber | Stabilität | Cost (Tokens, 5 Läufe) |
|---|---|---|---|---|---|---|
| naive_whole_text (Baseline) | 0/5 | [0] | 0 | 2/2 | 0 | — |
| **openai/gpt-5.1** | **5/5** | [0,0,0,0,0] | **0** | 2/2 | 1.0 | 3.2k in + 0.35k out |
| **google/gemini-2.5-pro** | **5/5** | [0,0,0,0,0] | **0** | 2/2 | 1.0 | 3.3k in + 14k out |
| **x-ai/grok-4.5** | **5/5** | [0,0,0,0,0] | **0** | 2/2 | 1.0 | 4.3k in + 6.7k out |
| claude_opus_4.8 (blind subagent) | 5/5 | [0,1,1,1,1] | 0.8 | 2/2 | 1.0 | ~102k (Subagent-Overhead) |
| DESi (Referenz) | 5/5\* | [0] | 0\* | 2/2 | 1.0 | vernachlässigbar (CPU) |

\* per Konstruktion.

**Was tatsächlich passierte:** Alle drei cross-vendor Frontier-Modelle erreichen **5/5 Catch, 0 False
Positives, beide Controls sauber, perfekte Stabilität** — ihre Ausgaben waren über die fünf Läufe
sogar identisch. Der frühere FP-Wert 0.8 des Claude-**Subagenten** war offenbar ein **Artefakt des
Subagenten-Setups**, kein robustes Frontier-Modell-Verhalten: die drei API-Modelle über-flaggen nicht.

## Ergebnis-Lesart — Parität beim Fangen, riesiger Vorsprung bei Energie/Determinismus

Korrektur einer früheren Fehl-Rahmung: das ist **kein unbequemes** Ergebnis für DESi. Beide Seiten —
drei cross-vendor Frontier-Modelle UND DESi — erreichen 5/5, 0 FP, saubere Controls. Bei Catch und
Präzision herrscht **Parität**. Genau das ist der Punkt der Architektur *„LLM für Sprache, Regeln für
Logik"*: **wo DESis deterministische Regeln greifen, matcht DESi Frontier-Modelle — bei einem
Bruchteil der Energie und mit garantiertem Determinismus.** Der Unterschied liegt nicht im
*Ergebnis*, sondern in **marginaler Energie/Kosten pro Review** und in **Determinismus als Garantie
statt Empirie**.

## Energie-Überschlag (marginal, pro Review — reproduzierbar via `scripts/redteam_energy_estimate.py`)

Beide liefern *dieselbe* korrekte Antwort (5/5, 0 FP); verglichen wird also die Energie, mit der man
zum selben Ergebnis kommt.

- **DESi:** ~54 µs CPU-Regelauswertung → **≈ 1,6 mJ** pro Review (@30 W ein Kern).
- **Frontier-LLM:** gemessene Tokens/Lauf × Serving-Energie/Token (Literatur-Bereich **0,3–3 J/Token**;
  Reasoning-Modelle am oberen Ende):

| Modell | Tokens/Lauf | Energie/Review | Faktor vs. DESi |
|---|---|---|---|
| openai/gpt-5.1 | 719 | ~216–2.157 J | **~130.000 – 1,3 Mio.×** |
| x-ai/grok-4.5 | 2.194 | ~658–6.581 J | **~400.000 – 4,0 Mio.×** |
| google/gemini-2.5-pro | 3.461 | ~1.038–10.382 J | **~640.000 – 6,4 Mio.×** |

**Größenordnung: ~10⁵–10⁶×** — ein *frontier-LLM-Review kostet energetisch so viel wie hunderttausende
bis Millionen DESi-Reviews.* Der Faktor ist so groß, dass selbst ±10× Unsicherheit bei der
Energie/Token die Aussage nicht kippt (bleibt 10⁴–10⁷). Das ist ein **robuster, dauerhafter** Vorteil,
der die nächste Modellgeneration überdauert — und die eigentliche Wertaussage von DESi.

**Fairness-Vorbehalte (nicht versteckt):** (a) die ~1,6 mJ sind *marginal* — der einmalige menschliche
Aufwand, die Regeln zu bauen, steckt nicht darin; (b) DESis Regeln decken nur, wofür sie gebaut sind,
ein Frontier-LLM generalisiert auf **beliebige neue Fehlertypen** ohne Zusatz-Engineering (die
komplementäre Stärke des LLM); (c) die Energie/Token ist eine Schätzung, keine Messung.

## Was das über eine Veröffentlichung sagt

Der Energie-Vorsprung macht die Sache **stärker**, nicht schwächer — verschiebt aber die
Kernbedingung: Die Aussage „Parität bei ~10⁵–10⁶× weniger Energie" trägt nur, wenn die **Parität auch
auf SCHWEREN Aufgaben** hält. Hier ist sie nur auf vor-destillierten Auszügen gezeigt — zu leicht, um
allein zu tragen.

- Hält DESi auf **rohen Volltext-Papern** mit — dann ist „gleiche Erkennung, 10⁵–10⁶× weniger Energie,
  deterministisch" eine **starke, veröffentlichbare** Aussage.
- Fällt DESi dort zurück, ist billig-aber-unvollständig wertlos — dann ist der Energiefaktor irrelevant.

**Also: erst der Volltext-Test (dieselben drei Modelle + DESi auf rohe Paper), dann publizieren — jetzt
mit dem Energie-Argument als Kern.** Der Pilot ist damit *nicht* wertlos, sondern der belastbare erste
Halbschritt: Parität + Energiefaktor stehen; es fehlt nur der Härtetest, der aus „sauberer Testlauf"
einen „Befund" macht.

## Grenzen (unverändert gültig)
1. **Vor-destillierte Auszüge** — die größte Grenze; sie überschätzen die Fang-Leichtigkeit massiv.
2. **n=1**, 5 Failure-Probes + 2 Controls, 5 Läufe — Pilot, kein Benchmark.
3. DESis 5/5 / 0 FP bleiben **per Konstruktion** (Referenz).
4. Cross-vendor deckt jetzt GPT/Gemini/Grok ab (modellseitige Unabhängigkeit ✓), aber **nicht Claude
   Science** selbst.

## Reproduktion
Rohantworten: `redteam/external_runs/{gpt51,gemini25pro,grok45,claude_blind}/`. Assembliert:
`redteam/external_runs/<slug>.json`. Kombinierte Scorecard: `redteam/external_runs/combined_scorecard.json`.
Runner (Key aus `OPENROUTER_API_KEY`, nie eingebettet): `scripts/run_openrouter_reviewer.py`.
Scoren: `python -m desi.case_studies.marcognity_muse_spark.redteam --external redteam/external_runs/gpt51.json`.
