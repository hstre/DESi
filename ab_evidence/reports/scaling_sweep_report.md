# Scaling Sweep — testing the consolidation hypothesis

The brief tested two claims:

1. **State grows sublinearly with chat length.**
2. **A→B preservation gap widens with chat length.**

This run measures both across case4 (4618 chat tok), case5 (7012), case6 (9439).

## Pre-registered predictions (committed in commit `142cf1d` BEFORE this run)

| case | predicted state | predicted ratio | actual state | actual ratio | verdict on prediction |
| --- | --- | --- | --- | --- | --- |
| case4 (baseline) | 1765 | 0.37 | 1765 | 0.382 | — |
| case5 | ~2500 | ~0.25 | 2457 | 0.350 | **partially wrong** (state right, ratio higher than predicted) |
| case6 | ~2700 | ~0.15 | 3465 | 0.367 | **wrong on both** (state +28%, ratio essentially flat) |

## Finding 1 — state grows ~linearly with the number of independent items

Per-GT-item, the state is consistently ~41 tokens across all three cases:

| case | chat tokens | state tokens | GT items | tokens/item |
| --- | --- | --- | --- | --- |
| case4 | 4618 | 1765 | 42 | 42.0 |
| case5 | 7012 | 2457 | 60 | 41.0 |
| case6 | 9439 | 3465 | 85 | 40.8 |

**The consolidation prediction is refuted at this scale.** State grows with the count of distinct
active items, not sublinearly with chat length. The dialog adds new decisions/constraints as it
grows; those new items must be stored, and the state grows accordingly.

The chat-to-state ratio is roughly STABLE around 0.35–0.38 across the three cases — not falling,
not rising. This means **token savings stay constant in proportion (~65%), not amplifying with
length**. The earlier inventory data (corr 0.9997 raw vs savings) reflected the same constant
proportion, not consolidation.

This honestly refutes my own interpretation in the prior message ("Bei 50.000 Tokens: erheblich.
Bei 500.000 Tokens: möglicherweise dramatisch."). The current evidence does NOT support that the
ratio falls at longer lengths. It supports that the ratio is approximately **constant**, set by
how densely a research dialog packs new active items per token of discussion.

## Finding 2 — A→B preservation gap, by case and model

| case | model | Δ dec | Δ cons | Δ conf | Δ claim | Δ q | input reduction |
| --- | --- | --- | --- | --- | --- | --- | --- |
| case4 | claude-sonnet-4.5 | +0.200 | +0.000 | +0.333 | +0.125 | +0.250 | 68.9% |
| case5 | claude-sonnet-4.5 | +0.182 | +0.059 | +0.500 | +0.545 | +0.000 | 72.4% |
| case6 | claude-sonnet-4.5 | **−0.215** | **−0.586** | +0.400 | +0.214 | +0.000 | 72.0% |
| case6 | gpt-4o | +0.607 | +0.586 | +0.800 | +0.786 | +0.556 | 73.1% |

**Sonnet 4.5: gap shrinks then INVERTS.** At case6 (9.4k chat / 85 GT items), B loses to A on
both decisions and constraints. Variance examination shows Sonnet's B response on case6 was
heavily **abbreviated** — it summarized constraints into one-line clusters like
`"p99 <50ms, p50 <10ms online latency (R1)"` and only listed 9 of 29 constraints explicitly.
Many "missing" items are arguably present in compressed form but fall below the Jaccard 0.25
threshold. This is partially an evaluator artifact (paraphrase-blind) and partially a real
Sonnet behavior (it self-truncated under length pressure when given the dense state).

**GPT-4o on the same case6: gap WIDENS dramatically.** Δdec +0.607, Δcons +0.586, Δclaim
+0.786. A's responses were short and missed most items; B's were thorough. The model effect is
large.

## Verdict on the two pre-registered predictions

1. **Sublinear state growth: REFUTED at this scale.** State grows linearly with the count of
   active items. Ratio stays ~0.35–0.38.
2. **A→B gap widens with length: NOT CONFIRMED on Sonnet 4.5** (gap shrinks and inverts on
   case6). **Confirmed for GPT-4o** at the long case where its A performance collapses, but
   that's the wrong frame: GPT-4o's A is bad at all lengths.

## What the data DOES still support

- **Token savings stay around 67–73% across all measured lengths.** That's not nothing.
- **B does not introduce more hallucinations.** At every length and every model B has fewer
  hallucinations than A.
- **At longer chat length, A's preservation drops faster than B's on most metrics for most
  models.** Even Sonnet's case6 result shows A also dropped on decisions and claims; B's case6
  drop was sharper but from a higher starting point.

## Honest reading

The simple version of the consolidation thesis (state stays small, savings amplify, gap widens)
is not what the data shows. The honest version is:

- State scales with **information density**, not with **chat length** (state/items ratio constant).
- The token-saving effect (~65–70%) is roughly **constant by proportion**, not amplifying.
- A→B preservation advantage is **real but model-dependent**. Strong on weak/short-output models
  (GPT-4o, Llama 3.3, Mistral); modest on careful/verbose models (Sonnet); on the longest case
  it can invert on the careful model if it self-summarizes the structured state.
- The interesting effect at length may NOT be "B wins by more" but **"B becomes the only viable
  context"** — at 50k+ tokens, A would hit context limits or get sloppy, but B stays small.
  That regime is not measured here.

## Methodological notes

- Pre-registration committed BEFORE the run (commit `142cf1d`).
- Same evaluator, same Jaccard threshold (0.25), same prompts.
- Ground truth for case6 is a superset of case5 which is a superset of case4. New items are
  added in later phases; old items remain active unless the dialog explicitly replaces them.
- GPT-4o spot-check on case6 only. Spot-check confirms the case6 Sonnet result is model-
  specific, not a fundamental property of DESi at length.

## Caveats

- N=3 cases × 1 main model + 1 spot-check is small.
- 9k tokens is not 50k. The real test of consolidation behavior is in the regime where A hits
  context limits.
- The evaluator's paraphrase-blindness affects all cases equally but matters more when models
  self-summarize structured input (the case6 Sonnet pathology).
- Sonnet's verbose / compressing behavior may be unique to its training. Other Claude sizes
  (Opus, Haiku) might show different patterns at case6.
- The pre-registered chat-token targets (~10k, ~18k) were missed — I overestimated content
  density when writing the dialogs. Actual case5 = 7012, case6 = 9439. The scaling test is
  weaker than intended; honest result is reported either way.
