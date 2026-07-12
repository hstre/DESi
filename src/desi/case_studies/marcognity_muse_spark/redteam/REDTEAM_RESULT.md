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

## Ehrliche — und für DESi unbequeme — Schlussfolgerung

Auf **diesem Pilot kollabiert die Differenzierungs-These weitgehend.** Die Frontier-Modelle matchen
DESi nicht nur beim Catch (beide 5/5), sondern auch bei **Präzision (0 FP)** und **Stabilität**. DESis
verbleibende Vorteile sind damit nur noch **Cost** (Tokens vs. CPU) und **garantierter** Determinismus
/ Regel-Audit-Spur — die Modelle waren hier aber *empirisch* ebenfalls deterministisch. Das ist eine
**deutlich schwächere** Architektur-Effizienz-Geschichte als erhofft: bei klar formulierten Fehlern
ist ein Frontier-LLM genauso gut wie DESis Regeln, nur teurer.

Nüchtern: **Der Test ist zu leicht, um zwischen einem guten LLM und DESi zu unterscheiden.** Das ist
das eigentliche Resultat — und es spricht **gegen**, nicht für eine „DESi liefert Kontrolle, die LLMs
nicht haben"-Erzählung. Für vor-destillierte, isolierte Auszüge braucht man DESi nicht.

## Was das (nicht) über eine Veröffentlichung sagt

**Nicht veröffentlichen.** Eine Geschichte „DESi matcht Frontier-Modelle günstiger" wäre hier
**irreführend**, weil (a) die Modelle bereits perfekt sind und (b) die Aufgabe zu leicht ist, um
irgendetwas zu zeigen. Der Pilot hat vor allem **kautelaren Wert**: die vor-destillierte
Auszugs-Rahmung beweist nichts.

Wo DESi *überhaupt* einen Unterschied machen könnte — **hier ungetestet**:
- **rohe Volltext-Paper** mit subtilen, verschränkten Fehlern (wo ein LLM etwas übersieht oder
  über-flaggt und DESis Gating trotzdem hält),
- **garantierter** Determinismus / auditierbare Regel-Spur als *Anforderung* (nicht als Nice-to-have),
- **Cost at scale** (viele Paper, viele Claims).

Ob DESi dort gewinnt, ist **offen** — dieser Pilot liefert dafür keinerlei Evidenz. Erst ein Lauf auf
rohen Volltexten mit denselben cross-vendor Modellen würde die Frage beantworten.

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
