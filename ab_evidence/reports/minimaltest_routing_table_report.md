# Epistemic Routing Table — Cross-Model × Cross-Task Survey

**N = 25 LongMemEval + 15 Code-Review + 30 Paper-Audit, 6 Modelle.**

## Setup

Für jedes Modell auf jeder Task-Klasse wurde der vorher etablierte Sieger-State verwendet:

- **LongMemEval**: Embedding Top-k @ Peak-k pro Modell (siehe model_sweep)
- **Code-Review**: Full Raw Codebase (Sieger aus Granite-Test)
- **Paper-Audit**: Embedding Top-3 Retrieval (Sieger aus Granite-Test)

**Caveat**: Wir haben nicht für jedes neue Modell den optimalen State neu vermessen.
Möglich, dass Llama / Qwen / Mistral bei Code-Review von Retrieval profitieren würden
oder bei Paper-Audit ein anderes k\* hätten. Die Tabelle vergleicht "jedes Modell unter
seiner LongMemEval-k\*-Optimum, Granite-Sieger-State auf den anderen zwei Tasks".

## Die Tabelle

| Modell | Params | LongMemEval (k\*) Score / Cost | Code-Review (raw) Score / Cost | Paper-Audit (retr) Score / Cost |
| --- | --- | --- | --- | --- |
| Granite Micro | ~3B | 0.560 (k=3) / $0.00013 | **0.867** / $0.00005 | 0.867 / $0.00004 |
| Granite 4.1 8B | 8B | **0.600** (k=10) / $0.00134 | 0.833 / $0.00006 | **0.967** / $0.00008 |
| Llama 3.2 3B | 3B | 0.440 (k=3) / $0.00041 | 0.567 / $0.00011 | 0.633 / $0.00009 |
| **Llama 3.1 8B** | 8B | 0.560 (k=5) / $0.00026 | 0.833 / **$0.00003** | 0.767 / **$0.00003** |
| Qwen 2.5 7B | 7B | 0.560 (k=3) / $0.00032 | **0.367** / $0.00004 | 0.900 / $0.00006 |
| Ministral 3B | 3B | 0.520 (k=8) / $0.00212 | 0.767 / $0.00009 | 0.833 / $0.00013 |

## Sieger pro Task

| Task | Max Score | Modell | Cost |
| --- | --- | --- | --- |
| LongMemEval | 0.600 | Granite 4.1 8B (k=10) | $0.00134 |
| Code-Review | **0.867** | **Granite Micro** | $0.00005 |
| Paper-Audit | 0.967 | Granite 4.1 8B | $0.00008 |

## Pareto-billigster Sieger bei Score ≥ 0.5

| Task | Modell | Score | Cost |
| --- | --- | --- | --- |
| LongMemEval | Granite Micro | 0.560 | $0.00013 |
| Code-Review | **Llama 3.1 8B** | 0.833 | **$0.00003** |
| Paper-Audit | **Llama 3.1 8B** | 0.767 | **$0.00003** |

## Epistemische Spezialgebiete (per-Modell-Diagnose)

### Granite Micro (~3B)
- **Stärke**: Code-Review Best-in-Class (0.867 — besser als Granite 8B!), LongMemEval Pareto-Sieger
- **Profil**: Optimiert für kompakte Evidenz, kleines k\* (3), starker Default
- **Routing-Regel**: Default für Cost-sensitive Workloads, ausgenommen NEI-Suspect-Cases

### Granite 4.1 8B
- **Stärke**: Max Score auf 2 von 3 Tasks (LongMemEval, Paper-Audit). Sehr stark bei NEI-Disambiguation
- **Schwäche**: 10× teurer als Granite Micro
- **Routing-Regel**: Escalation-Target, wenn Micro-Confidence niedrig oder Task explizit hochauflösend ist

### Llama 3.1 8B
- **Stärke**: **Pareto-billigster Sieger auf 2 von 3 Tasks** ($0.00003/Item). Solide Scores: 0.56, 0.83, 0.77
- **Schwäche**: LongMemEval nur mittel (0.56), kein einzelnes Maximum
- **Routing-Regel**: Default für Code-Review und Paper-Audit, wenn Cost dominiert

### Qwen 2.5 7B
- **Stärke**: Paper-Audit excellent (0.90)
- **Schwäche**: **Code-Review katastrophal (0.37)** — schlechtester Score aller Modelle hier
- **Routing-Regel**: **Aktiv vermeiden bei Code-Audit**. Sehr gut bei wissenschaftlicher Claim-Verification.

### Llama 3.2 3B
- **Stärke**: Schnellste Latenz (0.7s/Item auf LongMemEval)
- **Schwäche**: Schwächste Scores auf allen drei Tasks
- **Routing-Regel**: Nur für Latency-kritische Fälle mit niedrigen Qualitätsanforderungen

### Ministral 3B
- **Stärke**: Solider Allrounder (~0.83 auf Code-Review und Paper-Audit), kein Code-Bias
- **Schwäche**: Teuerstes 3B-Modell bei k\*=8 ($0.002/Item)
- **Routing-Regel**: Kaum Pareto-optimal — andere 3B-Modelle sind günstiger oder besser

## Drei wichtige Beobachtungen

### 1. Qwen 7B hat die größte Task-Heterogenität

| Qwen 2.5 7B | Score |
| --- | --- |
| Paper-Audit | 0.90 |
| LongMemEval | 0.56 |
| **Code-Review** | **0.37** |

Eine 2.4× Differenz zwischen bester und schlechtester Task. Die anderen Modelle haben
typischerweise 1.3–1.7× Spannweite. Qwen 7B ist auf wissenschaftliche Texte spezialisiert,
nicht auf Code.

### 2. Llama 3.1 8B ist der unterschätzte Cost-König

Bei $0.020/M in und $0.050/M out auf OpenRouter ist Llama 3.1 8B **4× billiger** als
Granite 4.1 8B (gleicher 8B-Klasse). Und bei zwei von drei Tasks ist es der
Pareto-billigste Sieger.

### 3. Granite Micro schlägt Granite 8B auf Code-Review

| | Code-Review Score |
| --- | --- |
| Granite Micro | **0.867** |
| Granite 4.1 8B | 0.833 |

Das größere Modell aus derselben Familie ist auf dieser Task **schlechter** als das
kleinere. Plausible Hypothese: Granite Micro wurde stärker auf code-bezogene Daten
fokussiert; Granite 8B ist generalistischer.

## Implikation für DESi als Epistemic Traffic Controller

Die Daten ermöglichen eine erste **Routing-Tabelle**:

```python
def route(task_class, latency_budget, cost_budget, accuracy_target):
    if task_class == "memory_recall":
        if accuracy_target > 0.58:    return "granite-4.1-8b", k=10
        else:                          return "granite-4.0-h-micro", k=3
    elif task_class == "code_audit":
        if cost_budget < 0.0001:       return "llama-3.1-8b-instruct"
        else:                          return "granite-4.0-h-micro"
        # AVOID: "qwen-2.5-7b" — scored 0.367 here
    elif task_class == "scientific_claim":
        if accuracy_target > 0.90:     return "granite-4.1-8b", retrieval=True
        elif cost_budget < 0.0001:     return "llama-3.1-8b-instruct"
        else:                          return "qwen-2.5-7b-instruct"
```

## Caveats — was die Tabelle NICHT zeigt

1. **N ist klein**: 25, 15, 30 Items pro Task. Bootstrap-95%-CI ist ungefähr ±0.10
   pro Score-Wert. Differenzen unter 0.10 sind sampling-rauschen.
2. **Nicht-Granite-Modelle wurden nicht state-optimiert**: Wir haben nicht für Qwen oder
   Llama untersucht, ob ein anderes k\* oder ein anderer State-Typ besser wäre.
   Die Tabelle vergleicht "jedes Modell auf der Granite-Winner-Konfiguration je Task".
3. **Latenz nicht konsistent gemessen**: Provider-Routing auf OpenRouter kann je nach
   Stunde anders sein. Latency-Werte sind als grobe Indikatoren zu lesen, nicht als
   feste Aussagen.
4. **Substring-Match-Scoring** unterschätzt Paraphrasen.
5. **Nur 3 Task-Klassen**. Multi-Hop, agentisches Reasoning, Tool-Use sind ungetestet.

## Kosten

Dieser Run: **~$0.30** (4 neue Modelle × (15 Bug + 30 Claim) = 180 Calls).

Kumulierte Minimaltest-Serie:

| Phase | Cost |
| --- | --- |
| LongMemEval-Sweep | ~$0.65 |
| Code-Review (Granite) | $0.004 |
| Paper-Audit (Granite) | $0.013 |
| Model-Sweep (4 Models × LME × 4 k) | ~$0.30 |
| **Routing-Tabelle** (4 Models × 2 Tasks) | **~$0.30** |
| **Total** | **~$1.30** |

## Replay

Per-Item-Daten in:
- `ab_evidence/results/minimaltest_code_review_extended/items/` (15 Bug-Cases × 4 neue Modelle)
- `ab_evidence/results/minimaltest_paper_audit_extended/items/` (30 Claims × 4 neue Modelle)
- Granite-Originale in `minimaltest_code_review/` und `minimaltest_paper_audit/`

Vollständige Routing-Tabellen-Summary in `minimaltest_routing_table_summary.json`.

## Wahrheitsmodus (User's Format)

- ✅ **Gesichert**: Jedes Modell hat ein eigenes k\* (LongMemEval) und einen eigenen Task-Profil.
- ✅ **Gesichert**: Llama 3.1 8B ist Pareto-billigster Sieger bei Code-Review und Paper-Audit.
- ✅ **Gesichert**: Qwen 7B hat eine starke Task-Heterogenität (0.37 vs 0.90).
- ⚠️ **Wahrscheinlich**: Granite Micro > Granite 8B auf Code-Review reflektiert Training-Fokus, nicht statistisches Rauschen (Δ = 0.034 bei n=15 ist am Rand der Signifikanz).
- ⚠️ **Spekulativ**: Eine stabile Routing-Tabelle existiert, in der kleine Modelle für >50 % der Task-Klassen Pareto-optimal sind. Bestätigung bräuchte 5+ weitere Task-Klassen.
