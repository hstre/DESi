# Code-Review Minimaltest — DESi für Bug-Localization?

**N = 15 geplante Bugs in Python-Modulen, je 9-Modul Codebase (1 buggy + 8 Distraktoren).**

## Setup

- **15 Bug-Cases**, jeder mit einem distinkten Bug-Typ (off-by-one, wrong operator, missing None, operator-precedence, resource leak, mutable default, inverted condition, wrong exception, slice off-by-one, integer division, shallow copy, shadowing, iterator exhaustion, format injection, TOCTOU)
- **Haystack pro Case**: 9 Module total (~600 Tokens) — 1 buggy + 8 saubere Distraktoren
- **3 State-Typen** × 2 Modelle = 6 Konditionen × 15 Cases = 90 API-Calls
- **Scoring**: 1.0 wenn Antwort den Function-Namen UND ein must-contain Marker enthält; 0.5 wenn nur eins; 0.0 wenn nichts
- **Embedding-Retrieval**: `all-MiniLM-L6-v2`, top-3 Module by Cosine-Similarity zur Audit-Frage

## Hauptergebnis

| State | Q4 (micro) | Q8 (8B) |
| --- | --- | --- |
| **Raw codebase** (alle 9 Module) | **0.867** | 0.833 |
| Oracle (nur Bug-Modul) | 0.967 | 0.967 |
| **Retrieval Top-3** | **0.367** | 0.367 |

**Q4 = Q8 auf allen drei Konditionen** — das kleine Modell ist beim Code-Review genauso gut wie das große, sofern es die richtige Code-Sicht bekommt.

## Die wichtigste Diagnose

**Embedding-Retrieval kollabiert auf 40 % Recall** — in 9 von 15 Cases war das Bug-Modul nicht in den Top-3.

| Bug-Typ | Retrieval Score | Warum |
| --- | --- | --- |
| B02 (wrong operator >18) | 1.0 | Operator-Bug hat distinktive Signal-Tokens |
| B08 (wrong exception) | 1.0 | "except IndexError" matched explizit |
| B14 (format injection) | 1.0 | "format" + "logging" hat hohe Ähnlichkeit zur Frage |
| B04 (precedence), B05 (resource), B06 (mutable), B07 (inverted), B09 (slice), B10 (int div), B11 (shallow), B13 (iterator) | **0.0** | Generische Patterns — Distraktoren matchen ähnlich gut |

**Warum funktioniert Retrieval hier nicht?** Die Audit-Frage *"Find any bugs"* enthält **kein semantisches Signal**, das auf ein bestimmtes Modul zeigt. Bei LongMemEval war die Frage spezifisch (*"Where does Emily live?"*) — da konnte Embedding die richtige Session finden. Hier ist die Frage generisch.

## Tokens, Latency, Kosten

| State | Q4 Tokens | Q4 Latency | Q8 Tokens | Q8 Latency |
| --- | --- | --- | --- | --- |
| Raw | 558 | 11.5 s | 648 | 2.1 s |
| Oracle | 155 | 10.2 s | 167 | 1.6 s |
| Retrieval | 251 | 11.8 s | 281 | 2.5 s |

Die Codebase ist klein (~600 Tokens). Token-Pressure existiert nicht. Latency ist dominated by API-Round-Trip und Output-Generation, nicht Kontext-Größe.

## Vergleich zu LongMemEval — das Muster kehrt sich um

| Dimension | LongMemEval-S | Code-Review (klein) |
| --- | --- | --- |
| Haystack-Größe | ~100k Tokens | ~600 Tokens |
| Frage-Spezifität | hoch | niedrig |
| Q4 + Raw | 0.16 (versagt) | **0.87 (sehr gut)** |
| Q4 + Top-3 Retrieval | **0.56 (Sieger)** | 0.37 (verliert massiv) |
| Q4 + Oracle | 0.48 | 0.97 (Obergrenze) |
| **Wer gewinnt?** | **Retrieval** | **Raw / Oracle** |

## Was alle Resultate zusammen sagen

> **Die DESi-State-Hypothese ist task-abhängig:**
>
> - **Bei großem Haystack + spezifischer Frage** (LongMemEval): semantische Retrieval-Bündelung schlägt Volltext deutlich. Hardware-Hebel real.
> - **Bei kleinem Haystack + generischer Frage** (kleines Code-Review): plain Volltext gewinnt. Auto-Selektion verschlechtert nur. Keine Hardware-These nötig — Q4 reicht ohnehin.
> - **Oracle** (perfekte Auswahl) ist auf BEIDEN Tasks die Obergrenze, aber der Auto-Extraktor schließt diese Lücke nur bei spezifischer Frage.

## Was noch offen ist

**Der eigentlich interessante Code-Review-Test wäre auf GRÖßERER Codebase.** Bei 50-100 Modulen mit einem Bug irgendwo drin, würde:
- Q4 + Raw eventuell scheitern (Kontext-Pressure)
- Retrieval-State eventuell helfen (sofern strukturelle statt semantische Retrieval-Signale)

Das war hier nicht getestet. Mögliche nächste Tests:
1. **Größere Codebase**: 50 Module total, Bug im einem von ihnen versteckt
2. **Strukturelle Retrieval-Signale**: Module mit Kontrollfluss + Exception-Handling + Type-Annotations zuerst (statt semantischer Frage-Ähnlichkeit)
3. **Multi-Hop-Bugs**: Bug, der Code aus 2-3 Modulen erfordert, um zu erkennen

## Kosten

Total: **$0.004** für 90 API-Calls. Code-Review ist extrem billig auf dieser Skala
(die Codebase ist klein, beide Modelle billig).

## Replay

Per-Bug-Daten in `ab_evidence/results/minimaltest_code_review/items/` (15 Dateien).
Bug-Definitions + Distraktoren in `ab_evidence/code_review_bugs.py`. Runner in
`ab_evidence/code_review_run.py`. Deterministisch bis auf Modell-Outputs.

## Fazit in einem Satz

> **DESi-State (in der einfachsten Embedding-Retrieval-Form) hilft bei Code-Review NICHT — weder Q4 noch Q8 profitieren, beide werden schlechter.** Der einfache Q4-Volltext-Audit ist auf dieser kleinen Codebase ausreichend (Score 0.867, ~600 Tokens). Die DESi-Frage für Code-Review wäre erst auf einem 100-Modul-Haystack mit strukturellen Retrieval-Signalen ernsthaft testbar.
