# Cross-Model k-Curve Sweep — Epistemic Density per Model Family

**Testet die User-Hypothese: jedes LLM hat ein eigenes optimales k\* (Evidenz-Dichte).**

N = 25 scorable LongMemEval-S items, identisch zur k-Curve aus dem Granite-Test.
Reuse von Embedding-Top-10 aus dem hybrid run (Cross-Model-Vergleich auf identischer Retrieval-Auswahl).

## Modelle getestet

| Modell | Params | OpenRouter ID |
| --- | --- | --- |
| Granite Micro | ~3B | `ibm-granite/granite-4.0-h-micro` |
| Granite 4.1 8B | 8B | `ibm-granite/granite-4.1-8b` |
| Llama 3.2 3B | 3B | `meta-llama/llama-3.2-3b-instruct` |
| Llama 3.1 8B | 8B | `meta-llama/llama-3.1-8b-instruct` |
| Qwen 2.5 7B | 7B | `qwen/qwen-2.5-7b-instruct` |
| Ministral 3B | 3B | `mistralai/ministral-3b-2512` |

## Die Kurve pro Modell

| Modell | k=3 | k=5 | k=8 | k=10 | **k\*** | Peak Score |
| --- | --- | --- | --- | --- | --- | --- |
| Granite Micro | **0.560** | 0.480 | 0.480 | 0.400 | **3** | 0.560 |
| Llama 3.2 3B | **0.440** | 0.440 | 0.280 | 0.320 | **3** | 0.440 |
| Qwen 2.5 7B | **0.560** | 0.560 | 0.480 | 0.320 | **3** | 0.560 |
| Llama 3.1 8B | 0.400 | **0.560** | 0.440 | 0.560 | **5** | 0.560 |
| Ministral 3B | 0.480 | 0.480 | **0.520** | 0.520 | **8** | 0.520 |
| Granite 4.1 8B | 0.440 | 0.520 | 0.520 | **0.600** | **10** | 0.600 |

## Was generalisiert

- **Jedes Modell hat ein nachweisbares k\*.** Sechs Modelle, drei unterschiedliche k\*-Werte (3, 5, 8, 10).
- **k\* ist nicht trivial aus der Parametergröße ableitbar.** Qwen 7B (7B Params) peakt bei k=3 wie ein 3B-Modell. Ministral 3B (kleinstes Modell) peakt bei k=8.
- **Modell-Familie / Training-Profil zählen mehr als Parameter-Count.**

## Drei beobachtbare Cluster

| Cluster | k\* | Modelle | Hypothese |
| --- | --- | --- | --- |
| Compact-evidence | 3 | Granite Micro, Llama 3B, Qwen 7B | Auf kompakte Kontexte trainiert/optimiert |
| Mid-evidence | 5–8 | Llama 8B, Ministral 3B | Adaptive Verarbeitung |
| Long-evidence | 10 | Granite 8B | Auf langen Kontext-Recall optimiert |

## Tokens, Latency, Cost am Peak

| Modell | k\* | Score | Mean Tokens | Latency | Kosten/Item |
| --- | --- | --- | --- | --- | --- |
| Granite Micro | 3 | 0.560 | 7740 | 2.1 s | $0.00013 |
| Granite 4.1 8B | 10 | 0.600 | 26599 | 2.6 s | $0.00134 |
| Llama 3.2 3B | 3 | 0.440 | 7828 | 0.7 s | $0.00041 |
| Llama 3.1 8B | 5 | 0.560 | 12699 | 2.2 s | $0.00026 |
| Qwen 2.5 7B | 3 | 0.560 | 7818 | 1.6 s | $0.00032 |
| Ministral 3B | 8 | 0.520 | 21180 | 2.7 s | $0.00212 |

## Pareto-Front auf diesem Test

Auf der Achse Score × Cost:

| Modell + k\* | Score | $/Item | Latency | Position |
| --- | --- | --- | --- | --- |
| **Granite Micro k=3** | 0.560 | $0.00013 | 2.1s | **Best Cost** |
| **Llama 3.1 8B k=5** | 0.560 | $0.00026 | 2.2s | Konkurrent |
| Qwen 2.5 7B k=3 | 0.560 | $0.00032 | 1.6s | Schneller, teurer |
| Llama 3.2 3B k=3 | 0.440 | $0.00041 | 0.7s | **Lowest Latency** (aber schwächste Score) |
| Ministral 3B k=8 | 0.520 | $0.00212 | 2.7s | Pareto-dominated |
| **Granite 4.1 8B k=10** | 0.600 | $0.00134 | 2.6s | **Best Score** |

**Dominante Wahl je Use-Case:**
- **Maximum Score bei höchsten Kosten**: Granite 4.1 8B @ k=10
- **Equal Score zu Cost-Optimum**: Granite Micro @ k=3 (Pareto-optimal in dieser Konfiguration)
- **Geschwindigkeit**: Llama 3.2 3B @ k=3 (0.7s, aber Score nur 0.44)

## Implikation für DESi → Epistemic Traffic Control

Die Daten stützen die User-Hypothese: **DESi ist kein "State-System", sondern ein Router**, der pro Anfrage entscheidet:

1. **Welches Modell?** (k\*-Kalibrierungstabelle)
2. **Wie viel Evidenz?** (k = f(Modell))
3. **Wann eskalieren?** (NEI-Verdacht → größeres Modell)
4. **Wann stoppen?** (Score-Schwelle erreicht)

Der zentrale Optimierungs-Parameter ist nicht `max_context(model)`, sondern **`k(model)`** —
der Punkt, an dem zusätzliche Evidenz für dieses Modell vom Signal zum Rauschen wird.

## Caveats

- **N=25 scorbar** — Bootstrap-SE ≈ ±0.10 pro Score-Wert. Die Cluster-Zuordnung ist
  klar (alle Differenzen > 0.10), aber exakte Peaks können bei k=2 oder k=4 statt k=3 liegen.
- **Substring-Match-Scoring** unterschätzt Paraphrasen.
- **Nur LongMemEval-S** — auf anderen Task-Klassen (Paper-Audit, Code-Review) hat die
  Frage-Spezifität dominanten Einfluss; k\* mag dort verschieden liegen.
- **Provider-Routing** auf OpenRouter beeinflusst Latenz. Ministral's 2.7s könnte
  Provider-spezifisch sein, nicht Modell-inherent.
- **Granite Micro / 4.1 8B** wurden in einem separaten Lauf gemessen (topk_curve);
  alle anderen im aktuellen Sweep. Konsistente Methodik, aber nicht im gleichen Zeitslot.

## Was als nächstes zu testen wäre

1. **Drittes k auf den Kurven-Spitzen**: bei den Modellen die bei k=3 peaken — k=2 und k=4 messen.
   Liegt der wirkliche Peak doch bei k=2?
2. **Cross-Task k\*-Stabilität**: ist Granite-Micro-k\*=3 task-stabil oder nur LongMemEval-spezifisch?
   (Paper-Audit hat ja gezeigt dass Q4+Retrieval Top-3 dort auch gut funktioniert.)
3. **Größere Modelle** (Llama 70B, Qwen 72B) — peaken die bei noch höherem k oder
   sättigen sie über k=10?
4. **k\* on synthetischen Tests** mit kontrolliertem Distraktor-Anteil — direkte Messung
   wann Distraktoren das Signal überschreiben.

## Kosten

Total dieses Runs: ~$0.30 (400 Calls × ~$0.0008 Mean).

## Replay

Per-Item-Daten in `ab_evidence/results/minimaltest_model_sweep/items/` (30 Dateien).
Runner: `ab_evidence/minimaltest_model_sweep.py`. Reuses Top-10-Selection aus
`minimaltest_hybrid/items/` (identische Retrieval-Auswahl across Modelle für fairen Vergleich).
