# Hard benchmark — jetzt diskriminiert er

*Der Pilot war zu leicht (alle 5/5). Dieser Satz ist bewusst schwer: rohe, eingebettete Fehler,
Near-Miss-Paare, Multi-Flag- und Zero-Flag-Items, adversariale Clean-Controls. Multi-Label-Scoring
(Precision/Recall/F1), Ground Truth aus dem Text selbst. Blind, cross-vendor, 5 Läufe je Modell.*

## Ergebnis (14 Items: 5×1-Flag, 2×2-Flag, 7 clean)

| Modell | F1 (±σ) | Exact-Match | Precision | Recall | Fehlerprofil |
|---|---|---|---|---|---|
| **openai/gpt-5.1** (frontier) | **0.989 ±0.02** | 0.986 | 0.98 | 1.00 | fängt alles; seltener (vertretbarer) Over-Flag |
| **x-ai/grok-4.5** (frontier) | 0.926 ±0.04 | 0.90 | 0.88 | 0.978 | hohe Trefferquote, **über-flaggt** (Domain/Multi) |
| **google/gemini-2.5-pro** (frontier) | 0.901 ±0.03 | 0.886 | **1.00** | 0.822 | nie Over-Flag, **übersieht** ~18 % |
| **ibm-granite/granite-4.1-8b** (8B) | **0.892 ±0.06** | 0.857 | 0.884 | 0.911 | **kleines Modell, ~Frontier-nah** |
| ibm-granite/granite-4.0-h-micro (~3B) | 0.538 ±0.00 | 0.357 | 0.412 | 0.778 | zu klein: über-flaggt Controls, übersieht Fehler |

**Erstmals echte Spreizung** — drei Frontier-Fehlerprofile (GPT nahezu perfekt; Grok über-, Gemini
unter-flaggt) **und ein klarer Größen-Schwellenwert bei den kleinen Modellen** (siehe eigener
Abschnitt).

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

## Kleine Modelle — DESis eigene Sprachschicht (der eigentliche Test)

DESis Architektur ist „**LLM für Sprache, Regeln für Logik**" — die Sprachschicht ist ein **kleines**
Modell (im Router-Setup `ibm-granite/granite-4.0-h-micro`). Genau deshalb ist der faire Effizienztest:
schafft ein *kleines* Modell die harten Fälle? Antwort mit klarem **Schwellenwert**:

- **granite-4.0-h-micro (~3B): F1 0.538** — **kollabiert.** Precision 0.41 (über-flaggt die
  adversarialen Clean-Controls massiv), Recall 0.78. Für harte, subtile Erkennung end-to-end **zu
  klein.** (Interessant: σ = 0 — sehr deterministisch, aber deterministisch *falsch*.)
- **granite-4.1-8b (8B): F1 0.892** — **fast Frontier.** Praktisch gleichauf mit gemini-2.5-pro
  (0.901) und nah an grok (0.926). **90 % von gpt-5.1s F1 (0.892 vs 0.989) — bei ~100× niedrigerem
  Output-Preis** (0.10 vs 10.00 $/M-Token).

**Das ist der konkrete, dauerhafte Effizienz-Befund**, den der leichte Test verdeckt hatte: nicht
„kleine Modelle können es nicht", sondern ein **Größen-Schwellenwert bei ~8B**. Ein 8B-Modell erreicht
frontier-nahe epistemische Erkennung zu einem **Hundertstel** der Kosten/Energie.

## Wo DESi steht — korrigiert und geschärft

Frühere Aussage („DESi kann Rohtext gar nicht") war zu grob. **DESis Sprachschicht IST ein kleines
Modell — und ein 8B-Granite liest Rohtext frontier-nah.** Damit:

1. **Modellwahl:** Das Router-Setup nutzt derzeit *micro* (3B) — für harte epistemische Erkennung
   **zu schwach** (F1 0.54, über-flaggt Controls). Für diese Aufgabe gehört **granite-4.1-8b** dorthin
   (immer noch winzig, ~100× billiger, F1 0.89).
2. **Regeln obendrauf:** granite-8b hat Rest-Schwächen (P 0.884 über-flaggt, R 0.911 übersieht etwas,
   σ 0.058). Genau das — **FP/FN und Varianz auf den abgedeckten Mustern** — ist, was ein
   deterministisches Regel-Gate (~0 Zusatzkosten) glätten könnte. Das ist DESis These, jetzt
   **konkret motiviert**, aber weiterhin **ungetestet** (das 8B-Modell macht hier noch das *Urteil*
   selbst; DESis Architektur würde es nur *extrahieren* lassen und die Regeln urteilen — Dekomposition
   könnte helfen oder nicht).

Ehrlich bleibt: DESis Regel-Abdeckung ist fix (5 Typen), ein LLM generalisiert auf neue Fehlertypen;
und die Regeln selbst hat hier niemand auf Rohtext laufen lassen.

## Veröffentlichung

**Deutlich näher dran.** Jetzt gibt es einen echten, konkreten Befund: cross-vendor, blind, harte
Items, echte Spreizung, ein benannter Frontier-Schwachpunkt (Multi-Flag-Unter-Berichten) — **und der
Größen-Schwellenwert: ein 8B-Modell erreicht ~90 % der Frontier-F1 zu ~1/100 der Kosten, ein 3B nicht.**
Für eine Veröffentlichung fehlt noch:
- **mehr Items** (14 → ~50–100, mehr Domänen),
- **unabhängige Label-Validierung** (≥2 Annotatoren; κ) — gerade wegen der Grauzone,
- **die Regel-Gate-Stufe testen**: granite-8b (oder eine Extraktions-Dekomposition) + DESi-Regeln vs.
  granite-8b allein — glätten die Regeln die Rest-FP/FN/Varianz?

Dann trägt die Aussage: *„Harte epistemische Fehlererkennung braucht kein Frontier-Modell — ein 8B
gelingt zu ~1/100 der Kosten (F1 0.89 vs 0.99); ein 3B nicht. Ein deterministisches Gate auf den
codierten Mustern (~0 Zusatzkosten) glättet die Rest-Fehler und die Varianz."* Das ist eine
**prüfbare, dauerhafte** These — und genau DESis Architektur.

## Reproduktion
Prompt/Scorer: `redteam/hard/{prompt,score,items}.py`. Rohantworten verbatim:
`redteam/hard/external_runs/<slug>/run_*.txt`. Scorecard: `redteam/hard/hard_scorecard.json`.
Runner (Key aus `OPENROUTER_API_KEY`, nie eingebettet): `scripts/run_hard_benchmark.py`.
