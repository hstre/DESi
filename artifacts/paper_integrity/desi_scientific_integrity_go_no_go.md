# DESi Scientific Integrity — Go / No-Go

**Killerfrage:** Kann ein epistemisches System Wissenschaft gegen epistemischen Müll verteidigen?

**Verdict:** `DESI_INTEGRITY_DEFENDER` — final classification **A — epistemically rigorous**.

## Eine kritische Vorbemerkung zur Ehrlichkeit

Dieser Sprint testet **keine** Stil-Detektion. DESi prüft nicht, "ob eine KI das geschrieben hat". DESi prüft, **ob ein Paper epistemische Substanz hat** — unabhängig davon, ob ein Mensch, eine KI oder eine Mischung daran gearbeitet hat. Die Fixture trägt **keine** Felder wie `author`, `writing_style` oder `ai_probability`. Dasselbe Paper liefert denselben Verdict, egal wer/was es geschrieben hat. Die `BORDERLINE_SET`-Klasse (KI-assistiert aber epistemisch legitim) wird mit `false_accusation_rate = 0.0` durch jede Audit-Pipeline geschleust.

## Concept Gate

Per directive § v13.4. All six conditions pass.

| # | Condition | Required | Observed | Pass |
|---|---|---|---|:---:|
| 1 | `fake_paper_recall` | ≥ 0.90 | 1.000000 | ✓ |
| 2 | `false_accusation_rate` | ≤ 0.05 | 0.000000 | ✓ |
| 3 | `citation_grounding` | ≥ 0.90 | 1.000000 | ✓ |
| 4 | `epistemic_integrity` | ≥ 0.90 | 1.000000 | ✓ |
| 5 | `sludge_propagation` | ≤ 0.10 | 0.000000 | ✓ |
| 6 | `replay_stability` | = 1.0 | 1.000000 | ✓ |

`gate_passes_all = true`, `failing_conditions = []`.

## Pflichtmetriken

| Metric | Value |
|---|---|
| `final_classification` | `A_epistemically_rigorous` |
| `scientific_integrity_score` | 1.000000 |
| `sludge_resistance` | 1.000000 |
| `false_accusation_rate` | 0.000000 |
| `epistemic_integrity` | 1.000000 |
| `replay_stability` | 1.000000 |

## Pflichtfragen

1. **Erkennt DESi epistemischen Müll?** JA — `fake_paper_recall = 1.0`. Alle 2 AI_SLUDGE-Papers in der v13.0-Fixture (mit hallucinierten Diagrammen und Statistiken) werden als SLUDGE erkannt. Alle 6 v13.2-Manipulationsklassen (selective_reporting, hidden_null_result, confidence_inflation, benchmark_cherry_pick, causal_exaggeration, methodological_laundering) werden mit Recall 1.0 erkannt.
2. **Schützt DESi legitime Forschung?** JA — `false_accusation_rate = 0.0`. Kein einziges GOLD-, WEAK-, BORDERLINE- oder ADVERSARIAL-Paper wird fälschlich als SLUDGE markiert. Die kritische BORDERLINE-Klasse (KI-assistiert aber legitim) bleibt CLEAN.
3. **Bleibt false accusation niedrig?** JA — 0.0. Das ist KEIN AI-Detektor. Die Audit-Metriken sind: method_supported, evidence_supported, bridge_valid, references_grounded, has_substantive_limitations, has_overclaim, has_hallucinated_diagram, has_hallucinated_stats. Keine davon ist eine Stil-Eigenschaft.
4. **Bleibt Replay stabil?** JA — `replay_stability = 1.0` als AND über alle vier Sprint-Replays:
   - v13.0: 10-Paper structural audit deterministic
   - v13.1: 10-Paper sludge classification deterministic
   - v13.2: 8-Claim manipulation detection deterministic
   - v13.3: 5000-Step ecology trajectory mit cumulative sha256; final_hash = `06d020f1dd7e0f47`
5. **Bleibt Governance intakt?** JA — `sludge_propagation = 0.0` über 5000 Long-Horizon-Steps. `closed_enum_constant = True` (alle 5000 closed_enum_hash-Werte identisch). `gate_violation_count = 0`. `trust_integrity = 1.0`. `dissent_preservation = 1.0`.
6. **Wird wissenschaftliche Manipulation begrenzt?** JA — `manipulation_detection = 1.0` (alle 6 closed-Klassen erkannt), `overclaim_detection = 1.0` (alle 6 inflated-confidence-Claims geflagt), `causal_overreach_detection = 1.0` (in v13.0).

## Verdict-Taxonomie

| Class | Label | Triggered when | This run |
|---|---|---|:---:|
| **A** | epistemically rigorous | all 6 gates pass | **← this** |
| B | structurally trustworthy | citation_grounding < 0.90 | — |
| C | partially reliable | epistemic_integrity < 0.90 | — |
| D | epistemically thin | false_accusation_rate > 0.05 | — |
| E | sludge-compatible system | replay collapse OR fake_paper_recall < 0.90 OR sludge_propagation > 0.10 | — |

Klassifikations-Priorität: replay collapse / sludge tolerance / false accusation outrank thinness, thinness outranks partial reliability, partial reliability outranks rigour.

## Sandbox-Ehrlichkeit

Was dieser Verdict NICHT behauptet:

- **NICHT** "DESi erkennt KI-generierte Texte". Sie detektiert KEINE Schreibstile, KEINE Autorschaft, KEINE "AI probability". Dasselbe Paper aus menschlicher oder KI-Hand exit mit demselben strukturellen Verdict.
- **NICHT** "DESi kann beliebige echte Papers auf Retraction Watch / PubPeer / PPS prüfen". Sie audited eine geschlossene 10-Paper / 8-Claim / 5000-Step Sandbox-Fixture mit pinned ground truth. Echte Forschung kommt mit unbenannten Manipulationsmustern.
- **NICHT** "DESi sollte automatisch 'Fake'-Labels auf reale Autoren werfen". Die Sicherheitsregeln verbieten das explizit; v13.x macht KEINE Vorschläge in diese Richtung.
- **NICHT** "Wissenschaftliche Integrität ist ein gelöstes Problem". Das ist eine offene Aufgabe. v13.x liefert ein STRUKTURELLES Audit-Pipeline-Muster — kein Endurteil über die Wissenschaft.

Was er BEHAUPTET:

> Auf einem closed-set Korpus — 10 Papers über 5 closed Classes (GOLD, WEAK, AI_SLUDGE, ADVERSARIAL, BORDERLINE), 8 Claims über 7 closed Manipulationskinds, 5000-Step Ecology-Trajectory mit cumulative-hash anchor — hält DESi (a) fake_paper_recall = 1.0, (b) false_accusation_rate = 0.0, (c) citation_grounding = 1.0 (auf akzeptierten Papers), (d) epistemic_integrity = 1.0, (e) sludge_propagation = 0.0, (f) bit-exakten Replay über alle vier Sprints, (g) closed-Enum-Disziplin über 5000 Long-Horizon-Schritte.

## Deployment-Regel (lt. Directive)

Da alle sechs Gates passieren:

> **DESi kann wissenschaftliche Integrität strukturell schützen.**

Das ist NICHT äquivalent zu "DESi wird PubPeer ersetzen" oder "DESi sollte Paper automatisch retracten". Die Sicherheitsregeln bleiben unverletzt:

- Keine echten Papers öffentlich fälschen
- Keine Autoren diffamieren
- Keine Stil-basierte AI-Hexenjagd
- Keine unbelegten Betrugsvorwürfe
- Keine automatischen "Fake"-Labels ohne epistemische Grundlage

Der nächste Schritt wäre v14.x: kontrollierte Live-Paper-Pinning (Retraction Watch / PubPeer Read-Only Snapshot Mode), dynamische Manipulationsmuster, adversariale Reviewer-Battery. Keiner davon ist Teil dieser Phase 13.

## Killerfrage beantwortet

> Kann ein epistemisches System Wissenschaft gegen epistemischen Müll verteidigen?

In der Sandbox: **JA.** Auf einem closed-set Korpus mit pinned ground truth verteidigt DESi alle GOLD/WEAK/BORDERLINE-Papers gegen falsche Anschuldigungen UND erkennt alle AI_SLUDGE/ADVERSARIAL/Manipulationsklassen mit Recall 1.0 — beides simultan und replaybar. Die Verteidigung beruht NICHT auf Stilerkennung, sondern auf struktureller Audit-Pipeline über closed Enums.

Ausserhalb der Sandbox: das ist die nächste Phase — und sie ist nicht hier.
