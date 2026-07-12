# HARD2 — der wirklich harte Benchmark bricht die Sättigung

*Der erste harte Satz sättigte ab ~12B (viele bei F1 1.0). HARD2 fügt drei Fehlertypen hinzu, die
*rigoros klingen* und die selbst starke Modelle übersehen — **causal_overreach** (Korrelation→Kausal),
**significance_not_importance** (p-Wert ≠ Effektgröße), **base_rate_neglect** — mit engen Near-Miss-Paaren
und expertenklingenden Clean-Controls. 8 Flags, 18 Items, blind, 5 Läufe. Multi-Label-F1.*

## Ergebnis — 14 Modelle (F1-sortiert)

| Modell | F1 (±σ) | P | R | $/M-Token |
|---|---|---|---|---|
| openai/gpt-5.1 | **0.927 ±0.03** | 0.948 | 0.909 | 10,00 |
| **google/gemma-4-31b-it** | 0.909 ±0.00 | 0.909 | 0.909 | **0,16** |
| poolside/laguna-m.1 | 0.905 ±0.03 | 0.944 | 0.873 | 0,40 |
| google/gemini-2.5-pro | 0.901 ±0.02 | 0.894 | 0.909 | 10,00 |
| x-ai/grok-4.5 | 0.901 ±0.02 | 0.894 | 0.909 | 6,00 |
| z-ai/glm-5.2 | 0.872 ±0.04 | 0.84 | 0.909 | 1,32 |
| deepseek/deepseek-v4-flash | 0.868 ±0.05 | 0.847 | 0.891 | 0,15 |
| deepseek/deepseek-chat-v3.1 | 0.867 ±0.02 | 0.902 | 0.836 | 0,79 |
| qwen/qwen3-next-80b-**a3b** | 0.784 ±0.03 | 0.754 | 0.818 | 1,10 |
| google/gemma-3-12b-it | 0.733 ±0.02 | 0.633 | 0.873 | 0,15 |
| qwen/qwen3-30b-a3b | 0.714 ±0.01 | 0.634 | 0.818 | 0,19 |
| ibm-granite/granite-4.1-8b | 0.681 ±0.06 | 0.685 | 0.691 | 0,10 |
| mistralai/ministral-8b | 0.660 ±0.33 | 0.832 | 0.691 | 0,15 |
| ibm-granite/granite-4.0-h-micro | 0.417 ±0.00 | 0.385 | 0.455 | 0,11 |

**Sättigung gebrochen:** kein 1.0 mehr; ein echter Gradient von 0.42 bis 0.93.

## Die vier Befunde

1. **Der Kosten-Sieger von HARD1 fällt.** gemma-3-12b (1.0 → **0.733**) und qwen3-30b (0.989 → **0.714**)
   brechen ein — sie fangen die *leichten* Fehler, aber nicht die *subtilen*. Die frühere Aussage „ein
   12B reicht" gilt **nur für leichte** epistemische Checks, **nicht** für subtile.
2. **Ein gutes ~31B bleibt aber nah am Frontier — günstig.** gemma-4-31b (**$0,16**) erreicht **0.909**,
   nur 1,8 Punkte unter gpt-5.1 (0.927, $10) — ~65× billiger. Die Effizienz-These überlebt HARD2 **am
   oberen Ende**; der Absturz ist bei ~12B und bei MoE-mit-wenig-aktiven-Experten.
3. **Aktive Parameter zählen:** qwen3-next-80b-**a3b** (nur ~3B aktiv) fällt auf **0.784** — deutlich
   unter das dichte 31B. Nennparameter ≠ Fähigkeit.
4. **Der eigentliche Härtetreiber ist EIN Fehlertyp** (per-Flag-Recall über alle Modelle):

   | Flag | Recall (alle Modelle) | Anmerkung |
   |---|---|---|
   | **significance_not_importance** | **0.43** | mit Abstand am schwersten — selbst Frontier verfehlt |
   | untraceable_citation | 0.76 | subtile Selbstzitat-Variante (G07) |
   | heuristic_not_empirical | 0.90 | |
   | causal_overreach | 0.91 | |
   | base_rate_neglect | 0.96 | überraschend gut erkannt |
   | source_domain / self_sealing / overclaim | 0.99 | ~gelöst |

## Der schärfste — und ehrlich eingeordnete — Einzelbefund

**LLMs verwechseln systematisch statistische Signifikanz mit Effektgröße/Bedeutung** (Recall 0.43).
Items G03 („p < 0.001, also klar weit wirksamer") und G15 werden fast nie exakt getroffen (Exact 0.09
bzw. 0.00).

**Aber ehrlich:** ein Teil davon ist **Taxonomie-Überlappung**, nicht reines Modellversagen. Viele
Modelle flaggen bei G03/G15 stattdessen **`overclaim`** (daher auch die **87 overclaim-False-Positives** —
mit Abstand die meisten). „p-Wert als Bedeutung" *ist* eine Form der Überdehnung; ob man es
`significance_not_importance` oder `overclaim` nennt, ist eine Label-Grenze. Der belastbare Kern bleibt:
**Modelle erkennen, dass hier etwas faul ist, benennen aber die *spezifische* Signifikanz-vs-Größe-
Struktur selten** — und übertreiben zugleich `overclaim` auf gut belegten Aussagen.

## Was das für DESi heißt — revidiert

- Die „8B/12B reicht"-These ist **auf subtile Fehler widerlegt**: granite-8b (0.68) und gemma-3-12b
  (0.73) sind zu schwach. DESis Sprachschicht für *subtile* Erkennung braucht **~31B dicht** (gemma-4-31b,
  günstig) — nicht das aktuelle Router-Modell und nicht ein MoE-mit-3B-aktiv.
- **Hier könnten die Regeln zum ersten Mal Genauigkeit *hinzufügen*:** die zwei systematischen
  LLM-Schwächen sind **regel-kodierbar** — (a) „p-Wert → Größen-/Wirksamkeitsaussage ohne Effektgröße"
  (significance-vs-importance) und (b) das *Über*-Flaggen von `overclaim` auf abgesicherten Aussagen.
  Eine deterministische Regel, die genau diese Muster prüft, könnte ein schwaches Modell auf diesen
  Fällen schlagen — **eine konkrete, testbare Hypothese** (granite-8b allein vs. + Regel), die HARD2
  erstmals messbar macht.

## Grenzen
- 18 Items, self-authored Labels; ~3 als `debatable` markiert (G07 Selbstzitat, G17 breites CI, und die
  significance↔overclaim-Grauzone durchzieht mehrere). Für ein Paper: **mehr Items + ≥2 unabhängige
  Annotatoren (κ)** — hier besonders wegen der Flag-Überlappung.
- Die significance/overclaim-Überlappung sollte in einer v2 durch schärfere Flag-Definitionen oder
  Zusammenlegen entschärft werden.

## Reproduktion
`redteam/hard2/{items,prompt}.py`; Scorer geteilt aus `redteam/hard/score.py`. Rohantworten verbatim:
`redteam/hard2/external_runs/<slug>/run_*.txt`. Scorecard: `redteam/hard2/hard2_scorecard.json`.
Runner: `python scripts/run_hard_benchmark.py --benchmark hard2 --models "<id>:<slug>,..."`
(`OPENROUTER_API_KEY` aus env, nie eingebettet).
