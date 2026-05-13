# Cycle 5 — Add `detect_borderline_chain` diagnostic

## Self-diagnosis

gen11 has 4 borderline ENs in a row (0.11, 0.10, 0.12, 0.11). Composite
labels are `borderline_no_recovery` × 3 + `borderline_with_recovery`.
None of the existing aggregator-level detectors flag this pattern; only
visible by manual inspection of the composite-label list.

## Change

Add `detect_borderline_chain` to `diagnostics.py`. Scans EN events in
order, reports the longest run of consecutive `borderline` legacy-bucket
labels. Fires when run-length >= 3.

New field on `DeterministicMetrics`: `borderline_chain`.
evaluate_suite.py adds `borderline_chain` to detector_hits dict.
Two regression tests assert (a) fires on 4-in-a-row, (b) doesn't fire
on mixed labels.

## Predicted impact

- n=20 borderline_chain fires: 0 → 1 (gen11 only).
- n=10 borderline_chain fires: 0.
- pytest 33 → 35.
