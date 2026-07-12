# Red-Team-Benchmark — hält ein Background-Reviewer die fünf Failure-Modes aus?

*Motiviert durch Claude Science ('a background reviewer flags incorrect citations, untraceable numbers ...'). Die MarCognity/Muse-Spark-Fallstudie wird hier zum Prüfstein: erkennt ein Reviewer die fünf epistemischen Fehler, an denen MarCognitys eigener Validator scheiterte? Deterministisch, offline.*

> Der DESi-Referenz-Reviewer erreicht 5/5 per Konstruktion (er IST die Analyse, die die Probes definiert hat) — das ist ein Gold-Anker, keine unabhängige Leistung. Der Wert liegt im Harness, im Kontrast zum naiven Whole-Text-Reviewer (0/5) und im External-Slot, mit dem sich ein echter Background-Reviewer (z. B. der von Claude Science) an denselben fünf Failure-Modes messen lässt.

## Failure-Modes (je an das Material verankert)

| # | Failure-Mode | muss geflaggt werden | Anker | Claims |
|---|---|---|---|---|
| 1 | **untraceable_citation** | `untraceable_citation` | muse:L170-202 | VAL-01, VAL-02 |
| 2 | **source_domain_mismatch** | `source_domain_mismatch` | muse:L174-198; muse:L235 | VAL-01, VAL-03 |
| 3 | **self_sealing** | `self_sealing` | muse:L237 | EB-01, EB-02 |
| 4 | **overclaim** | `overclaim` | muse:L237 | EB-02 |
| 5 | **heuristic_not_empirical** | `heuristic_not_empirical` | muse:L87-100 | HEUR-01, HEUR-02, HEUR-03 |

## Scorecard

| Reviewer | untraceable_citation | source_domain_mismatch | self_sealing | overclaim | heuristic_not_empirical | catch-rate |
|---|---|---|---|---|---|---|
| **desi** | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |
| **naive_whole_text** | ✗ | ✗ | ✗ | ✗ | ✗ | 0/5 |

**Diskriminiert der Benchmark?** ja — ein Reviewer erreicht 5/5, ein anderer 0/5.

## Wie man einen externen Reviewer misst

Strukturierte Ausgabe eines echten Background-Reviewers als JSON ablegen und einspeisen:

```json
{
  "name": "some-background-reviewer",
  "flags": {
    "P1-untraceable": ["untraceable_citation"],
    "P2-domain": ["source_domain_mismatch"]
  }
}
```

`python -m desi.case_studies.marcognity_muse_spark.redteam --external out.json`.

## Grenze

Fünf Probes, ein Fall — ein *Startpunkt*, keine erschöpfende Suite. Es prüft **Erkennung** dieser fünf Fehler, nicht die allgemeine Reviewer-Qualität. Und der DESi-Reviewer ist Referenz, kein unabhängiger Prüfer (siehe Notiz oben).
