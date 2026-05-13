# Generalization suite evaluation — cycle_3

n_fixtures: **20**
phase overlaps (any pair): **0**
malformed phase spans: **0**
missed expected detector hits (sum across fixtures): **28**
spurious detector hits (sum across fixtures): **15**

## Detector fire counts (out of 20)

| Detector | Fires |
|---|---:|
| `any_genuine_transformation_confirmed` | 6 |
| `attractor_lock` | 5 |
| `branch_explosion` | 2 |
| `step_coherence_violation` | 2 |

## Per-fixture summary

| Fixture | Phases (name:start-end) | Overlaps | Missed | Spurious | Composite EN labels |
|---|---|---|---|---|---|
| gen01_near_threshold_EN.json | I_EXPOSITION:0-0 | - | composite_EN: borderline_no_recovery (loop 4) becomes _with_recovery; 0.09 stays low; 0.13 should be high | - | false_return_confirmed, borderline_with_recovery, genuine_transformation_unconfirmed |
| gen02_long_trajectory_30_loops.json | I_EXPOSITION:0-0; III_DEVELOPMENT:16-24 | - | Phase III multiple times (recovery cycles), no Phase V (dup never >0.5) | any_genuine_transformation_confirmed | genuine_transformation_unconfirmed, genuine_transformation_confirmed, genuine_transformation_confirmed |
| gen03_lock_recovery_lock.json | I_EXPOSITION:0-0; V_TERMINAL_CONVERGENCE:1-3 | - | Phase V should close on first recovery (cycle-2 logic), then re-trigger? Currently detector returns ONLY the first trigger — multi-lock is invisible. | attractor_lock, any_genuine_transformation_confirmed | genuine_transformation_confirmed |
| gen04_branch_explosion_with_recovery.json | I_EXPOSITION:0-0 | - | branch_explosion likely triggers (avg dup<0.20, distinct branches >=5 over loops 0-4) even though late synthesis recovers. | attractor_lock | - |
| gen05_noisy_random_walk.json | I_EXPOSITION:0-0; III_DEVELOPMENT:3-7 | - | composite_EN labels vary; cycle-9 Phase II persistence rule should prevent false fire. | any_genuine_transformation_confirmed | genuine_transformation_confirmed, low_eni_with_unexpected_recovery, genuine_transformation_confirmed |
| gen06_mixed_stagnation_branch.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1 | - | mild_stagnation: maybe (tail of last 5 covers loops 3-7, mostly branch-explosion territory), branch_explosion: maybe (8 distinct branches in second half) | branch_explosion | - |
| gen07_sparse_late_EN.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:6-6; V_TERMINAL_CONVERGENCE:7-7 | - | Phase V should fire (dup>0.50 around loop 5+), composite_EN: 0.20 high but novel_next=0 -> genuine_transformation_unconfirmed | attractor_lock | genuine_transformation_unconfirmed |
| gen08_conflicting_metrics.json | I_EXPOSITION:0-0; V_TERMINAL_CONVERGENCE:3-3 | - | step_coherence: should detect incoherent step at loop 1 | step_coherence_violation | - |
| gen09_soft_convergence.json | I_EXPOSITION:0-0 | - | mild_stagnation should fire (tail mean novel <= 2.5, dup strictly increasing, no Phase V, no EN) | - | - |
| gen10_terminal_failure_with_recovery.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1; V_TERMINAL_CONVERGENCE:2-6 | - | Phase V should NOT close on reversal (terminal_failure_mode set -> cycle-2 keeps span open) | any_genuine_transformation_confirmed | genuine_transformation_confirmed |
| gen11_repeated_borderline_EN.json | I_EXPOSITION:0-0 | - | composite_EN: all 'borderline' family, penultimate-EN: no confirmed candidate (none in genuine band) | - | borderline_no_recovery, borderline_no_recovery, borderline_no_recovery, borderline_with_recovery |
| gen12_multiple_penultimate_candidates.json | I_EXPOSITION:0-0; III_DEVELOPMENT:2-4 | - | penultimate-EN: penultimate=loop 7 (false_return_confirmed), last=loop 9 (unconfirmed). has_candidate should be False. | any_genuine_transformation_confirmed | genuine_transformation_confirmed, false_return_confirmed, genuine_transformation_confirmed, false_return_confirmed, genuine_transformation_unconfirmed |
| gen13_delayed_phase_IV.json | I_EXPOSITION:0-0; III_DEVELOPMENT:3-16; IV_DEEPENING_ATTRACTOR:17-19 | - | Phase IV should fire at loops 17..19 (two consecutive low ENI very late) | any_genuine_transformation_confirmed | genuine_transformation_confirmed, false_return_confirmed, false_return_confirmed |
| gen14_phase_reversal_twice.json | I_EXPOSITION:0-0; V_TERMINAL_CONVERGENCE:1-2 | - | Phase V should close at loop 2 (after 2 broken loops 3-4). Second lock at loops 5-6 NOT detected. | - | - |
| gen15_high_EN_no_recovery_chain.json | II_FIRST_SATURATION_MODULATION:1-3; V_TERMINAL_CONVERGENCE:4-7 | - | composite_EN: 3 'genuine_transformation_unconfirmed' labels, Phase III should NOT fire (no confirmed) | attractor_lock | genuine_transformation_unconfirmed, genuine_transformation_unconfirmed, genuine_transformation_unconfirmed |
| gen16_low_EN_strong_recovery_chain.json | IV_DEEPENING_ATTRACTOR:1-3 | - | composite_EN: 3 'low_eni_with_unexpected_recovery' labels, Phase III should NOT fire (no confirmed genuine) | - | low_eni_with_unexpected_recovery, low_eni_with_unexpected_recovery, low_eni_with_unexpected_recovery |
| gen17_graph_growth_then_prune.json | I_EXPOSITION:0-0 | - | branch_explosion may fire on tail-3 avg (currently averages whole trajectory) | - | - |
| gen18_stagnation_then_branch.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1 | - | mild_stagnation: tail of last 5 covers loops 4-8 which is branch territory (mean novel=7) - should NOT fire, branch_explosion: ~10 distinct branches, avg dup~0.18 - should fire | branch_explosion | - |
| gen19_no_EN_saturation_then_recovery.json | I_EXPOSITION:0-0; II_FIRST_SATURATION_MODULATION:1-1 | - | Phase II (cycle-3): fires (no EN required); persistence at loops 1+2 satisfies cycle-9, mild_stagnation: tail-5 is loops 2-6 (mean novel ~3.6) — depends on whether dup is strictly increasing across that window (it isn't) — should NOT fire | - | - |
| gen20_metric_incoherence_edge.json | I_EXPOSITION:0-0 | - | step_coherence: loop 1 (dup=0.71, novel=5) should fire; loop 3 (dup=0.04, novel=0 after loop 0) should fire | step_coherence_violation, attractor_lock | - |

## Per-fixture detail

### gen01_near_threshold_EN.json

- trajectory_id: `gen01_near_threshold_EN`  steps=8  en_events=3
- expected failure mode: `None`  expected risk: `Threshold sensitivity — 0.09, 0.11, 0.13 straddle 0.10/0.12 boundaries.`
- expected detector hits: ['composite_EN: borderline_no_recovery (loop 4) becomes _with_recovery; 0.09 stays low; 0.13 should be high']
- phases: ['I_EXPOSITION:0-0']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['false_return_confirmed', 'borderline_with_recovery', 'genuine_transformation_unconfirmed']
- missed: ['composite_EN: borderline_no_recovery (loop 4) becomes _with_recovery; 0.09 stays low; 0.13 should be high']  spurious: []
- why_unseen: Original suite had values >=0.12 separated from <=0.07. This probes the exact boundary band.

### gen02_long_trajectory_30_loops.json

- trajectory_id: `gen02_long_trajectory_30_loops`  steps=30  en_events=3
- expected failure mode: `None`  expected risk: `Long-trajectory threshold drift — detectors calibrated on 8-loop fixtures may misbehave.`
- expected detector hits: ['Phase III multiple times (recovery cycles)', 'no Phase V (dup never >0.5)']
- phases: ['I_EXPOSITION:0-0', 'III_DEVELOPMENT:16-24']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_unconfirmed', 'genuine_transformation_confirmed', 'genuine_transformation_confirmed']
- missed: ['Phase III multiple times (recovery cycles)', 'no Phase V (dup never >0.5)']  spurious: ['any_genuine_transformation_confirmed']
- why_unseen: Original suite was 6-9 loops; this is 30 loops with multiple genuine EN events.

### gen03_lock_recovery_lock.json

- trajectory_id: `gen03_lock_recovery_lock`  steps=9  en_events=1
- expected failure mode: `None`  expected risk: `Phase V detector returns first trigger only; second lock will be missed.`
- expected detector hits: ['Phase V should close on first recovery (cycle-2 logic), then re-trigger? Currently detector returns ONLY the first trigger — multi-lock is invisible.']
- phases: ['I_EXPOSITION:0-0', 'V_TERMINAL_CONVERGENCE:1-3']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': True, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_confirmed']
- missed: ['Phase V should close on first recovery (cycle-2 logic), then re-trigger? Currently detector returns ONLY the first trigger — multi-lock is invisible.']  spurious: ['attractor_lock', 'any_genuine_transformation_confirmed']
- why_unseen: Cycle 2 closed Phase V on reversal but doesn't re-open. Lock-recovery-lock pattern is new.

### gen04_branch_explosion_with_recovery.json

- trajectory_id: `gen04_branch_explosion_with_recovery`  steps=8  en_events=0
- expected failure mode: `None`  expected risk: `Branch-explosion detector averages over whole trajectory — a late recovery doesn't reduce the count.`
- expected detector hits: ['branch_explosion likely triggers (avg dup<0.20, distinct branches >=5 over loops 0-4) even though late synthesis recovers.']
- phases: ['I_EXPOSITION:0-0']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': True, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: ['branch_explosion likely triggers (avg dup<0.20, distinct branches >=5 over loops 0-4) even though late synthesis recovers.']  spurious: ['attractor_lock']
- why_unseen: adv07 was pure branch explosion until end. This recovers; tests whether detector is fooled.

### gen05_noisy_random_walk.json

- trajectory_id: `gen05_noisy_random_walk`  steps=10  en_events=3
- expected failure mode: `None`  expected risk: `Cycle-9 persistence may still fire on the loops 1-2 dip if noise aligns.`
- expected detector hits: ['composite_EN labels vary; cycle-9 Phase II persistence rule should prevent false fire.']
- phases: ['I_EXPOSITION:0-0', 'III_DEVELOPMENT:3-7']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_confirmed', 'low_eni_with_unexpected_recovery', 'genuine_transformation_confirmed']
- missed: ['composite_EN labels vary; cycle-9 Phase II persistence rule should prevent false fire.']  spurious: ['any_genuine_transformation_confirmed']
- why_unseen: Larger noise amplitude than adv10; mixes near-threshold ENs with random walks.

### gen06_mixed_stagnation_branch.json

- trajectory_id: `gen06_mixed_stagnation_branch`  steps=8  en_events=0
- expected failure mode: `None`  expected risk: `Two pathologies in one trajectory; mild_stagnation tail-window logic may miss because it's a TAIL detector.`
- expected detector hits: ['mild_stagnation: maybe (tail of last 5 covers loops 3-7, mostly branch-explosion territory)', 'branch_explosion: maybe (8 distinct branches in second half)']
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:1-1']
- detector_hits: {'branch_explosion': True, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: ['mild_stagnation: maybe (tail of last 5 covers loops 3-7, mostly branch-explosion territory)', 'branch_explosion: maybe (8 distinct branches in second half)']  spurious: ['branch_explosion']
- why_unseen: Original suite had pure pathologies, not mixed.

### gen07_sparse_late_EN.json

- trajectory_id: `gen07_sparse_late_EN`  steps=8  en_events=1
- expected failure mode: `ATTRACTOR_LOCK`  expected risk: `Phase III may still fire on the late EN if it's the FIRST confirmed genuine, but it's unconfirmed -> should not fire.`
- expected detector hits: ['Phase V should fire (dup>0.50 around loop 5+)', 'composite_EN: 0.20 high but novel_next=0 -> genuine_transformation_unconfirmed']
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:6-6', 'V_TERMINAL_CONVERGENCE:7-7']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': True, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_unconfirmed']
- missed: ['Phase V should fire (dup>0.50 around loop 5+)', 'composite_EN: 0.20 high but novel_next=0 -> genuine_transformation_unconfirmed']  spurious: ['attractor_lock']
- why_unseen: Original suite had EN events mostly at loops 1-5. This places the only EN at loop 7.

### gen08_conflicting_metrics.json

- trajectory_id: `gen08_conflicting_metrics`  steps=4  en_events=0
- expected failure mode: `None`  expected risk: `If cycle-6 thresholds miss the dup>0.70 AND novel>=5 rule, this slips.`
- expected detector hits: ['step_coherence: should detect incoherent step at loop 1']
- phases: ['I_EXPOSITION:0-0', 'V_TERMINAL_CONVERGENCE:3-3']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': True, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: ['step_coherence: should detect incoherent step at loop 1']  spurious: ['step_coherence_violation']
- why_unseen: Original suite had no incoherent steps; cycle 6 was defensive.

### gen09_soft_convergence.json

- trajectory_id: `gen09_soft_convergence`  steps=8  en_events=0
- expected failure mode: `None`  expected risk: `Borderline-tail-mean trajectory; if MILD_STAGNATION_MAX_AVG_NOVEL=2.5 is too strict, this slips.`
- expected detector hits: ['mild_stagnation should fire (tail mean novel <= 2.5, dup strictly increasing, no Phase V, no EN)']
- phases: ['I_EXPOSITION:0-0']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: ['mild_stagnation should fire (tail mean novel <= 2.5, dup strictly increasing, no Phase V, no EN)']  spurious: []
- why_unseen: Different decay shape than adv04 — gradual rather than abrupt.

### gen10_terminal_failure_with_recovery.json

- trajectory_id: `gen10_terminal_failure_with_recovery`  steps=7  en_events=1
- expected failure mode: `NOVELTY_COLLAPSE`  expected risk: `Cycle-2 has_terminal_failure guard preserves Phase V over loops 2..6. May overstate convergence when DES later recovers.`
- expected detector hits: ['Phase V should NOT close on reversal (terminal_failure_mode set -> cycle-2 keeps span open)']
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:1-1', 'V_TERMINAL_CONVERGENCE:2-6']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_confirmed']
- missed: ['Phase V should NOT close on reversal (terminal_failure_mode set -> cycle-2 keeps span open)']  spurious: ['any_genuine_transformation_confirmed']
- why_unseen: adv09 had no terminal_failure_mode + recovered. This has both — tests the guard.

### gen11_repeated_borderline_EN.json

- trajectory_id: `gen11_repeated_borderline_EN`  steps=8  en_events=4
- expected failure mode: `None`  expected risk: `Bimodal classifier's borderline-band returns 4 'borderline' labels; downstream might mis-treat.`
- expected detector hits: ["composite_EN: all 'borderline' family", 'penultimate-EN: no confirmed candidate (none in genuine band)']
- phases: ['I_EXPOSITION:0-0']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['borderline_no_recovery', 'borderline_no_recovery', 'borderline_no_recovery', 'borderline_with_recovery']
- missed: ["composite_EN: all 'borderline' family", 'penultimate-EN: no confirmed candidate (none in genuine band)']  spurious: []
- why_unseen: Original suite never had 4 consecutive borderline ENs.

### gen12_multiple_penultimate_candidates.json

- trajectory_id: `gen12_multiple_penultimate_candidates`  steps=10  en_events=5
- expected failure mode: `None`  expected risk: `Detector only looks at last two ENs; intermediate confirmed-genuines (loops 1, 5) are ignored.`
- expected detector hits: ['penultimate-EN: penultimate=loop 7 (false_return_confirmed), last=loop 9 (unconfirmed). has_candidate should be False.']
- phases: ['I_EXPOSITION:0-0', 'III_DEVELOPMENT:2-4']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_confirmed', 'false_return_confirmed', 'genuine_transformation_confirmed', 'false_return_confirmed', 'genuine_transformation_unconfirmed']
- missed: ['penultimate-EN: penultimate=loop 7 (false_return_confirmed), last=loop 9 (unconfirmed). has_candidate should be False.']  spurious: ['any_genuine_transformation_confirmed']
- why_unseen: Many ENs in one trajectory probes the principle's last-two-only blind spot.

### gen13_delayed_phase_IV.json

- trajectory_id: `gen13_delayed_phase_IV`  steps=20  en_events=3
- expected failure mode: `None`  expected risk: `Detector finds the run regardless of position. Probably OK.`
- expected detector hits: ['Phase IV should fire at loops 17..19 (two consecutive low ENI very late)']
- phases: ['I_EXPOSITION:0-0', 'III_DEVELOPMENT:3-16', 'IV_DEEPENING_ATTRACTOR:17-19']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': True, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_confirmed', 'false_return_confirmed', 'false_return_confirmed']
- missed: ['Phase IV should fire at loops 17..19 (two consecutive low ENI very late)']  spurious: ['any_genuine_transformation_confirmed']
- why_unseen: Phase IV trigger placed at end of a 20-loop trajectory rather than mid-trajectory.

### gen14_phase_reversal_twice.json

- trajectory_id: `gen14_phase_reversal_twice`  steps=9  en_events=0
- expected failure mode: `None`  expected risk: `Phase V detector returns FIRST trigger only. Second lock invisible.`
- expected detector hits: ['Phase V should close at loop 2 (after 2 broken loops 3-4). Second lock at loops 5-6 NOT detected.']
- phases: ['I_EXPOSITION:0-0', 'V_TERMINAL_CONVERGENCE:1-2']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: ['Phase V should close at loop 2 (after 2 broken loops 3-4). Second lock at loops 5-6 NOT detected.']  spurious: []
- why_unseen: Like gen03 lock-recovery-lock, but with no terminal_failure_mode. Two completely independent cycles.

### gen15_high_EN_no_recovery_chain.json

- trajectory_id: `gen15_high_EN_no_recovery_chain`  steps=8  en_events=3
- expected failure mode: `ATTRACTOR_LOCK`  expected risk: `Pre-cycle-10 phase III would fire on first high-ENI. Post-cycle-10 it shouldn't. Generalization test.`
- expected detector hits: ["composite_EN: 3 'genuine_transformation_unconfirmed' labels", 'Phase III should NOT fire (no confirmed)']
- phases: ['II_FIRST_SATURATION_MODULATION:1-3', 'V_TERMINAL_CONVERGENCE:4-7']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': True, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['genuine_transformation_unconfirmed', 'genuine_transformation_unconfirmed', 'genuine_transformation_unconfirmed']
- missed: ["composite_EN: 3 'genuine_transformation_unconfirmed' labels", 'Phase III should NOT fire (no confirmed)']  spurious: ['attractor_lock']
- why_unseen: Chain of high-ENI events that all fail to recover — adv01 had only one.

### gen16_low_EN_strong_recovery_chain.json

- trajectory_id: `gen16_low_EN_strong_recovery_chain`  steps=8  en_events=3
- expected failure mode: `None`  expected risk: `Legacy classifier still calls these 'false_return'. Pre-cycle-7 there'd be no signal of recovery. Post-cycle-7 composite labels surface it.`
- expected detector hits: ["composite_EN: 3 'low_eni_with_unexpected_recovery' labels", 'Phase III should NOT fire (no confirmed genuine)']
- phases: ['IV_DEEPENING_ATTRACTOR:1-3']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: ['low_eni_with_unexpected_recovery', 'low_eni_with_unexpected_recovery', 'low_eni_with_unexpected_recovery']
- missed: ["composite_EN: 3 'low_eni_with_unexpected_recovery' labels", 'Phase III should NOT fire (no confirmed genuine)']  spurious: []
- why_unseen: adv02 was single low-EN-with-recovery; this is a chain.

### gen17_graph_growth_then_prune.json

- trajectory_id: `gen17_graph_growth_then_prune`  steps=7  en_events=0
- expected failure mode: `None`  expected risk: `Branch detector doesn't distinguish growth phase from prune phase.`
- expected detector hits: ['branch_explosion may fire on tail-3 avg (currently averages whole trajectory)']
- phases: ['I_EXPOSITION:0-0']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: ['branch_explosion may fire on tail-3 avg (currently averages whole trajectory)']  spurious: []
- why_unseen: DES would emit a SYNTHESIS-style operator to close branches. This tests whether the detector recognizes prune.

### gen18_stagnation_then_branch.json

- trajectory_id: `gen18_stagnation_then_branch`  steps=9  en_events=0
- expected failure mode: `None`  expected risk: `Mild stagnation's tail-window logic ignores the early stagnation phase entirely.`
- expected detector hits: ['mild_stagnation: tail of last 5 covers loops 4-8 which is branch territory (mean novel=7) - should NOT fire', 'branch_explosion: ~10 distinct branches, avg dup~0.18 - should fire']
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:1-1']
- detector_hits: {'branch_explosion': True, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: ['mild_stagnation: tail of last 5 covers loops 4-8 which is branch territory (mean novel=7) - should NOT fire', 'branch_explosion: ~10 distinct branches, avg dup~0.18 - should fire']  spurious: ['branch_explosion']
- why_unseen: Composite pathology with phase change mid-trajectory.

### gen19_no_EN_saturation_then_recovery.json

- trajectory_id: `gen19_no_EN_saturation_then_recovery`  steps=7  en_events=0
- expected failure mode: `None`  expected risk: `Recovery without EN is invisible to Phase III. Trajectory will look like Phase I + Phase II only.`
- expected detector hits: ['Phase II (cycle-3): fires (no EN required); persistence at loops 1+2 satisfies cycle-9', "mild_stagnation: tail-5 is loops 2-6 (mean novel ~3.6) — depends on whether dup is strictly increasing across that window (it isn't) — should NOT fire"]
- phases: ['I_EXPOSITION:0-0', 'II_FIRST_SATURATION_MODULATION:1-1']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': False, 'penultimate_en_candidate': False, 'attractor_lock': False, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: ['Phase II (cycle-3): fires (no EN required); persistence at loops 1+2 satisfies cycle-9', "mild_stagnation: tail-5 is loops 2-6 (mean novel ~3.6) — depends on whether dup is strictly increasing across that window (it isn't) — should NOT fire"]  spurious: []
- why_unseen: adv08 had saturation but no recovery. This adds a recovery to test whether DESi can detect it without EN signal.

### gen20_metric_incoherence_edge.json

- trajectory_id: `gen20_metric_incoherence_edge`  steps=4  en_events=0
- expected failure mode: `None`  expected risk: `Tests the EDGE of cycle-6 thresholds. Loop 2 should NOT fire (dup=0.69 < 0.70).`
- expected detector hits: ['step_coherence: loop 1 (dup=0.71, novel=5) should fire; loop 3 (dup=0.04, novel=0 after loop 0) should fire']
- phases: ['I_EXPOSITION:0-0']
- detector_hits: {'branch_explosion': False, 'mild_stagnation': False, 'step_coherence_violation': True, 'penultimate_en_candidate': False, 'attractor_lock': True, 'any_genuine_transformation_confirmed': False, 'any_recovered_after_high_eni': False, 'any_stuck_high_eni': False}
- composite_en_labels: []
- missed: ['step_coherence: loop 1 (dup=0.71, novel=5) should fire; loop 3 (dup=0.04, novel=0 after loop 0) should fire']  spurious: ['step_coherence_violation', 'attractor_lock']
- why_unseen: Original adv set was clean; cycle 6 was forward-looking. This is the first real test.
