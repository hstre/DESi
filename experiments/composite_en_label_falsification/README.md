# Composite-EN-label falsification

Branch `experiment/desi-birth-falsification` (branch name preserves
the original misnamed intent; see `../semantic_drift_report.md`).

## Read this first

This directory was originally named `experiments/birth_falsification/`
on the false premise that

```
birth(B) := composite EN classifier produces "genuine_transformation_confirmed"
```

That premise was a category error. Paper 0 defines
`birth(B) = (D, R, F, P, ΔQ)` — a 5-tuple, not a single boolean
composite label. The user caught the substitution and ordered a
semantic-drift audit. **See `../semantic_drift_report.md`** for the
full post-mortem.

What this directory actually probes is **the boundary behavior of
`classify_en_event_composite`'s `genuine_transformation_confirmed`
label** and adjacent phase-detection logic. That is not birth(B).
The findings here are real DESi findings about composite-EN label
boundaries; they are not Paper 0 falsifications.

## Operational definition (corrected)

```
confirmed_genuine_en(traj) = 1 iff classify_en_event_composite(e).label
                                     == "genuine_transformation_confirmed"
                              for some e in traj.en_events.
```

This is the actual quantity the cycles below force to 0.

## Rules (unchanged from the original misnamed attempt)

- DESi source is NOT modified. The probe runs the existing
  `compute_all` and reports.
- Each cycle: hypothesis → fixture → measurement → verdict.
- Every cycle is documented (this README + cycle_N/ artefacts).
- Failed hypotheses are preserved (cycle_N/ stays even if a
  hypothesis turns out not to falsify).
- No prior metrics rewritten.
- Stop when marginal epistemic gain approaches zero.

## Cycle log

| Cycle | Hypothesis | Fixture | confirmed_genuine_en | report Phase III | Falsified? |
|---:|---|---|:---:|:---:|:---:|
| 1 | eni=0.12 exactly + strong recovery → confirmed | `fx1_eni_eq_high_threshold_with_recovery` | **0** | 0 | YES (boundary) |
| 2 | eni=0.18 + dup_delta=-0.08 + novel_next=6 → confirmed | `fx2_high_eni_partial_dup_recovery` | **0** | 0 | YES (threshold) |
| 3 | confirmed-genuine EN + terminal_failure_mode → Phase III preserved | `fx3_terminal_failure_then_confirmed_birth` | 1 | **0** | PARTIAL (clip) |
| 4 | evaluator's phantom composite-label keys ever fire | (cross-suite scan) | n/a | n/a | YES (tooling) |

(See `cycle_N/proposal.md` + `cycle_N/evaluation.md` for full details.
References to "birth(B)" inside those files date from before the
semantic-drift audit; they are preserved verbatim as the historical
record of the mislabelling, with a header note in each cycle pointing
back here.)

## Findings (factual content, unchanged)

### Three distinct failure classes force `confirmed_genuine_en = 0`

1. **High-ENI strict-greater boundary.** `classify_en_event_composite`
   uses `eni > 0.12` (strict). An EN event at exactly the documented
   high-threshold value falls to `borderline`, and even with strong
   recovery becomes `borderline_with_recovery`, not
   `genuine_transformation_confirmed`. `confirmed_genuine_en = 0`
   forced.

2. **Recovery dup-delta threshold + float fragility.**
   `compute_novelty_recovery` requires `dup_delta <= -0.10`. A real
   recovery with a smaller-magnitude dup drop (e.g. -0.08 alongside
   6 novel claims and sustained low-dup tail) is labelled
   `genuine_transformation_unconfirmed`; `confirmed_genuine_en = 0`.
   Compounded by IEEE-754 float comparison fragility on the boundary
   itself.

3. **Phase-clip suppression of the report-level signal.** When
   `terminal_failure_mode` is set, Phase V extends to
   end-of-trajectory and gen-cycle-2's `_clip_phase_overlaps` drops
   Phase III entirely when it sits inside Phase V's span. The
   composite metric still says `confirmed_genuine_en = 1`, but the
   user-facing markdown report has no Phase III span: report-level
   signal = 0. Two readers of DESi output can validly disagree about
   whether a genuine transformation was confirmed depending on which
   surface they consult.

### One tooling contradiction

4. **`evaluate_suite.py` references composite-label strings that the
   classifier never produces** (`recovered_after_high_eni`,
   `stuck_high_eni`). Those detector_hits keys are dead — `False`
   identically across all trajectories. The names suggest measurements
   that the implementation does not actually perform.

## What is NOT here

These cycles do not falsify Paper 0's `birth(B) = (D, R, F, P, ΔQ)`.
That falsification remains open. It requires Paper 0's definitions of
D, R, F, P, ΔQ — which are absent from this repository. See
`../semantic_drift_report.md`.
