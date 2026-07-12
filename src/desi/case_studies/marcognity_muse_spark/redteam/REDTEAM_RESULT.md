# Red-Team-Ergebnis — der External-Slot, mit einem echten blinden Frontier-Reviewer gefüllt

*Der Harness war der Aufbau; dies ist der erste echte Lauf. Ergebnis zuerst, dann die Grenzen,
die es (noch) unveröffentlichbar machen.*

## Aufbau des Laufs

- **Reviewer:** ein **blinder Claude-Opus-4.8-Reviewer** — fünf unabhängige, frische Subagenten,
  die meinen Kontext (und damit den DESi-Answer-Key) **nicht** haben. Sie sahen nur die neutrale
  Rubrik (fünf Flag-Definitionen) und sieben Auszüge mit neutralen IDs (E1–E7), gemischt, ohne
  „failure/control"-Label (`redteam/external_probe.py`, roh gespeichert in
  `redteam/external_runs/claude_blind/run_*.json`).
- **NICHT Claude Science** — das Produkt war in dieser Umgebung nicht aufrufbar (keine API-Keys).
  Ein möglichst vergleichbares Frontier-Modell wurde genommen; die Einschränkung steht unten.
- **5 Läufe** für Varianz. Cost gemessen: ~20,4k Tokens/Lauf, ~102k gesamt.

## Ergebnis (5 Läufe)

| Reviewer | Catch | FP je Lauf | FP Ø | Controls sauber | Catch-Stabilität | Cost |
|---|---|---|---|---|---|---|
| naive_whole_text (Baseline) | 0/5 | [0] | 0 | 2/2 | 0 | (Stub) |
| **claude_opus_4_8_blind** | **5/5** | **[0,1,1,1,1]** | **0.8** | **2/2** | **1.0** | ~102k Tok / 5 Läufe |
| DESi (Referenz) | 5/5\* | [0] | 0\* | 2/2 | 1.0 | vernachlässigbar (CPU) |

\* per Konstruktion.

**Was tatsächlich passierte:**
- Der blinde Frontier-Reviewer **fängt alle fünf Failure-Modes in jedem Lauf** (Catch 5/5, stabil).
  Das ist der wichtigste, *nicht* selbstbedienende Befund: die Geschichte ist **nicht** „DESi schlägt
  das LLM beim Fangen". Beide fangen 5/5.
- Er **hält beide Clean-Controls in jedem Lauf sauber** — gute Präzision auf den Negativen.
- Er zeigt eine **milde Über-Flag-Tendenz**: in 4/5 Läufen hängt er `self_sealing` an den
  Untraceable-Citation-Auszug (E4/P1), wo es nicht hingehört → ein echter False Positive (FP Ø 0.8,
  Varianz zwischen 0 und 1).

## Ehrliche Interpretation

Auf **diesem Pilot** ist der eigentliche Unterschied nicht der Catch (beide 5/5), sondern:
**DESi = 0 FP, deterministisch (0 Varianz), ~0 Cost** — der Frontier-Reviewer = **milder FP + Lauf-zu-
Lauf-Varianz + echte Token-Kosten**. Das ist eine **partielle, ehrliche Stütze** der
Architektur-Effizienz-These: *vergleichbare Fang-Leistung, aber DESi mit deterministischer Präzision
zu vernachlässigbarem Compute* — **keine** „A schlägt B"-Aussage.

## Grenzen — warum das (noch) KEIN veröffentlichbarer Befund ist

1. **Vor-destillierte Auszüge (die größte Grenze).** Ich habe dem Reviewer bereits **zugespitzte,
   isolierte Snippets** gegeben, die das Problem quasi ansagen. Ein echter Background-Reviewer sieht
   **rohe Volltexte**, nicht kuratierte Auszüge. Das **überschätzt** die Fang-Leichtigkeit massiv; auf
   Rohtext läge Catch vermutlich niedriger und FP anders.
2. **Gleiche Modellfamilie.** Der Reviewer ist ein Claude-Modell — dieselbe Familie wie der
   Harness-Autor. **Modellseitige Unabhängigkeit ist begrenzt.** (Blind zum Answer-Key ist er
   allerdings — die *evidenzseitige* Unabhängigkeit hält.)
3. **Nicht Claude Science.** Das eigentlich interessante Zielsystem war nicht verfügbar.
4. **n=1, winzig.** Ein Fall, 5 Failure-Probes + 2 Controls, 5 Läufe. Ein **Pilot**, kein Benchmark.
5. **DESis 5/5 und 0 FP bleiben per Konstruktion** — Referenz, kein unabhängiger Beleg.

## Empfehlung

**Noch nichts auf Hugging Face veröffentlichen.** Der Lauf zeigt: der Harness liefert ein sinnvolles,
diskriminierendes Signal (Baseline 0/5, Frontier 5/5 mit mildem FP, DESi 5/5 deterministisch) — aber
die vor-destillierten Auszüge, die gleiche Modellfamilie und n=1 disqualifizieren jede öffentliche
Aussage. Für einen echten Befund:

- **Rohe Volltext-Paper** statt zugespitzter Auszüge (der entscheidende Schritt);
- ein **cross-vendor** Frontier-Modell (GPT/Gemini neben Claude) für echte modellseitige Unabhängigkeit;
- **mehr Items/Domänen** (nicht nur Rechtsphilosophie);
- wenn möglich **Claude Science selbst** durch denselben Slot.

Erst dann trägt die Architektur-Effizienz-These — und erst dann ist es ein Befund, kein sauberer
Testlauf.

## Reproduktion
Rohantworten: `redteam/external_runs/claude_blind/run_*.json` (verbatim). Assembliert:
`redteam/external_runs/claude_blind.json`. Scoren:
`python -m desi.case_studies.marcognity_muse_spark.redteam --external redteam/external_runs/claude_blind.json`.
Kombinierte Scorecard: `redteam/external_runs/claude_blind_scorecard.json`.
