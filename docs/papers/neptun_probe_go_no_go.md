# Neptun Probe — Concept Gate Decision

**Status:** decision artifact for the Missing Claim /
Neptun Probe Sprint (v3.73–v3.77). Per the directive's
opening "Keine Papers", this document records ONLY
the concept-gate result. No paper change, no new
failure category.

## Concept Gate evaluation (directive § "Paper-/Concept Gate")

| # | Gate                                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | high_coverage_removal > redundant_removal (v3.73) | >         | **0.0 < 13.37** | ✗ |
| 2 | localization_accuracy (v3.74)                     | >= 0.70   | **1.00**  | ✓ |
| 3 | candidate_match_score (v3.75)                     | >= 0.70   | **1.00**  | ✓ |
| 4 | region_recall (v3.76)                             | >= 0.70   | **1.00**  | ✓ |
| 5 | false_missing_claim_rate (v3.77)                  | <= 0.20   | **0.00**  | ✓ |
| 6 | replay_stability (all sprints)                    | == 1.00   | **1.00**  | ✓ |

Five of six gates pass; gate #1 fails.

## Decision

**Neptun-Hypothese: SCHWACH.** Per the directive's exact
wording — "Wenn eines scheitert: Neptun-Hypothese
schwach. Dokumentieren." — gate #1's empirical failure
keeps the hypothesis at the "weak" status. The audit
records:

* Where DESi can sense missing claims (BRIDGE removal,
  v3.73), it correctly localizes (v3.74), reconstructs
  the structural candidate (v3.75), and recovers the
  region under blind multi-removal (v3.76).
* Negative controls (v3.77) correctly reject noise
  perturbations as non-missing.
* But for HIGH-coverage claims with REDUNDANT
  duplicates, removal produces no perturbation signal
  in this corpus - the corpus's full redundancy on
  high-coverage anchors makes the "high > redundant"
  ordering empirically reversed.

The hypothesis "DESi can infer missing claims from
perturbations" is empirically supported only for
UNIQUE-coverage (bridge-style) claims in this corpus.
For HIGH-coverage claims whose role is replicated by
other anchors, the perturbation signal is masked.

## Sources

* `artifacts/v3_73/report.json`                              — known-claim removal
* `artifacts/v3_73/removal_perturbation.json`                — 4 removal outcomes
* `artifacts/v3_74/report.json`                              — region localization
* `artifacts/v3_74/missing_region_localization.json`         — per-removal centroids
* `artifacts/v3_75/report.json`                              — candidate reconstruction
* `artifacts/v3_75/missing_candidate_reconstruction.json`    — 1 candidate match
* `artifacts/v3_76/report.json`                              — blind recovery
* `artifacts/v3_76/blind_recovery.json`                      — 3 hidden, 2 recovered
* `artifacts/v3_77/report.json`                              — negative controls
* `artifacts/v3_77/missing_claim_negative_controls.json`     — 4 null kinds, 0 false-missing

## Findings the documentation must encode

### 1. Single-anchor removal is masked by redundancy (v3.73)

The v3.50 plateau cohort is fully redundant:

| Role        | Removed    | Coverage Loss | Perturbation |
|-------------|------------|---------------|--------------|
| high_coverage    | v23:R5_04  | 0             | 0.00         |
| low_coverage     | v23:R4_04  | 0             | 0.00         |
| bridge           | v23:R5_02  | 12            | 150.77       |
| redundant        | v314:D02   | 0             | 13.37        |

* HIGH (v23:R5_04, 121 cov) and REDUNDANT (v314:D02,
  also 121 cov, identical coverage set) both lose 0
  coverage on removal - each duplicates the other.
* BRIDGE removal is the only one producing both
  coverage loss (12 leakages) AND a high perturbation
  magnitude (150.77).
* Stop rule per directive: `high_coverage_removal
  (0.0) <= redundant_removal (13.37)` →
  "Hypothese schwach. Dokumentieren, aber weiter."

### 2. Localization works where there is a signal (v3.74)

* Of the 4 removals, only BRIDGE produces an orphan
  signal (12 leakage trajectories).
* The centroid of the 12 orphans is 2.96 units from
  the actual removed bridge anchor in 45-d trajectory
  space.
* Among the 4 test-set anchors, v23:R5_02 is the
  TOP-1 candidate → localization correct.
* `localization_accuracy` = 1.00 (1 of 1 localizable
  removals correctly attributed)

### 3. Candidate reconstruction is feature-exact for the bridge (v3.75)

The BRIDGE reconstruction's 5 structural predictions
each match the actual anchor:

| Feature                       | Predicted | Actual | Match |
|-------------------------------|-----------|--------|-------|
| expected_frame                | 5.0       | 5.0    | YES   |
| expected_support_role         | 0.0       | 0.0    | YES   |
| expected_bridge_role          | True      | True   | YES   |
| expected_coverage_contribution| 12        | 12     | YES   |
| expected_novelty_range        | [5.0,5.0] | 5.0    | YES   |

* `candidate_match_score` = 1.00
* `expected_region_overlap`= 1.00
* `role_reconstruction_accuracy` = 1.00

### 4. Blind multi-claim recovery distinguishes regions (v3.76)

Hidden subset = {BRIDGE, HIGH, REDUNDANT} (3 anchors,
2 distinct coverage regions because HIGH+REDUNDANT
cover the same 121 leakages).

* `orphan_count` = 133 (= baseline coverage size,
  since only LOW remains and LOW covers 0)
* `cluster_count` = 2 (single-link at threshold 1.0:
  one 12-leakage region, one 121-leakage region)
* `missing_count_error` = 0 (predicted distinct
  regions = actual distinct regions)
* `region_recall` = 1.00, `role_recall` = 1.00,
  `false_reconstruction_rate` = 0.00

### 5. Negative controls reject noise (v3.77)

Four null-space perturbation kinds applied to the
test set (no claim removed):

| Kind             | Budget | False Missing | Rejected |
|------------------|--------|---------------|----------|
| random_jitter    | 0.05   | 0             | YES      |
| frame_drift      | 0.10   | 0             | YES      |
| branch_variation | 0.20   | 0             | YES      |
| noise_only       | 0.25   | 0             | YES      |

* `false_missing_claim_rate` = 0.00 (well below the
  0.20 ceiling)
* `noise_rejection_rate` = 1.00
* `null_stability` = 1.00

Noise budgets are chosen to stay below the v3.43
discrimination band (min_manifold_distance = 2.93)
so the controls do not artificially trigger
false-positive missing-claim detections; this is
the boundary at which the "harmless perturbation"
framing of the directive is well-defined.

## Why this is WEAK, not GO

The directive's gate #1 ("high_coverage_removal >
redundant_removal") fails because the v3.50 plateau
cohort is perfectly redundant on high-coverage
anchors. Removing v23:R5_04 (121 coverage) loses 0
coverage because v314:D02 (also 121 coverage,
identical leakage set) is still present. The
directive's expected ordering rests on an assumption
that high-coverage anchors are uniquely high; in
this corpus they are not.

DESi's answer to the directive's closing question
"Kann ich aus Bahnstörungen auf einen fehlenden
epistemischen Planeten schließen?": **partly, only
when the missing planet was uniquely irreplaceable.**
For unique-coverage (bridge-style) claims, the
Neptun-style inference works end-to-end: localization,
candidate reconstruction, blind recovery, and noise
rejection all PASS. For high-coverage claims that
have a duplicate, the system cannot infer their
absence from perturbations because no perturbation
arises.

## What the documentation must NOT claim

* That DESi cannot infer missing claims. The v3.74-
  v3.76 chain shows it CAN, for unique-coverage
  claims.
* That the v3.73 gate failure invalidates the
  Neptun analogy. The analogy may still hold; the
  corpus simply doesn't contain unique-high-coverage
  claims to test against.
* That the gate failure is a NEW failure category.
  The directive explicitly forbids new failure
  categories in this sprint.
* That the negative-control budgets are universally
  correct. The noise budgets here are tuned to the
  v3.50 discrimination band; different corpora may
  require different ceilings to keep the controls
  truly harmless.

## Stop rules and gate signals

* v3.73 `high_coverage_removal (0.0) <=
  redundant_removal (13.37)` **TRIGGERS**. Documented.
  Sprint continues per directive
  ("Dokumentieren, aber weiter").
* v3.74 `localization_accuracy` (1.00) PASS.
* v3.75 `candidate_match_score` (1.00) PASS.
* v3.76 `region_recall` (1.00) PASS.
* v3.77 `false_missing_claim_rate` (0.00) PASS.
* v3.73-v3.77 `replay_stability` (1.00) PASS.
