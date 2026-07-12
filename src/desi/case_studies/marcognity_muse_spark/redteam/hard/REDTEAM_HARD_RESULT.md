# Hard benchmark — jetzt diskriminiert er

*Der Pilot war zu leicht (alle 5/5). Dieser Satz ist bewusst schwer: rohe, eingebettete Fehler,
Near-Miss-Paare, Multi-Flag- und Zero-Flag-Items, adversariale Clean-Controls. Multi-Label-Scoring
(Precision/Recall/F1), Ground Truth aus dem Text selbst. Blind, cross-vendor, 5 Läufe je Modell.*

## Ergebnis (14 Items: 5×1-Flag, 2×2-Flag, 7 clean)

| Modell | F1 (±σ) | Exact-Match | Precision | Recall | Fehlerprofil |
|---|---|---|---|---|---|
| **openai/gpt-5.1** | **0.989 ±0.02** | 0.986 | 0.98 | 1.00 | fängt alles; ein seltener (vertretbarer) Over-Flag |
| **x-ai/grok-4.5** | 0.926 ±0.04 | 0.90 | 0.88 | 0.978 | hohe Trefferquote, **über-flaggt** (Domain/Multi) |
| **google/gemini-2.5-pro** | 0.901 ±0.03 | 0.886 | **1.00** | 0.822 | nie Over-Flag, aber **übersieht** ~18 % |

**Erstmals echte Spreizung** — und drei **verschiedene Fehlerprofile**: GPT-5.1 nahezu perfekt,
Grok neigt zum Über-Flaggen (P 0.88), Gemini zum Unter-Flaggen (R 0.822, aber P 1.0). Der Test
diskriminiert also sowohl zwischen Modellen als auch in der Art des Fehlers.

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

## Wo DESi steht — ehrlich, weil unbequem-korrekt

**DESis Regel-Reviewer läuft auf diesen Items NICHT.** Er arbeitet auf bereits extrahierten,
typisierten Claims aus der Fallstudien-Fixierung; er hat **kein Rohtext-Frontend**. Auf rohem Text
ist DESi **nicht anwendbar** als End-to-End-Reviewer — sein Platz ist ein deterministisches Gate
*nach* einer LLM-Extraktion. Deshalb steht in der Tabelle **kein DESi-Wert**; ich erfinde keinen.

Aber der Härtetest legt eine **motivierte Hypothese** frei (nicht: einen Beleg): die zwei
LLM-Schwächen, die er zeigt — **Unter-Berichten bei Multi-Flag** und **Lauf-Varianz** — sind genau
das, was ein deterministisches Regel-Gate auf den **abgedeckten** Fehlertypen nicht hätte: es meldet
alle zutreffenden Flags, immer, mit σ = 0. *Wenn* die vorgelagerte Claim-Extraktion zuverlässig ist,
könnte DESi die beobachteten FN/Varianz auf den fünf codierten Mustern glätten. **Ungetestet** —
weil das Extraktions-Frontend hier nicht existiert, und weil DESis Abdeckung fix ist (5 Typen),
während ein LLM beliebige neue Fehlertypen erfasst.

## Veröffentlichung

**Näher dran, aber noch nicht.** Was jetzt steht, ist interessant: cross-vendor, blind, harte Items,
**echte Spreizung + ein konkreter Schwachpunkt (Multi-Flag-Unter-Berichten)**. Für eine
Veröffentlichung fehlt:
- **mehr Items** (14 → ~50–100, mehr Domänen),
- **unabhängige Label-Validierung** (≥2 menschliche Annotatoren; κ berichten) — gerade wegen der
  Grauzone,
- **DESi tatsächlich laufen lassen** über ein Extraktions-Frontend, um die Gate-Hypothese zu prüfen.

Dann wäre die Aussage tragfähig: *„Frontier-Modelle erkennen harte epistemische Fehler stark (F1
0.90–0.99), unter-berichten aber verschränkte Fehler und variieren zwischen Läufen; ein
deterministisches Gate auf den codierten Mustern stabilisiert das bei ~10⁵–10⁶× weniger Energie —
sofern die Extraktion trägt."* Das ist eine **prüfbare, dauerhafte** These, keine Werbung.

## Reproduktion
Prompt/Scorer: `redteam/hard/{prompt,score,items}.py`. Rohantworten verbatim:
`redteam/hard/external_runs/<slug>/run_*.txt`. Scorecard: `redteam/hard/hard_scorecard.json`.
Runner (Key aus `OPENROUTER_API_KEY`, nie eingebettet): `scripts/run_hard_benchmark.py`.
