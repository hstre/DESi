# Generalization suite evaluation — cycle_3_adv

n_fixtures: **10**
phase overlaps (any pair): **0**
malformed phase spans: **0**
missed expected detector hits (sum across fixtures): **0**
spurious detector hits (sum across fixtures): **13**

## Detector fire counts (out of 20)

| Detector | Fires |
|---|---:|
| `any_genuine_transformation_confirmed` | 5 |
| `attractor_lock` | 5 |
| `branch_explosion` | 1 |
| `mild_stagnation` | 1 |
| `penultimate_en_candidate` | 1 |

## Per-fixture summary

| Fixture | Phases (name:start-end) | Overlaps | Missed | Spurious | Composite EN labels |
|---|---|---|---|---|---|
| adv01_no_recovery_despite_high_en.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1; V_TERMINAL_CONVERGENCE:3-5 | - | - | attractor_lock | genuine_transformation_unconfirmed |
| adv02_recovery_below_threshold.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-2 | - | - | - | borderline_with_recovery |
| adv03_phase_iv_without_two_consecutive_low_en.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1; V_TERMINAL_CONVERGENCE:2-5 | - | - | penultimate_en_candidate, attractor_lock, any_genuine_transformation_confirmed | false_return_confirmed, genuine_transformation_confirmed, false_return_confirmed |
| adv04_terminal_convergence_without_dup_spike.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:2-2 | - | - | mild_stagnation, attractor_lock | - |
| adv05_oscillating_novelty.json | I_EXPOSITION:0-0; III_DEVELOPMENT:2-2 | - | - | any_genuine_transformation_confirmed | genuine_transformation_confirmed, genuine_transformation_confirmed, genuine_transformation_confirmed |
| adv06_false_penultimate_candidate.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1; III_DEVELOPMENT:2-2; V_TERMINAL_CONVERGENCE:4-6 | - | - | attractor_lock, any_genuine_transformation_confirmed | genuine_transformation_confirmed, genuine_transformation_unconfirmed, false_return_confirmed |
| adv07_branch_explosion_no_attractor.json | I_EXPOSITION:0-0; V_TERMINAL_CONVERGENCE:5-5 | - | - | branch_explosion | - |
| adv08_monotonic_decline_only.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:4-4; V_TERMINAL_CONVERGENCE:5-6 | - | - | attractor_lock | - |
| adv09_late_recovery_after_apparent_lock.json | I_EXPOSITION:0-0; V_TERMINAL_CONVERGENCE:2-5 | - | - | any_genuine_transformation_confirmed | false_return_confirmed, false_return_confirmed, genuine_transformation_confirmed |
| adv10_random_walk.json | I_EXPOSITION:0-0; III_DEVELOPMENT:3-5; V_TERMINAL_CONVERGENCE:6-7 | - | - | any_genuine_transformation_confirmed | genuine_transformation_confirmed, low_eni_with_unexpected_recovery, genuine_transformation_confirmed |

## Per-fixture detail

### adv01_no_recovery_despite_high_en.json

- trajectory_id: `adv01_no_recovery_despite_high_en`  steps=6  en_events=1
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:1-1', 'V_TERMINAL_CONVERGENCE:3-5']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': True, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_unconfirmed']
- missed: []  spurious: ['attractor_lock']
- why_unseen: None

### adv02_recovery_below_threshold.json

- trajectory_id: `adv02_recovery_below_threshold`  steps=6  en_events=1
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:1-2']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['borderline_with_recovery']
- missed: []  spurious: []
- why_unseen: None

### adv03_phase_iv_without_two_consecutive_low_en.json

- trajectory_id: `adv03_phase_iv_without_two_consecutive_low_en`  steps=6  en_events=3
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:1-1', 'V_TERMINAL_CONVERGENCE:2-5']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': True, 'attractor_lock': True, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['false_return_confirmed', 'genuine_transformation_confirmed', 'false_return_confirmed']
- missed: []  spurious: ['penultimate_en_candidate', 'attractor_lock', 'any_genuine_transformation_confirmed']
- why_unseen: None

### adv04_terminal_convergence_without_dup_spike.json

- trajectory_id: `adv04_terminal_convergence_without_dup_spike`  steps=7  en_events=0
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:2-2']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': True, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': True, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: []  spurious: ['mild_stagnation', 'attractor_lock']
- why_unseen: None

### adv05_oscillating_novelty.json

- trajectory_id: `adv05_oscillating_novelty`  steps=7  en_events=3
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'III_DEVELOPMENT:2-2']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_confirmed', 'genuine_transformation_confirmed', 'genuine_transformation_confirmed']
- missed: []  spurious: ['any_genuine_transformation_confirmed']
- why_unseen: None

### adv06_false_penultimate_candidate.json

- trajectory_id: `adv06_false_penultimate_candidate`  steps=7  en_events=3
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:1-1', 'III_DEVELOPMENT:2-2', 'V_TERMINAL_CONVERGENCE:4-6']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': True, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_confirmed', 'genuine_transformation_unconfirmed', 'false_return_confirmed']
- missed: []  spurious: ['attractor_lock', 'any_genuine_transformation_confirmed']
- why_unseen: None

### adv07_branch_explosion_no_attractor.json

- trajectory_id: `adv07_branch_explosion_no_attractor`  steps=6  en_events=0
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'V_TERMINAL_CONVERGENCE:5-5']
- detector_hits: {'branch_explosion': True, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: []  spurious: ['branch_explosion']
- why_unseen: None

### adv08_monotonic_decline_only.json

- trajectory_id: `adv08_monotonic_decline_only`  steps=7  en_events=0
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:4-4', 'V_TERMINAL_CONVERGENCE:5-6']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': True, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: []  spurious: ['attractor_lock']
- why_unseen: None

### adv09_late_recovery_after_apparent_lock.json

- trajectory_id: `adv09_late_recovery_after_apparent_lock`  steps=9  en_events=3
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'V_TERMINAL_CONVERGENCE:2-5']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['false_return_confirmed', 'false_return_confirmed', 'genuine_transformation_confirmed']
- missed: []  spurious: ['any_genuine_transformation_confirmed']
- why_unseen: None

### adv10_random_walk.json

- trajectory_id: `adv10_random_walk`  steps=8  en_events=3
- expected failure mode: `None`  expected risk: `None`
- expected detector hits: []
- phases: ['I_EXPOSITION:0-0', 'III_DEVELOPMENT:3-5', 'V_TERMINAL_CONVERGENCE:6-7']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_confirmed', 'low_eni_with_unexpected_recovery', 'genuine_transformation_confirmed']
- missed: []  spurious: ['any_genuine_transformation_confirmed']
- why_unseen: None
