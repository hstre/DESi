# Hard benchmark — jetzt diskriminiert er

*Der Pilot war zu leicht (alle 5/5). Dieser Satz ist bewusst schwer: rohe, eingebettete Fehler,
Near-Miss-Paare, Multi-Flag- und Zero-Flag-Items, adversariale Clean-Controls. Multi-Label-Scoring
(Precision/Recall/F1), Ground Truth aus dem Text selbst. Blind, cross-vendor, 5 Läufe je Modell.*

## Ergebnis — 11 Modelle (14 Items: 5×1-Flag, 2×2-Flag, 7 clean; blind, 5 Läufe je Modell)

| Modell | Klasse | F1 (±σ) | P | R | $/M-Token (out) |
|---|---|---|---|---|---|
| **google/gemma-4-31b-it:free** | 31B, **frei** | **1.00 ±0.00** | 1.00 | 1.00 | **0** |
| **qwen/qwen3-next-80b-a3b-instruct** | 80B-a3b | **1.00 ±0.00** | 1.00 | 1.00 | 1,10 |
| openai/gpt-5.1 | frontier | 0.989 ±0.02 | 0.98 | 1.00 | 10,00 |
| deepseek/deepseek-v4-flash | günstig | 0.978 ±0.03 | 0.98 | 0.978 | **0,15** |
| z-ai/glm-5.2 | günstig | 0.978 ±0.03 | 0.98 | 0.978 | 1,32 |
| poolside/laguna-m.1:free | **frei** | 0.946 ±0.03 | 0.944 | 0.956 | 0 |
| deepseek/deepseek-v4-pro | günstig | 0.927 ±0.02 | 0.887 | 0.978 | 0,87 |
| x-ai/grok-4.5 | frontier | 0.926 ±0.04 | 0.88 | 0.978 | 6,00 |
| google/gemini-2.5-pro | frontier | 0.901 ±0.03 | 1.00 | 0.822 | 10,00 |
| ibm-granite/granite-4.1-8b | 8B | 0.892 ±0.06 | 0.884 | 0.911 | 0,10 |
| ibm-granite/granite-4.0-h-micro | ~3B | 0.538 ±0.00 | 0.412 | 0.778 | 0,11 |

*(qwen3-next-80b:free war rate-limitiert → die kostenpflichtige, identische Variante genommen.)*

**Drei harte Befunde:**

1. **Ein FREIES 31B-Modell (gemma-4-31b) und ein günstiges 80B (qwen3-next) erreichen F1 = 1.00** —
   und **schlagen damit das teuerste Frontier-Modell** (gpt-5.1, 0.989, $10). deepseek-v4-flash
   (**$0,15**) und glm-5.2 liegen bei 0.978. **Auf Kosten-pro-Qualität dominieren die freien/günstigen
   Modelle das Frontier klar** (≈65× billiger bei gleicher/besserer F1).

2. **Der Benchmark ist am oberen Ende gesättigt:** alles ab ~30B liegt bei **F1 0.89–1.00** — Frontier
   *und* frei *und* günstig. Harte epistemische Fehlererkennung (auf selbst-enthaltenen Items) ist
   **keine Frontier-Fähigkeit**, sondern breit verfügbar.

3. **Der einzige echte Bruch ist die Größen-Schwelle unten:** granite-**micro (3B) kollabiert**
   (F1 0.538, deterministisch *falsch*, σ = 0), granite-**8B** trägt (0.892), **≥30B** ~perfekt.

## Der eigentliche Diskriminator: Multi-Flag-Items

Die zwei Items mit **zwei** verschränkten Fehlern trennen das Feld:

- **H11** (gold: `overclaim` + `untraceable_citation`): GPT 5/5, **Grok 4/5, Gemini 0/5** — Gemini
  meldet nur *einen* der beiden Fehler (übersieht `overclaim`).
- **H12** (gold: `heuristic_not_empirical` + `source_domain_mismatch`): GPT 5/5, Grok 4/5,
  **Gemini 2/5** — übersieht meist den Heuristik-Fehler.

**Befund:** Frontier-Modelle **unter-berichten bei mehreren verschränkten Fehlern** — sie tendieren
zu „ein Flag pro Item". Genau dort (und in der Lauf-zu-Lauf-Varianz, σ 0.02–0.04) liegt die reale
Schwäche, die der leichte Test verdeckt hatte.

## Ehrlichkeit zur Ground Truth

Zwei „Fehler" sind **Label-Ambiguität**, kein Modellversagen:
- **H09** (gold: nur `heuristic`): GPT setzt zusätzlich `overclaim` — vertretbar, denn „R = 0.72 …
  shows … empirically robust" *ist* auch ein milder Overclaim. Meine Ein-Flag-Wertung ist strittig.
- **H05** (gold: `domain_mismatch`): Grok setzt zusätzlich `untraceable_citation` — die Quelle ist
  *benannt* (JGR-Artikel), nur domänenfremd; Groks Zusatz-Flag ist also eher falsch, aber die Nähe
  zeigt die Grauzone.

Von 14 Items sind ~2 **strittig** (`debatable`); Uneinigkeit dort ist Datum, nicht Fehler. Das ist
selbst ein Befund: **epistemische Ground Truth ist bei harten Fällen unscharf.**

## Was das für DESi bedeutet — zwei Seiten, beide ehrlich

**Stark bestätigt: „Du brauchst kein Frontier-Modell."** DESis Architektur ist „LLM für Sprache,
Regeln für Logik" — die Sprachschicht ist ein kleines/günstiges Modell. Der Test zeigt: die
Sprachschicht kann **kostenlos** F1 = 1.00 erreichen (gemma-4-31b:free) oder für $0,15/M-Token F1 0.978
(deepseek-v4-flash). Frontier-Kosten sind für diese Aufgabe **nicht nötig**. Einzige Bedingung: **nicht
zu klein** — das 3B-*micro* im aktuellen Router-Setup kollabiert (F1 0.54); ~30B frei/günstig ist der
Sweet Spot.

**Ehrlich einschränkend: die Regeln zeigen hier *keinen* Genauigkeits-Vorteil.** Da freie Modelle
bereits F1 = 1.00 liefern, kann ein deterministisches Regel-Gate die **Genauigkeit** am oberen Ende
nicht mehr verbessern — sie ist schon perfekt und **gratis**. DESis Regel-Wert reduziert sich damit auf
das, was ein LLM *nicht* liefert: **σ = 0 als Garantie** (statt empirisch), eine **auditierbare
Regel-Spur**, und feste, überprüfbare Semantik — nicht auf höhere Trefferquote. Das ist ein echter,
aber **engerer** Anspruch als „bessere Erkennung".

**Der Benchmark ist zu leicht, um mehr zu zeigen.** Er sättigt ab ~30B (0.89–1.00). Wo DESis Regeln
die Genauigkeit *verbessern* könnten, läge erst dort, wo auch 30B+-Modelle unter ~0.85 fallen — solche
Items gibt es hier nicht (nur das 3B-Modell scheitert). Um DESis Gate-These auf **Genauigkeit** zu
prüfen, braucht es **härtere Items** *und* den Vergleich granite-8b-allein vs. granite-8b + Regeln.
Auf **Determinismus/Auditierbarkeit** ist DESis Vorteil dagegen schon jetzt real und modell-unabhängig.

## Veröffentlichung

Der **publikationsreife Befund** ist jetzt der **Kosten/Fähigkeits-Befund**, nicht ein DESi-Vorteil:
*„Harte epistemische Fehlererkennung auf selbst-enthaltenen Items ist keine Frontier-Fähigkeit — ein
**freies** 31B und ein günstiges 80B erreichen F1 = 1.00 und schlagen ein $10/M-Token-Frontier-Modell;
der einzige Bruch ist eine Größen-Schwelle unterhalb ~8B."* Das ist neu, überraschend und
reproduzierbar — und für DESis „kein Frontier nötig"-These die stärkste Stütze bisher.

Was für diesen Befund noch fehlt: **mehr Items** (14 → ~50–100, mehr Domänen) und **unabhängige
Label-Validierung** (≥2 Annotatoren; κ) — gerade wegen der ~2 strittigen Items.

Was der **DESi-Regel-Vorteil** angeht, ist die Lage nüchtern: auf **Genauigkeit** kann er hier nicht
gezeigt werden (freie Modelle sind schon perfekt); er lebt von **Determinismus + Auditierbarkeit**.
Ein *Genauigkeits*-Beleg bräuchte **härtere Items** (wo auch ≥30B-Modelle < 0.85 fallen) plus den
direkten Vergleich *granite-8b allein vs. granite-8b + Regeln*. Ohne den ist „Regeln verbessern die
Erkennung" **unbewiesen** — und das sollte kein Paper behaupten.

## Reproduktion
Prompt/Scorer: `redteam/hard/{prompt,score,items}.py`. Rohantworten verbatim:
`redteam/hard/external_runs/<slug>/run_*.txt`. Scorecard: `redteam/hard/hard_scorecard.json`.
Runner (Key aus `OPENROUTER_API_KEY`, nie eingebettet): `scripts/run_hard_benchmark.py`.
