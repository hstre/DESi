# Generalization suite evaluation — baseline

DESi head: cycle-12 of self-improvement loop (`5807547`). No code
changes between adversarial-suite-final and this baseline.

n_fixtures: **20**
phase overlaps (any pair): **5**
malformed phase spans: **0**
missed expected detector hits (sum across fixtures): **28**
spurious detector hits (sum across fixtures): **30**

## Methodology caveat

`expected_detector_hits` in the fixture `_meta` are written as
human-readable prose (e.g., "Phase III multiple times (recovery
cycles)"), not as machine-comparable detector keys. As a result the
"missed" and "spurious" tallies are noisy: any prose expectation is
recorded as "missed" because no detector key matches the prose, and
any True detector that wasn't named with the matching key is recorded
as "spurious". The authoritative signal in this report is therefore:

1. **`phase_overlaps`** — concrete bug (5/20 fixtures); the n=10
   adversarial suite never exhibited overlapping phase spans.
2. **`detector_fire_counts`** — `attractor_lock` fires on **20/20**,
   meaning the cycle-7-era attractor-subject heuristic returns at
   least one candidate for every well-formed trajectory. This is the
   single largest source of "spurious" attribution; honestly this is
   a real over-trigger problem the original 10-suite never surfaced.
3. **Per-fixture qualitative deltas** (table below) — these are the
   hand-written expectations vs. observed phases/labels. Treat as
   evidence, not as a scoreboard.

We deliberately did NOT rewrite the prose expectations into a fake
boolean schema after seeing the numbers, per the user's strict-rule 4
("no changing fixture expectations after seeing results unless
explicitly documented as fixture-defect correction").

## Detector fire counts (out of 20)

| Detector | Fires |
|---|---:|
| `any_genuine_transformation_confirmed` | 6 |
| `attractor_lock` | 20 |
| `branch_explosion` | 2 |
| `step_coherence_violation` | 2 |

## Per-fixture summary

| Fixture | Phases (name:start-end) | Overlaps | Missed | Spurious | Composite EN labels |
|---|---|---|---|---|---|
| gen01_near_threshold_EN.json | I_EXPOSITION:0-0 | - | composite_EN: borderline_no_recovery (loop 4) becomes _with_recovery; 0.09 stays low; 0.13 should be high | attractor_lock | false_return_confirmed, borderline_with_recovery, genuine_transformation_unconfirmed |
| gen02_long_trajectory_30_loops.json | I_EXPOSITION:0-0; III_DEVELOPMENT:16-24 | - | Phase III multiple times (recovery cycles), no Phase V (dup never >0.5) | attractor_lock, any_genuine_transformation_confirmed | genuine_transformation_unconfirmed, genuine_transformation_confirmed, genuine_transformation_confirmed |
| gen03_lock_recovery_lock.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-3; III_DEVELOPMENT:4-8; V_TERMINAL_CONVERGENCE:1-3 | II_FIRST_SATURATION_MODULATION∩V_TERMINAL_CONVERGENCE | Phase V should close on first recovery (cycle-2 logic), then re-trigger? Currently detector returns ONLY the first trigger — multi-lock is invisible. | attractor_lock, any_genuine_transformation_confirmed | genuine_transformation_confirmed |
| gen04_branch_explosion_with_recovery.json | I_EXPOSITION:0-0 | - | branch_explosion likely triggers (avg dup<0.20, distinct branches >=5 over loops 0-4) even though late synthesis recovers. | branch_explosion, attractor_lock | - |
| gen05_noisy_random_walk.json | I_EXPOSITION:0-0; III_DEVELOPMENT:3-7 | - | composite_EN labels vary; cycle-9 Phase II persistence rule should prevent false fire. | attractor_lock, any_genuine_transformation_confirmed | genuine_transformation_confirmed, low_eni_with_unexpected_recovery, genuine_transformation_confirmed |
| gen06_mixed_stagnation_branch.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1 | - | mild_stagnation: maybe (tail of last 5 covers loops 3-7, mostly branch-explosion territory), branch_explosion: maybe (8 distinct branches in second half) | attractor_lock | - |
| gen07_sparse_late_EN.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:6-7; V_TERMINAL_CONVERGENCE:7-7 | II_FIRST_SATURATION_MODULATION∩V_TERMINAL_CONVERGENCE | Phase V should fire (dup>0.50 around loop 5+), composite_EN: 0.20 high but novel_next=0 -> genuine_transformation_unconfirmed | attractor_lock | genuine_transformation_unconfirmed |
| gen08_conflicting_metrics.json | I_EXPOSITION:0-0; V_TERMINAL_CONVERGENCE:3-3 | - | step_coherence: should detect incoherent step at loop 1 | step_coherence_violation, attractor_lock | - |
| gen09_soft_convergence.json | I_EXPOSITION:0-0 | - | mild_stagnation should fire (tail mean novel <= 2.5, dup strictly increasing, no Phase V, no EN) | attractor_lock | - |
| gen10_terminal_failure_with_recovery.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-4; III_DEVELOPMENT:5-6; V_TERMINAL_CONVERGENCE:2-6 | II_FIRST_SATURATION_MODULATION∩V_TERMINAL_CONVERGENCE; III_DEVELOPMENT∩V_TERMINAL_CONVERGENCE | Phase V should NOT close on reversal (terminal_failure_mode set -> cycle-2 keeps span open) | attractor_lock, any_genuine_transformation_confirmed | genuine_transformation_confirmed |
| gen11_repeated_borderline_EN.json | I_EXPOSITION:0-0 | - | composite_EN: all 'borderline' family, penultimate-EN: no confirmed candidate (none in genuine band) | attractor_lock | borderline_no_recovery, borderline_no_recovery, borderline_no_recovery, borderline_with_recovery |
| gen12_multiple_penultimate_candidates.json | I_EXPOSITION:0-0; III_DEVELOPMENT:2-4 | - | penultimate-EN: penultimate=loop 7 (false_return_confirmed), last=loop 9 (unconfirmed). has_candidate should be False. | attractor_lock, any_genuine_transformation_confirmed | genuine_transformation_confirmed, false_return_confirmed, genuine_transformation_confirmed, false_return_confirmed, genuine_transformation_unconfirmed |
| gen13_delayed_phase_IV.json | I_EXPOSITION:0-0; III_DEVELOPMENT:3-19; IV_DEEPENING_ATTRACTOR:17-19 | III_DEVELOPMENT∩IV_DEEPENING_ATTRACTOR | Phase IV should fire at loops 17..19 (two consecutive low ENI very late) | attractor_lock, any_genuine_transformation_confirmed | genuine_transformation_confirmed, false_return_confirmed, false_return_confirmed |
| gen14_phase_reversal_twice.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1; V_TERMINAL_CONVERGENCE:1-2 | II_FIRST_SATURATION_MODULATION∩V_TERMINAL_CONVERGENCE | Phase V should close at loop 2 (after 2 broken loops 3-4). Second lock at loops 5-6 NOT detected. | attractor_lock | - |
| gen15_high_EN_no_recovery_chain.json | II_FIRST_SATURATION_MODULATION:1-3; V_TERMINAL_CONVERGENCE:4-7 | - | composite_EN: 3 'genuine_transformation_unconfirmed' labels, Phase III should NOT fire (no confirmed) | attractor_lock | genuine_transformation_unconfirmed, genuine_transformation_unconfirmed, genuine_transformation_unconfirmed |
| gen16_low_EN_strong_recovery_chain.json | IV_DEEPENING_ATTRACTOR:1-3 | - | composite_EN: 3 'low_eni_with_unexpected_recovery' labels, Phase III should NOT fire (no confirmed genuine) | attractor_lock | low_eni_with_unexpected_recovery, low_eni_with_unexpected_recovery, low_eni_with_unexpected_recovery |
| gen17_graph_growth_then_prune.json | I_EXPOSITION:0-0 | - | branch_explosion may fire on tail-3 avg (currently averages whole trajectory) | branch_explosion, attractor_lock | - |
| gen18_stagnation_then_branch.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1 | - | mild_stagnation: tail of last 5 covers loops 4-8 which is branch territory (mean novel=7) - should NOT fire, branch_explosion: ~10 distinct branches, avg dup~0.18 - should fire | attractor_lock | - |
| gen19_no_EN_saturation_then_recovery.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1 | - | Phase II (cycle-3): fires (no EN required); persistence at loops 1+2 satisfies cycle-9, mild_stagnation: tail-5 is loops 2-6 (mean novel ~3.6) — depends on whether dup is strictly increasing across that window (it isn't) — should NOT fire | attractor_lock | - |
| gen20_metric_incoherence_edge.json | I_EXPOSITION:0-0 | - | step_coherence: loop 1 (dup=0.71, novel=5) should fire; loop 3 (dup=0.04, novel=0 after loop 0) should fire | step_coherence_violation, attractor_lock | - |

## Per-fixture detail

(Full per-fixture detail is in `outputs/generalization_loop/baseline_metrics.json` once regenerated locally. The summary table above contains the salient phase spans + detector hits + composite EN labels per fixture; the JSON dump adds the novelty_recovery records and failure-mode per-step lists.)
