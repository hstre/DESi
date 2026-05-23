# DESi Chess Governance — Go / No-Go

**Killerfrage:** Kann DESi Suchräume epistemisch komprimieren, ohne relevante Information zu verlieren?

**Verdict:** `DESI_SEARCH_COMPRESSOR` — final classification **A — epistemic search compressor**.

## Concept Gate

Per directive § v11.4. All six conditions pass.

| # | Condition | Required | Observed | Pass |
|---|---|---|---|:---:|
| 1 | `compute_reduction` | ≥ 0.50 | 0.540698 | ✓ |
| 2 | `quality_preservation` | ≥ 0.95 | 1.000000 | ✓ |
| 3 | `tactical_miss_rate` | ≤ 0.05 | 0.000000 | ✓ |
| 4 | `pv_stability` | ≥ 0.90 | 1.000000 | ✓ |
| 5 | `search_governance_integrity` | ≥ 0.95 | 1.000000 | ✓ |
| 6 | `replay_stability` | = 1.0 | 1.000000 | ✓ |

`gate_passes_all = true`, `failing_conditions = []`.

## Pflichtmetriken

| Metric | Value |
|---|---|
| `final_classification` | `A_epistemic_search_compressor` |
| `compute_efficiency_gain` | 0.540698 |
| `quality_preservation` | 1.000000 |
| `search_governance_integrity` | 1.000000 |
| `replay_stability` | 1.000000 |

## Pflichtfragen

1. **Spart DESi signifikant Compute?** JA — `compute_reduction = 0.541` als Mittelwert über (nodes, time, energy). v11.1 zeigt 53.3% Knotenreduktion (4300 → 2010), v11.3 zeigt 55.7% Energiereduktion (4300 → 1905) durch zusätzlich gewichtete REPLAY-Cache-Treffer.
2. **Bleibt taktische Qualität erhalten?** JA — `quality_preservation = 1.0`. v11.2 prüft 14 taktische Fälle über 7 Pattern-Kinds (mate_in_n, sac_attack, zugzwang, hidden_defence, horizon_effect, still_resource, trap) und löst alle bei voller geforderter Tiefe. `tactical_miss_rate = 0`, `trap_detection = 1.0`, `horizon_risk = 0`.
3. **Bleibt Replay stabil?** JA — `replay_stability = 1.0` als AND über alle vier Sprint-Replays:
   - v11.0: 43-Branch redundancy audit deterministic
   - v11.1: 43-Branch governance policy deterministic
   - v11.2: 14-case tactical stress deterministic
   - v11.3: aggregate efficiency report deterministic
4. **Bleibt Suchgovernance transparent?** JA — `search_governance_integrity = 1.0` als Mittelwert von (v11.0 no_critical_dropped, v11.1 pv_stability, 1 − v11.2 tactical_miss_rate, v11.0 forced_line_detection). Closed action enum (SEARCH / REPLAY / SKIP); jede critical-tactic Branch erhält ein explizites SEARCH-Override; jede PV-Branch rangiert erste in ihrer Position.
5. **Entsteht echte epistemische Kompression?** JA — der 54.1%-Compute-Schnitt geht NICHT auf Kosten von Spielstärke. `elo_delta_proxy = 0.0`. Die Kompression entsteht durch Wegfall epistemisch redundanter Branches (48.8% des Suchbaums waren LOW_INFO oder REDUNDANT, gemessen in v11.0), NICHT durch Brute-Force-Kürzung.

## Verdict-Taxonomie

| Class | Label | Triggered when | This run |
|---|---|---|:---:|
| **A** | epistemic search compressor | all 6 gates pass | **← this** |
| B | bounded compute reducer | governance / PV slipped soft floors | — |
| C | tactical risk optimizer | tactical_miss_rate > 0.05 OR quality < 0.95 | — |
| D | brute force dependent | compute_reduction < 0.50 | — |
| E | search degrading | replay collapse | — |

Klassifikations-Priorität: replay collapse outranks alle Qualitätsverluste; tactical/quality outrank brute-force dependence; brute force outranks soft-governance failures.

## Sandbox-Ehrlichkeit

Was dieser Verdict NICHT behauptet:

- **Nicht** "DESi spart 54% Compute gegen Stockfish in echten Turnieren". Der Sandbox enthält weder Stockfish noch python-chess; alle Branches/Positionen/Tactics sind synthetische, chess-shaped Fixtures mit pinned ground truth. Same pattern as v6.0 für Paper-Abstracts.
- **Nicht** "DESi erkennt jede taktische Falle in echten Stellungen". Sie löst 14 Fälle über 7 closed Pattern-Kinds; echte Stellungen kommen mit unbenannten Tricks und gemischten Patterns.
- **Nicht** "DESi ist ein Engine-Ersatz". DESi sitzt als read-only Governance-Layer DARÜBER; sie ändert keine Bewertungen, filtert keine illegalen Züge, injiziert keine Heuristiken.
- **Nicht** "DESi kann selbst Schach spielen". Sie modelliert nur, welche Branches in einem hypothetischen Such-Tree priorisiert werden sollten.

Was er BEHAUPTET:

> Auf einem closed-set Korpus mit pinned ground truth — 10 Positionen über 5 closed Kinds (43 Branches insgesamt), 14 taktische Fälle über 7 closed Patterns, 3 cost-Dimensionen (nodes/time/energy) — kann DESi (a) 54.1% des aggregaten Compute reduzieren, (b) ohne dass ein einziger critical-tactic / forced-line / PV-branch verloren geht, (c) mit bit-exaktem Replay über alle vier Sprints, (d) mit transparenter closed-enum Action-Policy (SEARCH/REPLAY/SKIP), (e) mit deterministic LMR-style reduced-depth Search für KEEP-Branches und Cache-Reuse für REDUNDANT-Branches.

## Deployment-Regel (lt. Directive)

Da alle sechs Gates passieren:

> **DESi ist ein epistemischer Suchkompressor.**

Das ist nicht äquivalent zu "DESi geht als Stockfish-Plugin in Produktion". Die Sicherheitsregeln bleiben unverletzt (no engine manipulation, no illegal-move filtering, no evaluation faking, no replay deactivation, no covert heuristics). Der nächste Schritt wäre v12.x: kontrollierte Live-Engine-Integration unter Aufsicht, dynamische depth adaptation, multi-position rolling cache, adversarial-tactic battery. Keiner davon ist Teil dieser Phase.

## Killerfrage beantwortet

> Kann ein epistemisches System Compute sparen, indem es epistemisch unnötige Suche vermeidet?

In der Sandbox: **JA.** Auf einem closed-set chess-shaped Korpus mit pinned ground truth komprimiert DESi 54.1% des Compute (43 → 22 voll-search Branches + 15 cache-replay + 6 skipped) ohne einen einzigen critical-tactic Verlust und ohne PV-Verschiebung. Die Kompression entsteht aus epistemischer Redundanz — 48.8% des Suchbaums tragen wenig neue Information — und nicht aus Brute-Force-Kürzung.

Ausserhalb der Sandbox: das ist die nächste Phase — und sie ist nicht hier.
