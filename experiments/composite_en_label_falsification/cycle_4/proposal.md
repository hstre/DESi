> **Mislabelling note (added in semantic-drift audit):** this file
> refers to `birth(B)` throughout. That term was incorrectly bound to
> `confirmed_genuine_en` in the original probe. Paper 0 defines
> `birth(B) = (D, R, F, P, ΔQ)`; the cycle's findings concern composite-EN
> label boundaries, not Paper 0's tuple. See
> `../../semantic_drift_report.md` for the post-mortem. The factual
> content below is preserved verbatim as the historical record.

# Cycle 4 — Metric contradiction: evaluator references phantom composite labels

## Hypothesis

`experiments/generalization_loop/evaluate_suite.py` defines a
`detector_hits` dict that includes keys
`any_recovered_after_high_eni` and `any_stuck_high_eni`. These keys
check for the strings `"recovered_after_high_eni"` and
`"stuck_high_eni"` in `composite_labels`. But `classify_en_event_composite`
NEVER produces either string — its 6-label set is:

- `genuine_transformation_confirmed`
- `genuine_transformation_unconfirmed`
- `borderline_with_recovery`
- `borderline_no_recovery`
- `low_eni_with_unexpected_recovery`
- `false_return_confirmed`

So `any_recovered_after_high_eni` and `any_stuck_high_eni` are
**unreachable** — they evaluate to False for every possible
trajectory. This is a **spec-vs-implementation contradiction
in the evaluator itself**: the evaluator was authored against a
label set that doesn't match the classifier.

## Why this is a birth(B) falsification

If birth(B) were extended to include any one of these phantom
labels (a not-unreasonable Paper-0 interpretation of "the
trajectory had recovery after a high-ENI moment"), then no
fixture in any suite would ever satisfy it. birth(B) under that
interpretation is **always 0**.

## Falsification criterion

A scan across both committed suites should produce **zero**
fixtures with `any_recovered_after_high_eni = True` or
`any_stuck_high_eni = True`. If true, the keys are dead.
