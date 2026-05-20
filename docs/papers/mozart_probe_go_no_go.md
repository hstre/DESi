# Mozart Probe — Historical Go / No-Go Decision

**Status:** decision artifact for the Mozart Coverage
Audit Sprint (v3.69–v3.72). Per the directive's
opening "Paper 11 bleibt exploratory" / "Keine neuen
Failure Categories", this document records ONLY whether
the historical Mozart probe earns a note-eintrag in the
exploratory Paper 11. It does not change Paper 11's
exploratory status or open a new failure category.

## Historical gate evaluation (directive § "Paper-11 Historical Gate")

| # | Gate                                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | mozart coverage_percentile (v3.69)                | >= 0.90   | **1.00**  | ✓ |
| 2 | input_specificity (v3.70)                         | > 0       | **0.85**  | ✓ |
| 3 | new_regions (v3.71)                               | > 0       | **2**     | ✓ |
| 4 | forecast_margin (v3.72)                           | > 0       | **1.00**  | ✓ |
| 5 | replay_stability (all sprints)                    | == 1.00   | **1.00**  | ✓ |

All five historical gates pass.

## Decision

**Mozart probe: NOTE-EINTRAG.** Mozart earns a
historical-note entry in the exploratory Paper 11. Per
the directive's exact wording — "Wenn eines scheitert:
Mozart bleibt nur nette Anekdote. ... Nur historischer
Note-Eintrag wenn: ..." — every gate must be met to
upgrade Mozart from anecdote to documented finding.

Paper 11 itself remains EXPLORATORY (v3.65–v3.68 final
gate not met). This sprint adds a Mozart-specific
historical note within the exploratory framing; it
does not promote Paper 11 to non-exploratory.

## Sources

* `artifacts/v3_69/report.json`                       — coverage reconstruction
* `artifacts/v3_69/mozart_coverage.json`              — 3 probe coverages + timelines
* `artifacts/v3_70/report.json`                       — counterfactual swap
* `artifacts/v3_70/mozart_counterfactual.json`        — 5 random + 2 historical substitutes
* `artifacts/v3_71/report.json`                       — coverage source
* `artifacts/v3_71/mozart_region_map.json`            — state + transition regions
* `artifacts/v3_72/report.json`                       — predictive forecast
* `artifacts/v3_72/mozart_forecast.json`              — pre-activation forecast summary

## Findings the historical note must encode

### 1. Mozart is a strict coverage maximum (v3.69)

* `coverage_by_probe` = {mozart: 19.8, darwin: 14.4,
  kant: 0.0 (missing)}
* `coverage_percentile (mozart)` = 1.00 (strict max
  among 395 trajectories)
* `gap_events_by_probe` = {mozart: 2, darwin: 1,
  kant: 0}
* `bridge_by_probe` = {all 0}
* sample:n03_kant is documented missing; not
  substituted (per directive).

Mozart's trajectory length (8) is above the median (5),
its distinct frame count (>= 3 across hash seeds) is
above the median (2), its novelty range (12.0) is above
the median (5.0), and its anchor_density_range (0.80)
is uniquely non-zero in the corpus. The composite
coverage_score is the strict corpus maximum.

### 2. Mozart is input-specific (v3.70)

| Substitute        | Coverage | Loss  | Relative |
|-------------------|----------|-------|----------|
| Mozart (baseline) | 19.8     | 0.00  | 0.00     |
| Darwin            | 17.3     | 2.5   | 0.13     |
| Kant              | missing  | 19.8  | 1.00     |
| Random control 1  | 3.0      | 16.8  | 0.85     |
| Random control 2  | 1.3      | 18.5  | 0.93     |
| Random control 3  | 3.0      | 16.8  | 0.85     |
| Random control 4  | 3.0      | 16.8  | 0.85     |
| Random control 5  | 3.0      | 16.8  | 0.85     |

* `input_specificity` = 0.85 (Mozart strictly above
  every random control by at least 70%; comparator
  restricted to random controls to avoid the v3.32
  FrameDetector hash-seed jitter that affects the
  Mozart-vs-Darwin margin)

### 3. Mozart opens new claim regions structurally (v3.71)

* `mozart_state_regions` = 4 distinct (frame, support)
  pairs
* `mozart_transition_regions` = 6 adjacent state-pair
  patterns
* `new_regions` = 2 (varies 1..5 across hash seeds;
  always strictly positive)
* `overlap_with_controls` = 0.67
* `coverage_source` = "structural" (stable across hash
  seeds; Mozart's structural axis dominates the
  semantic axis under axis-normalisation)
* `novelty_type_by_probe` = {mozart: structural,
  darwin: structural, kant: missing}

Mozart's coverage comes primarily from frame-transition
patterns, not from semantic novelty alone.

### 4. Mozart is forecastable from state[0] (v3.72)

* `max_novelty_at_zero` = 12.0
* `mozart_forecast_score` = 1.00 (strict max)
* `darwin_forecast_score` = 0.917
* All 5 random control forecast scores = 0.00 (their
  state[0].novelty is 0)
* `forecast_margin` = 1.00
* `calibration_error` = 0.00

A single pre-activation feature (state[0].novelty)
flags Mozart as a coverage outlier before the
trajectory unfolds. Darwin is also flagged (margin
0.92). Random controls are correctly ranked at the
bottom.

## Why this is a NOTE, not a paper revision

The directive's gate language is strict: ALL five
historical gates must pass for a note-eintrag. They do.
But the broader Paper 11 final gate (v3.65–v3.68) is
NOT changed by this audit — the v3.67 finding that
coverage_gain alone subsumes all predictive value for
the v3.50 resonance phenomenon stands.

The Mozart note documents a SEPARATE phenomenon: a
single trajectory in the sample corpus that was
historically flagged by Steffen's intuition. The
audit confirms:

1. Mozart was empirically a coverage outlier.
2. The outlier status is input-specific (substituting
   random controls loses ~85% of coverage).
3. The outlier opens structural claim regions
   (frame-transition patterns absent from the rest
   of the corpus).
4. The outlier is detectable PRE-ACTIVATION from a
   single state[0].novelty feature.

DESi's answer to the directive's closing question
"War Mozart nur Steffens Bauchgefühl — oder ein
früher Coverage-Trigger?": ein früher Coverage-
Trigger. The intuition was correct; the structural
signature is detectable in the post-hoc audit AND in
the pre-activation forecast.

## What the historical note must NOT claim

* That Mozart is a new failure category. The
  directive explicitly forbids new failure
  categories.
* That the Mozart audit changes Paper 11's
  exploratory status. The v3.65-v3.68 final gate
  still controls Paper 11.
* That the forecast (v3.72) generalises beyond the
  Mozart/Darwin pair. The state[0].novelty = 12.0
  threshold is met by Mozart only; Darwin (11.0) is
  the next-highest and other trajectories drop to
  0.0. The forecast is essentially a Mozart
  detector, not a general coverage-outlier
  detector.
* That kant's absence is a problem. The directive
  required documentation of missing probes
  ("Dokumentieren. Nicht ersetzen.") — done.
* That Mozart's MID_RUN_GAP pattern (2 consecutive
  GAP_DETECTED visits) is the source of its
  coverage. v3.71 shows the dominant source is
  structural (frame transitions), not the gap
  events themselves.

## Stop rules not triggered

* v3.69 `replay_stability` (1.00) PASS.
* v3.69 `mozart_coverage_percentile` (1.00) >= 0.90.
* v3.70 `replay_stability` (1.00) PASS.
* v3.70 `input_specificity` (0.85) > 0.
* v3.71 `replay_stability` (1.00) PASS.
* v3.71 `new_regions` (2; jitters 1..5) > 0.
* v3.72 `replay_stability` (1.00) PASS.
* v3.72 `forecast_margin` (1.00) > 0.
