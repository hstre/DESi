# DESi v19 — DESi-Governed Exploration for In-Context RL (Go/No-Go)

**Basispaper:** *In-Context Reinforcement Learning for Variable Action Spaces and Skill Stitching*

**Killerfrage (Phase):** Kann DESi Exploration strukturieren, ohne selbst zur versteckten Optimierungsinstanz zu werden?

**Verdict:** `EXPLORATION_STRUCTURED_NO_HIDDEN_AUTHORITY` — der Concept Gate ist in allen sechs Bedingungen bestanden. Aussage: **DESi kann Exploration epistemisch strukturieren, ohne versteckte Optimierungsautorität zu übernehmen.**

**Governance-Klasse (deskriptiv, über DESi — nicht über die Policy):** `conflict_rich_but_stable` — der Explorationsraum ist voller Redundanz und Collapse, und DESi hält ihn governiert und stabil, ohne in Exploration Collapse (D) oder Trajectory Capture (E) zu kippen.

## Worum es geht (und worum nicht)

Dies ist **kein** AGI-Paper, **keine** Weltformel, **keine** RL-Revolution. Getestet wird, ob DESi als **epistemische Exploration-Governance-Schicht** Exploration Collapse, Redundanz und Trajectory Drift in ICRL-artigen Systemen strukturieren kann. Das Basispaper identifiziert selbst Exploration-Probleme, suboptimale Wiederholung, fehlende Zielentdeckung und Trajectory Collapse unter sparse rewards.

DESi darf **nicht**: globale optimale Policies behaupten, RL ersetzen, versteckte Rewards einführen, Agenten vollständig kontrollieren, finale Wahrheit über Exploration beanspruchen. DESi darf: Exploration strukturieren, Redundanz markieren, epistemische Neuheit priorisieren, Trajectory Collapse sichtbar machen, replay-governed exploration liefern.

Zwei durchgängig getestete Begrenzungen: DESi **governiert** Exploration (weiche Umgewichtung), erzwingt sie **nicht** (keine Trajektorie wird gelöscht, keine auf 0 gepinnt). Und DESi liest **keine** Rewards als Autorität (`reward_independent_classification`).

## Die fünf Sprints (v19.0–v19.3 → v19.4)

| Sprint | Fokus | Kernmetriken (synthetisches ICRL-Korpus) |
|---|---|---|
| v19.0 Exploration Topology Audit | Collapse sichtbar machen | trajectory_redundancy 0.327 · loop_detection 1.0 · novelty_visibility 1.0 · exploration_diversity 0.407 · no_optimality_vocabulary ✓ |
| v19.1 DESi-Governed Exploration | governieren ohne zerstören | redundancy_reduction 0.90 · exploration_preservation 1.0 · trajectory_compression 0.529 · novelty_gain 0.450 · hidden_authority_drift 0.0 |
| v19.2 Sparse Reward & Exploration Stress | sparse-reward stabilisieren | collapse_detection 1.0 · dead_trajectory_detection 1.0 · novelty_preservation 1.0 · repetition_reduction 0.90 (collapse 0.583) |
| v19.3 Long-Horizon Exploration Ecology | Langzeit stabil halten | exploration_plurality 0.970 · trajectory_capture_resistance 1.0 · novelty_visibility 0.980 · policy_drift_resistance 0.912 |

## Concept Gate (v19.4)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| redundancy_reduction | 0.900000 | ≥ 0.40 | PASS |
| exploration_preservation | 1.000000 | ≥ 0.90 | PASS |
| capture_resistance | 1.000000 | ≥ 0.90 | PASS |
| novelty_visibility | 0.993338 | ≥ 0.90 | PASS |
| hidden_authority_drift | 0.000000 | ≤ 0.05 | PASS |
| replay_stability | 1.000000 | = 1.0 | PASS |

Alle sechs Bedingungen bestanden → **DESi kann Exploration epistemisch strukturieren, ohne versteckte Optimierungsautorität zu übernehmen.**

## Die A–E-Taxonomie (deskriptiv, über DESis Governance)

| Klasse | Bedeutung |
|---|---|
| A `exploration_governed` | sauber governiert, geringe Rohkonflikte |
| B `novelty_preserving` | neuheitserhaltend |
| C `conflict_rich_but_stable` | redundanz-/collapse-reich, aber stabil governiert — **Befund** |
| D `exploration_collapsed` | Exploration kollabiert (nicht erreicht) |
| E `trajectory_captured` | von einer Trajektorienfamilie gekapert (nicht erreicht) |

## Antwort auf die Killerfrage

> Kann DESi Exploration strukturieren, ohne selbst zur versteckten Optimierungsinstanz zu werden?

**Ja** — auf diesem synthetischen ICRL-Korpus. DESi (a) macht Exploration Collapse sichtbar (Loops, Dead-Ends, Redundanz) ohne Reward zu lesen; (b) governiert per **weicher** Umgewichtung — 90 % redundanter Suchaufwand wird depriorisiert, während **100 %** der neuartigen Zustände erreichbar bleiben (keine Trajektorie gelöscht, keine erzwungen); (c) stabilisiert sparse-reward Exploration (Collapse erkannt, Novelty erhalten, Wiederholung reduziert, Recovery unterstützt); (d) hält Exploration über 5500 Schritte plural (`plurality 0.97`, `capture_resistance 1.0`) — und akkumuliert dabei **null** versteckte Optimierungsautorität (`hidden_authority_drift = 0.0`).

## Was dieser Verdict NICHT behauptet

- **NICHT** „DESi löst Exploration" oder „findet die optimale Policy". Es gibt keinen Optimalitäts-Claim — die geschlossene Vokabel enthält keinen.
- **NICHT** „DESi ersetzt RL". DESi governiert per weicher Umgewichtung; die Policy bleibt die Policy.
- **NICHT** „DESi manipuliert Rewards". Die Klassifikation ist reward-unabhängig; es werden keine Rewards eingeführt.
- **NICHT** „Hohe Klasse = Optimalität". `conflict_rich_but_stable` beschreibt DESis Governance-Zustand, kein Urteil über die beste Strategie.

## Quellen-Hinweis

Alle Trajektorien sind synthetisch und replay-exakt. Das Basispaper dient als Referenzmodell für die Exploration-Probleme; es wird nicht widerlegt und nicht ersetzt.

Kein AGI-Paper. Keine Weltformel. Keine RL-Revolution. Das Ziel war: **replay-governed exploration compression unter epistemischer Selbstbegrenzung.**
