# Birth(B) falsification

Branch `experiment/desi-birth-falsification`. Adversarial probe of DESi's
**birth detection**. DESi/Paper-0 treats a `genuine_transformation_confirmed`
EN event as the canonical birth signal — Phase III's first trigger consumes
it; the penultimate-EN principle consumes it; the composite classifier
mints it. If `birth(B)=0` for a trajectory Paper 0 would call a real
breakthrough, the system is wrong.

## Operational definition

```
birth(B) = 1 iff there exists a composite EN classification
            with label == "genuine_transformation_confirmed"
        in the trajectory's metrics.
```

(Equivalently: did `classify_en_event_composite` return any
`genuine_transformation_confirmed` label?)

This collapses two upstream conditions:

1. `eni_novelty > ENI_HIGH_THRESHOLD` (i.e. `> 0.12`, strict).
2. `compute_novelty_recovery(event).recovered` is True
   (`dup_delta <= -0.10 AND novel_claims_next >= 1`).

Both conditions are necessary. Failing EITHER produces birth(B) = 0.
The downstream "did Phase III fire?" follows the same gate.

## Rules

- DESi source is NOT modified. The probe runs the existing
  `compute_all` and reports.
- Each cycle: hypothesis → fixture → measurement → verdict.
- Every cycle is documented (this README + cycle_N/ artefacts).
- Failed hypotheses are preserved (cycle_N/ stays even if a
  hypothesis turns out not to falsify).
- No prior metrics rewritten.
- Stop when marginal epistemic gain approaches zero.

## Cycle log

| Cycle | Hypothesis | Fixture | metric birth(B) | report birth | Falsified? |
|---:|---|---|:---:|:---:|:---:|
| 1 | eni=0.12 exactly + strong recovery → birth | `fx1_eni_eq_high_threshold_with_recovery` | **0** | 0 | YES (boundary) |
| 2 | eni=0.18 + dup_delta=-0.08 + novel_next=6 → birth | `fx2_high_eni_partial_dup_recovery` | **0** | 0 | YES (threshold) |
| 3 | confirmed birth + terminal_failure_mode → Phase III preserved | `fx3_terminal_failure_then_confirmed_birth` | 1 | **0** | PARTIAL (clip) |
| 4 | evaluator's phantom composite-label keys ever fire | (cross-suite scan) | n/a | n/a | YES (tooling) |

(See `cycle_N/proposal.md` + `cycle_N/evaluation.md` for full details.)

## Findings

### Three distinct failure classes force birth(B) = 0

1. **High-ENI strict-greater boundary.** `classify_en_event_composite`
   uses `eni > 0.12` (strict). An EN event at exactly the documented
   high-threshold value falls to `borderline`, and even with strong
   recovery becomes `borderline_with_recovery`, not
   `genuine_transformation_confirmed`. birth(B) = 0 forced.

2. **Recovery dup-delta threshold + float fragility.**
   `compute_novelty_recovery` requires `dup_delta <= -0.10`. A real
   recovery with a smaller-magnitude dup drop (e.g. -0.08 alongside
   6 novel claims and sustained low-dup tail) is labelled
   `genuine_transformation_unconfirmed`; birth(B) = 0. Compounded by
   IEEE-754 float comparison fragility on the boundary itself.

3. **Phase-clip suppression of the report-level birth signal.**
   When `terminal_failure_mode` is set, Phase V extends to
   end-of-trajectory and gen-cycle-2's `_clip_phase_overlaps` drops
   Phase III entirely when it sits inside Phase V's span. The
   composite metric still says birth = 1, but the user-facing
   markdown report has no Phase III span: report-level birth = 0.
   Two readers of DESi output can validly disagree about whether
   birth occurred depending on which surface they consult.

### One tooling contradiction

4. **`evaluate_suite.py` references composite-label strings that the
   classifier never produces** (`recovered_after_high_eni`,
   `stuck_high_eni`). Those detector_hits keys are dead — `False`
   identically across all trajectories. The names suggest measurements
   that the implementation does not actually perform.

## What this means for Paper 0

Paper 0 should acknowledge:

- The bimodal classifier's threshold inclusion is asymmetric:
  the high-side comparison is strict and excludes the documented
  threshold value. Either the comparison or the documented
  threshold must change. (Falsification class 1.)

- The "recovery" predicate's `-0.10` cutoff is calibrated against
  the original adversarial suite's big-step recoveries and is too
  strict for plausible real DES runs with smoother dup decay.
  (Falsification class 2.)

- The phase model can SILENTLY drop a confirmed-birth signal
  when terminal_failure_mode is set, leaving a contradiction
  between the composite-metric output and the phase-detection
  output. Either the clip rule needs an exception, or the
  metric/phase divergence needs to be flagged explicitly in the
  rendered report. (Falsification class 3.)

- Cross-validation of falsification tooling against the
  implementation's actual output is a standing requirement. The
  phantom-label keys would have been caught by running the
  evaluator against ANY fixture and checking whether the keys
  ever flipped to True. (Class 4.)

## Stop reasoning

Three distinct deterministic-side failure classes were established
in cycles 1-3. Cycle 4 added a tooling artefact. Plausible further
probes (long-trajectory drift, role/auditor interactions,
echo-chamber conditions) either repeat the threshold-boundary
shape established in cycle 1 (long-trajectory drift) or require
LLM-side execution that is out of scope for a deterministic probe.
Marginal epistemic gain is approximately zero.

**Loop terminated at cycle 4** per the user's "stop when marginal
gain approaches zero" criterion. No code in `src/desi/` was
modified. Branch `experiment/desi-birth-falsification` is not
merged to `main`.

