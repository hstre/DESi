> **Mislabelling note (added in semantic-drift audit):** this file
> refers to `birth(B)` throughout. That term was incorrectly bound to
> `confirmed_genuine_en` in the original probe. Paper 0 defines
> `birth(B) = (D, R, F, P, ΔQ)`; the cycle's findings concern composite-EN
> label boundaries, not Paper 0's tuple. See
> `../../semantic_drift_report.md` for the post-mortem. The factual
> content below is preserved verbatim as the historical record.

# Cycle 3 evaluation — birth signal splits between metric and report levels

## Probe output (verbatim)

```
trajectory_id: fx3_terminal_failure_then_confirmed_birth
n_en_events: 1
composite_labels: ["genuine_transformation_confirmed"]
novelty_recoveries: [{loop: 3, dup_delta: -0.33, novel_next: 5, recovered: true}]
phase_iii_present: false
phase_iii_span: null
confirmed_count: 1
birth_B: 1     <-- composite-level birth signal
```

## Verdict: **PARTIALLY FALSIFIED**

The two birth signals **disagree**:

| Birth interpretation | Value | Source |
|---|:---:|---|
| Composite-metric (`any genuine_transformation_confirmed`) | **1** | `compute_all().en_classifications_composite` |
| Operational / report-level (`Phase III present?`) | **0** | `detect_phases()` after `_clip_phase_overlaps` |

The classifier correctly mints `genuine_transformation_confirmed`
on a 0.18 ENI with strong recovery; the post-processor erases the
Phase III span entirely because gen-cycle-2's
`_clip_phase_overlaps` drops a phase span fully contained inside
a later phase. With `terminal_failure_mode` set, Phase V is
loops 1..6 (whole tail); Phase III is loops 4..6 (post-EN); Phase
III is fully subsumed; Phase III is dropped.

## Discussion

This is a real falsification of the **report-level** birth signal.
DESi's user-facing markdown (`render_report`) iterates over phase
spans in its Phase Detection section. A reader of the report on
this trajectory will see ONLY Phase V (terminal lock) — no Phase
III. The trajectory **did** have a confirmed genuine
transformation, and the composite label is rendered in the "New
deterministic detectors" section, but the **phase-level birth
verdict is wrong**: the trajectory looks terminal-with-no-birth.

This is a more interesting falsification than cycles 1-2 because:

1. It's not a threshold boundary — the trajectory is squarely
   inside the "high ENI + strong recovery" regime.
2. The metric level is internally consistent (composite says
   confirmed; recovery flag fires).
3. The disagreement between metric and operational levels means
   **two readers of DESi's output can validly disagree about
   whether birth occurred** depending on which output surface
   they consult.

This is the kind of internal contradiction Paper 0 should
acknowledge: when terminal_failure_mode is set on a trajectory
that actually recovered, the phase model loses the recovery
information even though the composite metric retains it.

## Marginal epistemic gain

**Non-zero.** A different *kind* of failure than cycles 1-2 —
a cross-detector inconsistency rather than a threshold boundary.

## Stop or continue?

Continue with one more probe to test if the falsification space
extends further, then synthesize. Cycle 4 candidate: long
trajectory where the FIRST genuine EN is followed by a long
no-EN tail; does Phase III span the right window, and does the
composite-level confirm count accurately?

Actually — re-reading the n=20 baseline, all the "Phase III"
disagreements are clipping-related, and clipping is by design
post-gen-cycle-2. The remaining falsification space probably
lies in role / auditor drift, which requires LLM-side probing
and is out of scope for this deterministic probe.

**Tentative stop.** Three cycles is enough to demonstrate the
falsification space; further cycles would mostly repeat the
three categories already established.
