# Generalization suite evaluation — baseline_adv_n10

Same evaluator (`evaluate_suite.py`) run against the original n=10
adversarial suite at DESi cycle-12 head (`5807547`). Included so the
generalization-loop deltas have a cross-suite reference: if a cycle
improves the n=20 suite but degrades the n=10 suite, that's a regression
worth flagging.

n_fixtures: **10**
phase overlaps (any pair): **3**
malformed phase spans: **0**
missed expected detector hits (sum across fixtures): **0**
spurious detector hits (sum across fixtures): **17**

## Detector fire counts

| Detector | Fires |
|---|---:|
| `any_genuine_transformation_confirmed` | 5 |
| `attractor_lock` | 9 |
| `branch_explosion` | 1 |
| `mild_stagnation` | 1 |
| `penultimate_en_candidate` | 1 |

## Per-fixture summary (phase spans + key labels)

| Fixture | Phases | Overlaps |
|---|---|---|
| adv01_no_recovery_despite_high_en | I:0-0; II:1-1; V:3-5 | - |
| adv02_recovery_below_threshold | I:0-0; II:1-2 | - |
| adv03_phase_iv_without_two_consecutive_low_en | I:0-0; II:1-2; V:2-5 | II∩V |
| adv04_terminal_convergence_without_dup_spike | I:0-0; II:2-2 | - |
| adv05_oscillating_novelty | I:0-0; III:2-2 | - |
| adv06_false_penultimate_candidate | I:0-0; II:1-3; III:2-2; V:4-6 | II∩III |
| adv07_branch_explosion_no_attractor | I:0-0; V:5-5 | - |
| adv08_monotonic_decline_only | I:0-0; II:4-4; V:5-6 | - |
| adv09_late_recovery_after_apparent_lock | I:0-0; II:2-2; III:6-8; IV:2-4; V:2-5 | II∩IV; II∩V; IV∩V |
| adv10_random_walk | I:0-0; III:3-5; V:6-7 | - |

## Key cross-suite observations

1. **3 phase overlaps already present in the n=10 suite at cycle-12 head.** This
   is a pre-existing condition, NOT a generalization-loop regression. The 11
   prior cycles never targeted overlap-elimination.
2. **`attractor_lock` fires on 9/10 of the original suite** as well. The
   over-permissive attractor detector is a baseline issue across both suites.
3. **`adv09` shows the most chaotic overlap pattern (3 pairs)** — III, IV, V
   all overlap with each other. This was the original "late recovery after
   apparent lock" fixture and it survived all 11 cycles in this shape.
