# R1-Härtung — von Phrasen-Memorierer zu generalisierender Regel (blind belegt)

*Der Hold-out zeigte: R1 ist hochpräzise, aber lexikalisch spröde. Diese Studie quantifiziert das an
einem größeren, formulierungs-diversen Signifikanz-Korpus und härtet die Regel sauber: gefrorenes R1 (v1)
auf einem **Hold-out-Test** messen, v2 **nur aus dem Dev-Split** entwickeln, dann v2 **blind** auf dem Test
prüfen. Vollständig LLM-frei (R1 ist Regex), 48 Items, mechanisch bestimmte Labels.*

## Der Aufbau

48 Signifikanz-vs-Bedeutung-Items, Labels per **fixer Entscheidungsprozedur** (Independence-Proxy, nicht
Bauchgefühl): SIG-positiv ⟺ (1) Größen-/Bedeutungsbehauptung, (2) nur durch Signifikanz gestützt, (3) **keine**
Effektgröße genannt. Split 24 dev / 24 test (je 12 SIG / 12 clean). **Die Test-Items nutzen absichtlich
Signifikanz-Marker und Größenwörter, die im Dev-Split nicht vorkommen** (game-changer, markedly, „statistically
reliable", „significant at the 1% level" …).

## Ergebnis — v1 (gefroren) vs. v2 (auf Dev gehärtet)

| Detektor | Split | Precision | Recall | F1 |
|---|---|---|---|---|
| **v1 (gefroren)** | dev | 1.000 | 0.417 | 0.588 |
| **v1 (gefroren)** | **test (blind)** | 1.000 | **0.000** | **0.000** |
| v2 (gehärtet auf dev) | dev | 1.000 | 1.000 | 1.000 |
| **v2 (gehärtet auf dev)** | **test (blind)** | **1.000** | **0.917** | **0.957** |

## Die zwei Befunde

1. **v1 war im Kern ein Phrasen-Memorierer.** Auf 12 neu formulierten Test-Positiven: **Recall 0.000** —
   es fängt *keine* einzige. Das erklärt ehrlich rückwirkend die früheren Gewinne: hard2/holdout teilten
   R1s Dev-Vokabular. Präzision blieb 1.000 (v1 feuert nie falsch — aber fast gar nicht auf ungesehene
   Formulierung).
2. **Die Sprödigkeit ist behebbar — sauber.** v2, **nur aus den 7 Dev-Fehlern** entwickelt (breiteres
   Signifikanz-/Größen-Vokabular, breiterer Effektgrößen-Guard, Null-Result-Guard), erreicht auf dem
   **blinden** Test **Recall 0.917 bei Precision 1.000** (F1 0.957). Nur T-S04 („p **fell** under 0.05" —
   Signifikanz-Marker mit eingeschobenem Verb) entgeht auch v2 — ehrlich, kein Detektor ist vollständig.
   **Null False Positives** auf den Clean-Items, inklusive der Fallen „significant at the 5% level"
   (SIG-positiv, darf nicht vom %-Guard blockiert werden) und effektgrößen-korrekter Negative.

## Gegenprobe — v2 generalisiert auch außerhalb dieses Korpus

Auf den **separaten** Sätzen (nicht zum Härten benutzt):

| Satz | v1 SIG-Recall | v2 SIG-Recall | Precision |
|---|---|---|---|
| hard2 (Dev-Benchmark) | 1.000 | 1.000 | 1.000 (beide) |
| **hold-out** | **0.571** | **1.000** | 1.000 (beide) |

v2 hebt den Hold-out-SIG-Recall von 0.571 auf 1.000 **ohne** Precision-Verlust und **ohne** Regression auf
hard2 — also kein Overfit auf den sig_corpus-Dev-Split.

## Urteil

**Die Regel ist härtbar.** R1s Sprödigkeit war real (Test-Recall 0.0), aber mit reinem Dev-Signal auf
**0.917 blind** zu heben, bei perfekter Präzision — die deterministische Reviewer-Schicht skaliert also nicht
nur auf ein enges Phrasenset. Das stärkt den DESi-Nutzen-Nachweis: nicht „eine Regel fängt zufällig die
Benchmark-Formulierungen", sondern „ein kodifizierbares Muster lässt sich zu robuster, hochpräziser Deckung
ausbauen".

**Ehrliche Grenzen (unverändert wichtig):**
- **48 self-authored Items, ein Annotator.** Die mechanische Label-Prozedur reduziert Subjektivität, ersetzt
  aber keine ≥2 unabhängigen Annotatoren (κ). Für ein Paper zwingend.
- **v2 ist immer noch lexikalisch** — T-S04 zeigt die Restlücke; „vollständig" ist eine Regex nie. Ein
  echter Produktivpfad würde v2 gegen ein großes reales p-Wert-Korpus weiter härten und die Präzision auf
  *korrekt* getrennten Signifikanz-Aussagen breit prüfen.
- Nur der **Signifikanz**-Check (R1) ist damit belegt; R2 (overclaim) bleibt wirkungslos.
- v1 bleibt eingefroren (die hard2/holdout-Ergebnisse nutzen v1); v2 ist der additive, gehärtete Nachfolger.

## Reproduktion
`python scripts/run_sig_corpus_test.py` (LLM-frei). Korpus: `redteam/sig_corpus/items.py` (dev/test).
Regeln: `redteam/hard2/rules.py` (`_v1` gefroren seit `c1f7db6`, `_v2` gehärtet auf dev). Scorecard:
`redteam/sig_corpus/sig_corpus_scorecard.json`.
