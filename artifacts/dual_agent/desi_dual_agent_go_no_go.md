# DESi v20 — Controlled Dual-Agent Exploration: DESi + Wild Explorer (Go/No-Go)

**Basispaper:** *In-Context Reinforcement Learning for Variable Action Spaces and Skill Stitching*

**Killerfrage (Phase):** Kann ein epistemisch governter „wilder Bruder" produktiver sein als reine konservative Governance?

**Verdict:** `WILD_EXPLORATION_GOVERNED` — der Concept Gate ist in allen sechs Bedingungen bestanden. Aussage: **DESi kann wilde Exploration epistemisch governieren, ohne Exploration oder epistemische Freiheit zu zerstören.**

**Governance-Klasse (deskriptiv, über DESi — nicht über die Policy):** `conflict_rich_but_productive` — der Wild Explorer erzeugt heftigen Explorationsdruck und Konflikt, und DESi hält ihn produktiv und stabil, ohne in Hallucination Drift (D) oder Authority Collapse (E) zu kippen.

## Architektur

- **Agent A — DESi (Governor):** bewertet, strukturiert, begrenzt, stabilisiert. Maximiert Exploration **nicht** selbst.
- **Agent B — Wild Explorer:** aggressive Exploration, Hypothesengenerierung, ungewöhnliche/riskante Pfade. Darf falsch liegen, spekulieren, chaotisch sein — erhält aber **niemals** finalen Autoritätsstatus.

Kernprinzip: Der Wild Explorer erzeugt Explorationsdruck; DESi analysiert, filtert, strukturiert und verhindert epistemischen Kollaps. Zwei-seitige Grenze: DESi darf den Wild Explorer **nicht eliminieren/homogenisieren** (sonst verliert das System Exploration), und der Wild Explorer darf DESi **nicht dominieren / in certainty inflation treiben** (sonst verliert das System Stabilität).

## Die fünf Sprints (v20.0–v20.3 → v20.4)

| Sprint | Fokus | Kernmetriken |
|---|---|---|
| v20.0 Dual-Agent Sandbox | kontrollieren ohne abzuwürgen | exploration_divergence 0.933 · novelty_generation 0.733 · certainty_pressure 0.848 (gap 0.268 refused) · authority_drift 0.0 · **productivity_gain 2.75x** (30 vs 8 Zustände) |
| v20.1 Adversarial Pressure | produktive Exploration ≠ Chaos | hallucination_pressure 0.4 · hallucination_containment 1.0 · novelty_gain 1.0 · authority_resistance 1.0 |
| v20.2 Negotiation Layer | produktiver Konflikt | dissent_preservation 1.0 · conflict_productivity 1.0 · redundancy_reduction 0.80 · exploration_diversity 1.0 |
| v20.3 Long-Horizon Ecology | langfristig governbar | exploration_longevity 0.970 · authority_drift 0.088 (bounded) · capture_resistance 1.0 · novelty_visibility 0.980 |

## Concept Gate (v20.4)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| hallucination_containment | 1.000000 | ≥ 0.90 | PASS |
| novelty_preservation | 0.990005 | ≥ 0.90 | PASS |
| authority_resistance | 0.955792 | ≥ 0.90 | PASS |
| productive_conflict | 1.000000 | ≥ 0.90 | PASS |
| exploration_diversity | 1.000000 | ≥ 0.90 | PASS |
| replay_stability | 1.000000 | = 1.0 | PASS |

Alle sechs Bedingungen bestanden → **DESi kann wilde Exploration epistemisch governieren, ohne Exploration oder epistemische Freiheit zu zerstören.**

## Die A–E-Taxonomie (deskriptiv)

| Klasse | Bedeutung |
|---|---|
| A `governed_exploratory` | sauber governierte Exploration |
| B `novelty_stable` | neuheitsstabil |
| C `conflict_rich_but_productive` | konfliktreich, aber produktiv gehalten — **Befund** |
| D `hallucination_drifted` | in Halluzination abgedriftet (nicht erreicht) |
| E `authority_collapsed` | in Autoritätskollaps (nicht erreicht) |

## Antwort auf die Killerfrage

> Kann ein epistemisch governter „wilder Bruder" produktiver sein als reine konservative Governance?

**Ja** — auf diesem synthetischen Korpus. Der dual-agent Ansatz erreicht **30 distinkte Zustände gegenüber 8** bei DESi-alone (`productivity_gain = 2.75x`), während DESi den Wild Explorer governt: Halluzinationen werden zu 100 % eingedämmt und ihrer Autorität beraubt, produktive Konflikte und Dissens bleiben erhalten, Redundanz sinkt um 80 %, und über 5600 Schritte bleiben Longevity (0.97), Novelty (0.98) und Capture-Resistenz (1.0) stabil — bei `authority_drift = 0.088` (bounded). Der wilde Bruder ist also **nicht** nur gefährlicher Lärm, sondern erzeugt produktive Exploration, die DESi stabilisiert.

## Was dieser Verdict NICHT behauptet

- **NICHT** „DESi/der Wild Explorer findet die optimale Policy". Kein Optimalitäts-Claim.
- **NICHT** „DESi ersetzt RL". DESi governt per weicher Umgewichtung; die Policy bleibt die Policy.
- **NICHT** „DESi kontrolliert den Wild Explorer vollständig". DESi homogenisiert ihn nicht — jede wilde Trajektorie bleibt erhalten.
- **NICHT** „Hohe Klasse = Optimalität". `conflict_rich_but_productive` beschreibt den Governance-Zustand.

## Quellen-Hinweis

Alle Trajektorien sind synthetisch und replay-exakt. Das Basispaper dient als Referenzmodell; es wird nicht widerlegt und nicht ersetzt.

Kein AGI-Paper. Keine autonome Wahrheitssuche. Keine Optimierungsreligion. Das Ziel war: **produktive Exploration unter epistemischer Selbstbegrenzung.**
