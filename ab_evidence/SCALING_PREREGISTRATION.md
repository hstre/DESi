# Pre-registration: scaling hypothesis test

**Written and committed BEFORE writing any new fixture or running any new A/B.**

## The hypothesis

The interesting thing about DESi state is not compression. It is consolidation: as a research
dialog grows, active decisions/constraints/conflicts converge into a stable set, while the
dialog itself keeps accumulating turns (discussion, dead ends, repetition). Therefore:

1. **State grows sublinearly with chat length** (slope much less than 1).
2. **State-vs-chat ratio falls** as chat length grows.
3. **A→B performance gap widens** with chat length (B's relative advantage grows because A's
   signal-to-noise drops faster than B's).

## Pre-registered predictions

Given case4 measured at chat=4826 / state=1765 / ratio=0.37:

| case | target chat tokens | predicted state tokens | predicted ratio | predicted state growth |
| --- | --- | --- | --- | --- |
| case4 (already measured) | 4826 | 1765 | 0.37 | baseline |
| **case5 (new)** | ~10000 | ~2500 | **~0.25** | ~+40% over case4 |
| **case6 (new)** | ~18000 | ~2700 | **~0.15** | ~+8% over case5 |

If the hypothesis is CORRECT: chat doubles roughly, state grows by tens of percent, ratio falls.

If the hypothesis is WRONG and DESi state just scales linearly with chat content:
state stays around 0.37 × chat for every length → predicted state tokens at 10k = 3700, at 18k = 6660.

## Performance prediction

If the consolidation hypothesis is correct, B's advantage over A should grow with chat length:

- case4 (5k): B beats A by Δdec ~0.20 (Sonnet 4.5 baseline)
- **case5 (10k): B beats A by Δdec ≥ 0.30 predicted**
- **case6 (18k): B beats A by Δdec ≥ 0.40 predicted**

If the gap STAYS FLAT around +0.20 across lengths, the consolidation interpretation is weakened —
B's advantage would be a fixed effect, not a length-dependent one.

## What would falsify the hypothesis

1. State growth: case6 state > 0.30 × case6 chat (state grows linearly, not sublinearly).
2. Performance: case6 Δdec < case4 Δdec (B advantage shrinks at longer length).
3. Both: any case where B is worse than A on decisions.

## Methodological commitments

- Predictions are committed BEFORE writing case5/case6 fixtures.
- New GT will be annotated manually, by the same author, BEFORE running any A/B on it.
- Same Jaccard threshold (0.25). Not tuned per case.
- Same model (Claude Sonnet 4.5 via OpenRouter) for the headline scaling result. A second
  spot-check model (GPT-4o) on case6 only, to confirm the multi-model robustness extends to
  the longest case.
- Hashes for case5 / case6 fixtures will be added to HASHES.txt.
- Negative results (hypothesis falsified) are primary results.
