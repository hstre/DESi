> **Mislabelling note (added in semantic-drift audit):** this file
> refers to `birth(B)` throughout. That term was incorrectly bound to
> `confirmed_genuine_en` in the original probe. Paper 0 defines
> `birth(B) = (D, R, F, P, ΔQ)`; the cycle's findings concern composite-EN
> label boundaries, not Paper 0's tuple. See
> `../../semantic_drift_report.md` for the post-mortem. The factual
> content below is preserved verbatim as the historical record.

# Cycle 1 — High-ENI strict boundary

## Hypothesis

`classify_en_event_composite` uses `eni > ENI_HIGH_THRESHOLD` (strict-greater)
where `ENI_HIGH_THRESHOLD = 0.12`. An EN event with `eni_novelty == 0.12`
exactly is *not* classified as `high`; it falls to `borderline`. Combined
with a strong recovery this produces composite label
`borderline_with_recovery`, not `genuine_transformation_confirmed`. So
`birth(B) = 0` even though the trajectory shows a perfect "high-ENI ⇒
strong recovery" breakthrough pattern.

Paper 0's discussion of the bimodal classifier treats 0.12 as the
*high-side threshold*. The strict-greater implementation excludes the
threshold value itself from being "high". This is a boundary
specification mismatch.

## Fixture

`fx1_eni_eq_high_threshold_with_recovery.json`:
- 6 steps.
- 1 EN event at loop 2 with `eni_novelty = 0.12` exactly.
- Recovery is unambiguous: `novel_claims_next = 5`, `dup_before = 0.40`,
  `dup_after = 0.20` (dup_delta = -0.20, well past the -0.10 gate).

## Prediction

- composite label of the EN event: `borderline_with_recovery`
- birth(B) = 0.
- Phase III not fired (no `genuine_transformation_confirmed`).

## Falsification criterion

The hypothesis is **falsified** iff probe reports birth(B) = 1 on this
fixture (i.e., DESi treats eni=0.12 as "high"). Otherwise birth(B) = 0
is **forced** by a value that Paper 0 treats as on-threshold; the
falsification target is achieved.
