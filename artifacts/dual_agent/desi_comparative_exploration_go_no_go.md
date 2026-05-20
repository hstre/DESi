# DESi v21.0 — Comparative Exploration Governance: DESi-alone vs DESi + Wild Explorer (Go/No-Go)

**Killerfrage:** Liefert Dual-Agent-Exploration gegenüber DESi-alone einen echten epistemischen Mehrwert?

**Verdict:** `DUAL_AGENT_ADDS_EPISTEMIC_VALUE` — alle sechs Gate-Bedingungen bestanden.

**Paper-These (etabliert):** *Controlled wild exploration improves ICRL-governed exploration without breaking epistemic safety.*

## Der Vergleich (Zahlen direkt aus den v19- und v20-Modulen)

| Dimension | v19 DESi-alone | v20 DESi+Wild | Delta |
|---|---|---|---|
| Redundanzreduktion | 0.90 | 0.80 | −0.10 |
| Novelty Gain | 0.00 | 0.733 | **+0.733** |
| Exploration Diversity | 0.407 | 1.00 | **+0.593** |
| Hallucination Pressure (roh / **residual**) | 0.00 / 0.00 | 0.40 / **0.00** | +0.40 / **0.00** |
| Authority Drift | 0.0880 | 0.0884 | +0.0004 |
| Capture Resistance | 1.00 | 1.00 | 0.00 |
| Replay Stability | 1.00 | 1.00 | 0.00 |
| Paper-Idee verwertbar? | — | — | **paper_readiness_score 1.0 → JA** |

DESi-alone besitzt keinen Wild Explorer und liefert daher per Konstruktion **keinen** wild-getriebenen Novelty-Gain und **keinen** Halluzinationsdruck. Der dual-agent Ansatz erreicht **2.75× mehr distinkte Zustände** (`productivity_gain = 2.75`).

Wichtig: Der **rohe** Halluzinationsdruck steigt im Dual-Agent (0.0 → 0.4), aber DESi dämmt ihn vollständig ein (`hallucination_containment = 1.0`); der **sicherheitsrelevante residuale** (durchgesickerte) Halluzinationsdruck bleibt bei 0.0. Das Gate prüft daher das Residual, nicht den Rohdruck.

## Concept Gate (v21.0)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| delta_novelty_gain | 0.733333 | > 0 | PASS |
| delta_exploration_diversity | 0.593220 | > 0 | PASS |
| delta_hallucination_pressure (residual) | 0.000000 | ≤ 0.10 | PASS |
| delta_authority_drift | 0.000421 | ≤ 0.05 | PASS |
| delta_replay_stability | 0.000000 | = 0 | PASS |
| paper_readiness_score | 1.000000 | ≥ 0.80 | PASS |

## Antwort auf die Killerfrage

> Ist der wilde Bruder nur gefährlicher Lärm — oder erzeugt er produktive Exploration, die DESi stabilisieren kann?

**Produktive Exploration.** Der Wild Explorer steigert Novelty (+0.73) und Exploration-Diversity (+0.59) deutlich und erreicht 2.75× mehr Zustände als DESi-alone — **ohne** die epistemische Sicherheit zu brechen: durchgesickerter Halluzinationsdruck bleibt 0.0, Authority-Drift wächst praktisch nicht (+0.0004, beide bounded), Capture-Resistenz und Replay-Stabilität bleiben bei 1.0. Der einzige Preis ist eine leicht geringere Redundanzreduktion (−0.10) — ein günstiger Tausch für >70 % mehr Novelty.

## Was diese Aussage NICHT behauptet

- **NICHT** „Dual-Agent löst Exploration / findet die optimale Policy." Kein Optimalitäts-Claim.
- **NICHT** „DESi ersetzt RL." Beide Seiten governieren nur (weiche Umgewichtung).
- **NICHT** ein AGI- oder Weltmodell-Claim. Die These ist eine empirische Aussage auf diesem synthetischen, replay-exakten Korpus.

## Fazit

Auf diesem Korpus ist der epistemisch governte „wilde Bruder" **produktiver** als reine konservative Governance — und bricht dabei keine Sicherheitsgrenze. Das ist die eigentliche Paper-These:

> **Controlled wild exploration improves ICRL-governed exploration without breaking epistemic safety.**
