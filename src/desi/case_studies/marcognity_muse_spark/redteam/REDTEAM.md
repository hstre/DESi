# Red-Team-Benchmark — Harness für Background-Reviewer (kein Ergebnis)

*Motiviert durch Claude Science ('a background reviewer flags incorrect citations, untraceable numbers ...'). Die MarCognity/Muse-Spark-Fallstudie wird zum Prüfstein: fängt ein Reviewer die fünf epistemischen Fehler, an denen MarCognitys Validator scheiterte — **ohne** über Clean-Controls hinweg über-zu-flaggen? Deterministisch, offline.*

> Dies ist ein HARNESS, kein Ergebnis. Der DESi-Referenz-Reviewer erreicht 5/5 Catch und 0 False Positives per Konstruktion (er IST die Analyse, die die Probes definiert hat); der naive Whole-Text-Reviewer 0/5. Beides ist kein Befund. Der interessante Befund entsteht erst, wenn ein ECHTER Background-Reviewer (Claude Science, ein Frontier-LLM) durch den External-Slot läuft und die Tabelle sich füllt — und die tragfähige Aussage wäre keine 'A schlägt B', sondern eine Architektur-Effizienz-These: vergleichbare epistemische Kontrolle bei deutlich geringerem, deterministischerem Compute.

## Probes

| Key | Art | Ziel-Flag | Anker | Claims |
|---|---|---|---|---|
| P1-untraceable | failure | `untraceable_citation` | muse:L170-202 | VAL-01, VAL-02 |
| P2-domain | failure | `source_domain_mismatch` | muse:L174-198; muse:L235 | VAL-01, VAL-03 |
| P3-selfsealing | failure | `self_sealing` | muse:L237 | EB-01, EB-02 |
| P4-overclaim | failure | `overclaim` | muse:L237 | EB-02 |
| P5-heuristic | failure | `heuristic_not_empirical` | muse:L87-100 | HEUR-01, HEUR-02, HEUR-03 |
| C1-clean-citation | control | — (clean) | constructed | — |
| C2-clean-heuristic | control | — (clean) | constructed | — |

## Scorecard (mehrdimensional — Catch allein wäre zu schwach)

| Reviewer | Catch | False Positives | Controls sauber | Stabilität | Runs | Cost |
|---|---|---|---|---|---|---|
| **desi** | 5/5 | 0 | 2/2 | 1.0 | 1 | negligible (no model call) |
| **naive_whole_text** | 0/5 | 0 | 2/2 | 0.0 | 1 | high in reality (1 LLM pass); stubbed here |

**Diskriminiert der Harness?** ja. Aber die Baseline (0/5) ist kein Befund — der Vergleich wird erst mit echten Reviewern aussagekräftig.

## Die eigentlich interessante Tabelle (zu füllen)

| Reviewer | Catch-Rate | False Positives | Cost | Varianz |
|---|---|---|---|---|
| Naive LLM | ? | ? | hoch | hoch |
| Claude Science | ? | ? | hoch | ? |
| Frontier-LLM (GPT/…) | ? | ? | hoch | ? |
| **DESi** | 5/5\* | 0\* | niedrig | 0 (deterministisch) |

\* per Konstruktion (Referenz). Kommt ein echter Reviewer nahe an 5/5 und DESi ebenfalls, ist die tragfähige Aussage **keine** 'A schlägt B', sondern: *vergleichbare epistemische Kontrolle bei deutlich geringerem, deterministischerem Compute* — eine Architektur-Effizienz-These, die die nächste Modellgeneration überdauert.

## Einen echten Reviewer einspeisen (mit Wiederholungen für Varianz)

Strukturierte Ausgabe eines echten Background-Reviewers als JSON ablegen:

```json
{
  "name": "some-background-reviewer",
  "runs": [
    {"P2-domain": ["source_domain_mismatch"], "P4-overclaim": ["overclaim"]},
    {"P2-domain": ["source_domain_mismatch"]}
  ],
  "profile": {"cost": "1 LLM pass / probe", "compute": "frontier api"}
}
```

`python -m desi.case_studies.marcognity_muse_spark.redteam --external out.json`. Mehrere `runs` → der Harness rechnet Stabilität; `profile` füllt Cost/Compute.

## Grenzen

- **Harness, kein Ergebnis** — 5 Failure-Probes + 2 Controls, ein Fall. Ein Startpunkt, keine erschöpfende Suite.
- Der DESi-Reviewer ist **Referenz** (5/5, 0 FP per Konstruktion), kein unabhängiger Prüfer.
- Der Befund entsteht erst, wenn der External-Slot mit ≥1 echten Reviewer gefüllt ist — vorher weiß man nur, dass die Testumgebung sauber ist.
