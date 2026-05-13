> **Mislabelling note (added in semantic-drift audit):** this file
> refers to `birth(B)` throughout. That term was incorrectly bound to
> `confirmed_genuine_en` in the original probe. Paper 0 defines
> `birth(B) = (D, R, F, P, ΔQ)`; the cycle's findings concern composite-EN
> label boundaries, not Paper 0's tuple. See
> `../../semantic_drift_report.md` for the post-mortem. The factual
> content below is preserved verbatim as the historical record.

# Cycle 2 — Recovery dup-delta boundary

## Hypothesis

`compute_novelty_recovery` returns `recovered = True` iff
`dup_delta <= -0.10 AND novel_claims_next >= 1`. A trajectory with a
clean high-ENI EN event (`eni > 0.12`) followed by a smaller but real
duplication drop (e.g. -0.08) and many novel claims (e.g. 6) should be
a birth by any reasonable reading: DES has clearly recovered.
DESi labels it `genuine_transformation_unconfirmed` and birth(B)=0.

## Fixture

`fx2_high_eni_partial_dup_recovery.json`:
- 6 steps.
- 1 EN at loop 2 with `eni_novelty = 0.18` (clearly high).
- `dup_before = 0.42`, `dup_after = 0.34` → `dup_delta = -0.08`
  (just under the -0.10 gate).
- `novel_claims_next = 6` (strong novelty rebound).
- Subsequent steps show sustained recovery (dup drops further,
  novelty stays elevated).

## Prediction

- composite label: `genuine_transformation_unconfirmed`.
- birth(B) = 0.
- Phase III not fired.

## Falsification criterion

Same as cycle 1: if birth(B) = 0 despite a reasonable real-DES
interpretation of "recovery", the boundary is forcing a false
negative.
