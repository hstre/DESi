# Paper 11 — Final Go / No-Go Decision

**Status:** decision artifact for the Predictive
Complementarity Validation Sprint (v3.65–v3.68). The
directive's opening "Paper 11 noch nicht schreiben"
is respected: this document records the final-gate
result, not the paper itself.

## Paper-11 final gate evaluation (directive § "Paper-11 Final Gate")

| # | Gate                                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | auc (v3.65)                                       | >= 0.70   | **1.00**  | ✓ |
| 2 | oos_auc (v3.66)                                   | >= 0.70   | **1.00**  | ✓ |
| 3 | transfer_gap (v3.66)                              | <= 0.20   | **0.00**  | ✓ |
| 4 | best_model includes distance + coverage (v3.67)   | both      | **B_coverage_only** | ✗ |
| 5 | forecast_accuracy (v3.68)                         | >= 0.70   | **0.714** | ✓ |
| 6 | replay_stability (all sprints)                    | == 1.00   | **1.00**  | ✓ |

Five of six gates pass; gate #4 fails.

## Decision

**Paper 11: EXPLORATORY (final-gate NOT met).**

Per the directive's exact wording — "Wenn eines
scheitert: Paper bleibt exploratory." — the failure
of gate #4 keeps Paper 11 at exploratory status. The
v3.67 minimal-predictor sprint identifies
``B_coverage_only`` as the most parsimonious
near-optimum (AUC 1.00 with a single feature). The
directive required the best model to include BOTH
distance AND coverage; in this corpus coverage alone
is sufficient because it is mechanically equivalent
to the resonance definition.

Paper 11 may be written as an exploratory note when
the user requests; this document records the
final-gate result, not the paper.

## Sources

* `artifacts/v3_65/report.json`                       — blind prediction
* `artifacts/v3_65/predictive_activation.json`        — 190 fold records
* `artifacts/v3_66/report.json`                       — OOS transfer
* `artifacts/v3_66/oos_transfer.json`                 — 55 in-sample + 135 oos pairs
* `artifacts/v3_67/report.json`                       — minimal predictor
* `artifacts/v3_67/minimal_predictor.json`            — 4 model evaluations + marginal gains
* `artifacts/v3_68/report.json`                       — causal forecast
* `artifacts/v3_68/activation_forecast.json`          — pre-activation forecast result

## Findings the exploratory note must encode

### 1. Blind prediction is trivially perfect (v3.65)

* Deterministic 67/33 train/test stride split
  (127/63 of the 190 plateau pairs)
* Fisher-style linear discriminant on the 4 features
  (distance, coverage_gain, heterogeneity, diversity)
* `auc` = 1.00 on the held-out test fold
* `precision` = 1.00, `recall` = 1.00, `fpr` = 0.00

The predictor passes Paper-11 final gate #1
trivially because coverage_gain is mechanically
equivalent to the resonance definition.

### 2. OOS transfer is also perfect (v3.66)

* Train on reference-corpus pairs only (v23, v314,
  v315, v316; 55 pairs)
* Test on pairs touching v317 / v317-h / v318-wmf /
  sample (135 pairs)
* `in_sample_auc` = 1.00, `oos_auc` = 1.00
* `transfer_gap` = 0.00

The coverage_gain feature is corpus-invariant by
construction (geometric definition independent of
generative source). Paper-11 final gates #2 and #3
pass.

### 3. Coverage-gain alone is sufficient (v3.67)

| Model                    | Features | AUC   | Marginal |
|--------------------------|----------|-------|----------|
| A_distance_only          | 1        | 0.717 | -        |
| B_coverage_only          | 1        | 1.000 | +0.283   |
| C_distance_and_coverage  | 2        | 1.000 | 0.000    |
| D_all_features           | 4        | 1.000 | 0.000    |

* `best_model` = `B_coverage_only` (parsimony
  tie-break at AUC 1.00)
* `best_model_features` = (coverage_gain,)
* Paper-11 final gate #4 **FAILS** — the best model
  does NOT include distance.

This is the gate failure. The directive expected the
distance feature to add marginal predictive value
above coverage; empirically it does not. Distance
alone reaches AUC 0.717 (just above the directive's
0.70 floor) but loses entirely once coverage_gain is
available.

### 4. Pre-activation forecast is usable but weaker (v3.68)

* Pre-activation features only: distance,
  heterogeneity, diversity (coverage_gain excluded
  as post-activation)
* `forecast_accuracy` = 0.714
* `calibration_error` = 0.063
* `early_warning_steps` = 4 (the trajectory has 4
  pre-audit states; the forecast is available at
  state index 0)
* Underlying AUC drops to 0.674 (below the 0.70
  floor) but accuracy at the trained threshold is
  0.714 (above the floor)

Paper-11 final gate #5 passes by accuracy, not by
AUC. The forecast is usable but not as strong as the
post-activation predictor.

## Why this is EXPLORATORY, not NO-GO

The directive's gate language is strict: ONE failure
keeps the paper at exploratory status. Gate #4 is the
only failure, and it has a clear explanation:

* The v3.67 ablation reveals that the v3.61–v3.64
  complementarity framing is REDUCIBLE to the
  trivial coverage_gain > 0 rule in this corpus.
* coverage_gain is necessary by construction (v3.64
  finding); the explanatory layers (distance,
  heterogeneity, diversity) ADD information about
  why the coverage gap exists but do NOT add
  predictive value on top.
* Distance alone hits AUC 0.717 (just above floor)
  but is dominated entirely by coverage_gain.

The honest exploratory note should therefore say:

> Pair resonance is fully predictable from a single
> geometric feature (coverage_gain); the
> complementarity framing in v3.61–v3.64 is
> explanatory rather than predictive on this corpus.

Paper 11, if written as an exploratory note, must
include this distinction.

## What the exploratory note must NOT claim

* That distance + coverage is the minimal sufficient
  predictor. v3.67 shows coverage alone reaches the
  same AUC.
* That the complementarity framing has predictive
  value beyond the coverage_gain rule. v3.67's
  marginal_gain row pins this at 0.0.
* That the v3.65/v3.66 perfect AUC reflects deep
  generalisation. It reflects the mechanical
  equivalence of coverage_gain to the resonance
  definition; any predictor including coverage_gain
  on a sufficiently-large corpus would be perfect.
* That the forecast (v3.68) generalises beyond this
  corpus. The pre-activation forecast hits accuracy
  0.714, just above the floor; the underlying AUC
  0.674 is below the floor. The forecast is at the
  weakest end of "usable".

## Stop rules not triggered (and the one that was)

* v3.65 `replay_stability` (1.00) PASS.
* v3.65 `auc` (1.00) PASS the >= 0.70 floor.
* v3.66 `replay_stability` (1.00) PASS.
* v3.66 `oos_auc` (1.00) PASS the >= 0.70 floor.
* v3.66 `transfer_gap` (0.00) PASS the <= 0.20
  ceiling.
* v3.67 `replay_stability` (1.00) PASS.
* v3.67 `best_model` (B_coverage_only) **FAIL** —
  does NOT include the distance feature, so the
  directive's Paper-11 final gate #4 fails.
* v3.68 `forecast_replay_stability` (1.00) PASS.
* v3.68 `forecast_accuracy` (0.714) PASS the
  >= 0.70 floor.

## Next direction (out of scope for this document)

A future sprint may:

1. **Re-define complementarity beyond coverage_gain.**
   The v3.61–v3.64 framing identified four
   explanatory factors but v3.67 shows coverage_gain
   subsumes all predictive value. A re-framing could
   ask: what makes a pair have coverage_gain > 0?
   That is the deeper question.
2. **Test the forecast on truly held-out trajectories
   from outside the v2/v3 universe** (e.g. a v4
   probe corpus). v3.66's OOS test is still inside
   the same generative process.
3. **Decompose coverage_gain into its components.**
   coverage_gain = |A ∪ B| - max(|A|, |B|). The
   components |A| and |B| depend on per-anchor
   reach (related to distance), so the predictive
   role of distance may be hidden inside
   coverage_gain. A causal model that separates
   anchor reach from pair overlap could restore
   distance as an explicit predictor.
4. **Probe the gate-#4 question via constrained
   prediction.** Train a model that uses distance
   ONLY when coverage_gain is non-trivial (e.g. a
   threshold-gated predictor that uses distance
   to decide when coverage_gain is reliable). This
   might surface distance's marginal contribution
   in a non-redundant way.
