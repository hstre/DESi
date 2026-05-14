# Cycle 5 — time-to-attention distributions

## Stance

Documentation-only. **No source change in `src/desi/`.** A standalone
analyser computes `latency = first_focus_loop - creation_loop` for
every reconstructed candidate found in each of the three sources:

1. hand-authored adversarial suite (n=10)
2. hand-authored generalization suite (n=20)
3. native DES trajectory (1)

Reports mean / median / variance per source. Sets
`LATENCY_DISTRIBUTION_MISMATCH` per the user's rule:

```
LATENCY_DISTRIBUTION_MISMATCH = TRUE
    iff real_DES_mean > 2 * synthetic_mean
    where synthetic_mean is the (combined or per-suite) mean across
    hand-authored suites.
```

## Predicted outcome

The reconstruction rules from cycles 1 + 2 only fire on operations
carrying a `[hypothesis_builder]` or `[falsifier]` sub-role.
**Hand-authored fixtures do not use this notation** — they emit bare
`Tn` operators only. So `reconstruct_en_candidates` and
`reconstruct_critique_navigation_candidates` will return zero
candidates on the n=10 + n=20 fixtures.

If the rules emit zero candidates on hand-authored, the latency
metric **has no synthetic-side sample to compute mean/median/variance
over**. The comparison is structurally undefined.

The honest interpretation:

- `synthetic_mean` is **undefined**, not zero. Treating it as zero
  triggers division-by-undefined for the `> 2x` rule.
- Per the literal rule wording, undefined denominator → flag is
  undefined, not False.
- The undefinedness IS a finding: the structural mismatch between
  hand-authored and real DES is so deep that even a simple latency
  comparison cannot be set up. Hand-authored fixtures don't model
  per-claim identity-over-time; real DES does.

## What this cycle does NOT do

- Does not invent ENI scores.
- Does not modify any DESi detector or model.
- Does not create candidates on suites where the existing rules
  don't fire — that would be reading the cycle wrongly as "find
  something to compare" rather than "honestly compare what the
  rules produce".

## Stop condition

Single-pass. Stop after writing the report.
