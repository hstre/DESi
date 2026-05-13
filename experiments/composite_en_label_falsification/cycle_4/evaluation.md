> **Mislabelling note (added in semantic-drift audit):** this file
> refers to `birth(B)` throughout. That term was incorrectly bound to
> `confirmed_genuine_en` in the original probe. Paper 0 defines
> `birth(B) = (D, R, F, P, ΔQ)`; the cycle's findings concern composite-EN
> label boundaries, not Paper 0's tuple. See
> `../../semantic_drift_report.md` for the post-mortem. The factual
> content below is preserved verbatim as the historical record.

# Cycle 4 evaluation — confirmed phantom labels in evaluator dict

## Probe output (verbatim)

```
n=10 adversarial: any_recovered_after_high_eni fires on 0 fixtures;
                  any_stuck_high_eni fires on 0
composite labels actually produced (n=10 adversarial):
  - borderline_with_recovery
  - false_return_confirmed
  - genuine_transformation_confirmed
  - genuine_transformation_unconfirmed
  - low_eni_with_unexpected_recovery
(out of the 6-label specification; `borderline_no_recovery` produced
on n=20 but not n=10.)
```

## Verdict: **CONFIRMED METRIC CONTRADICTION**

`experiments/generalization_loop/evaluate_suite.py` contains the
detector_hits keys

- `any_recovered_after_high_eni`
- `any_stuck_high_eni`

both of which test for composite-label strings that the implementation
never produces. The actual label set is enumerated in
`classify_en_event_composite` and uses different names. The evaluator's
keys are therefore **unreachable**: they evaluate to `False` for every
trajectory.

This is a contradiction *internal to the generalization-loop tooling*:
the evaluator was authored against a label-set specification that
diverged from the implementation. If `birth(B)` were interpreted via
either of those keys, birth(B) would be **0 identically** across all
possible trajectories.

## Discussion

This is **not** a falsification of the composite classifier — that
component is internally consistent. It IS a falsification of the
evaluator's claim to be measuring those signals. Anyone reading the
generalization-loop metrics_json output and seeing
`any_recovered_after_high_eni: false` across all 20 fixtures should
not infer "no trajectory ever showed recovery after high ENI";
they should infer "this key is dead and the metric never measured
what its name implies".

## Marginal epistemic gain

**Diminishing.** This is a low-grade discovery — a bug in the
falsification *tooling* rather than in DESi itself. Worth recording
because it explains a `0` value that a reader might otherwise treat
as meaningful.

## Stop or continue?

**STOP.** Further cycles would:

- Re-probe the same threshold boundary classes (cycles 1, 2) with
  different specific values — no new shape.
- Probe LLM-side role / auditor drift, which requires live calls
  and is explicitly out of scope for this deterministic probe.
- Test long-trajectory drift — a slow-moving version of cycle 1.

Marginal epistemic gain has dropped to roughly zero. Three distinct
failure classes documented (threshold boundary, recovery threshold,
phase-clip suppression) plus one tooling contradiction. Stopping is
honest.
