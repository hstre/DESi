# Representational Degeneracy — Concept Gate Decision

**Status:** decision artifact for the
Representational Degeneracy Audit (v3.97–v3.100).
Per the opening directive ("Kein Paper", "Keine
Synthese bis v3.100") this document records ONLY
the Concept Gate result; no paper change, no new
failure category, no theory.

## Question

> Sind epistemische Doppelgänger intelligente
> Kompression — oder verliere ich gerade etwas,
> das ich noch nicht sehe?

The entangled pair under audit is **G_v316susp**
(9 anchors) and **E_v317h** (10 anchors) from
v3.93.

## Concept Gate evaluation

| # | Gate                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | semantic_distance (v3.97)         | > 0       | **0.990** | ✓ |
| 2 | verdict_overlap (v3.98)           | >= 0.90   | **1.000** | ✓ |
| 3 | separation_rate (v3.99)           | < 0.20    | **0.000** | ✓ |
| 4 | information_loss (v3.100)         | <= 0.10   | **0.500** | ✗ |
| 5 | predictive_delta (v3.100)         | <= 0.10   | **0.000** | ✓ |
| 6 | replay_stability (all four)       | == 1.00   | **1.000** | ✓ |

Five of six gates pass; gate 4 fails.

## Decision

**Degeneracy = potenzieller Informationsverlust.**
Per the directive's exact wording — "Wenn eines
scheitert: Degeneracy = potenzieller
Informationsverlust." — the failure of gate 4
keeps the representational-degeneracy hypothesis
at the "potential information loss" status. The
audit records:

* The two families are essentially completely
  disjoint at the text level (v3.97: semantic
  distance 0.990, concept divergence 1.000,
  unique-vocabulary fraction > 95 %).
* Under the current DESi downstream pipeline they
  produce IDENTICAL outcomes on every audited
  axis (v3.98: 8/8 axes at overlap 1.000).
* Five perturbation kinds across seven magnitudes
  (35 cells) cannot separate them: the coupling
  is stable, not just at equilibrium (v3.99:
  separation_rate 0, chaos_threshold = -1
  sentinel).
* Under the upper-bound diversity model the
  degenerate representation locks off 50 % of
  the (family x downstream outcome) cells that a
  family-aware representation could in principle
  produce (v3.100: information_loss 0.5,
  reasoning_delta 0.5). Predictive AUC on the
  current downstream-verdict task is unchanged
  (predictive_delta 0.0), so the loss is not yet
  observable in any production metric.

## Findings the documentation must encode

### 1. Semantic divergence is essentially total (v3.97)

| Metric                    | Value                                  |
|---------------------------|----------------------------------------|
| semantic_distance         | 0.990                                  |
| semantic_overlap          | 0.010 (unigram 0.016, bigram 0.005)    |
| concept_divergence        | 1.000 (total-variation, maximal)       |
| family_uniqueness G       | 0.96 (96 % of G's vocabulary unique)   |
| family_uniqueness E       | 0.97 (97 % of E's vocabulary unique)   |
| dominant_concept G        | circular_reasoning (9/9)               |
| dominant_concept E        | universal_syllogism (6/10), post_hoc_narrative (4/10) |

* G_v316susp is uniformly circular ("X PRED Y. Y
  PRED X. Therefore ...").
* E_v317h splits between syllogisms ("All X are
  Y. Z is X. Therefore Z is Y.") and post-hoc
  narratives ("Event A. Event B. Therefore A
  caused B.").
* The two families share none of their reasoning
  templates and almost none of their vocabulary.

### 2. Downstream effects are perfectly equivalent (v3.98)

Eight audited downstream axes, each measured as
the fraction of cross-family pairs (G × E) that
agree on that axis:

| Axis                      | Overlap |
|---------------------------|---------|
| final_verdict             | 1.000   |
| rescue_eligible           | 1.000   |
| intervention_kind         | 1.000   |
| failure_class             | 1.000   |
| audit_outcome             | 1.000   |
| branch_path               | 1.000   |
| support_path              | 1.000   |
| rollback_required         | 1.000   |
| **outcome_divergence**    | **0.000** |

Every G/E pair maps to the same final verdict
(LOGICALLY_REJECTED), the same intervention
(REJECT), the same failure class (AUDIT_LOSS),
and the same rescue/rollback flags.

### 3. The coupling is stable under perturbation (v3.99)

35 cells (5 perturbation kinds × 7 magnitudes
including a zero-magnitude control). Per-anchor
sha256-derived noise is added to the targeted
dimension across the 5 trajectory states; we
re-measure pairwise AUC against the same_family
label.

| Metric                    | Value     | Gate           |
|---------------------------|-----------|----------------|
| baseline_auc              | 0.491     | -              |
| perturbation_divergence   | 0.014     | -              |
| separation_rate           | 0.000     | < 0.20 ✓       |
| coupling_stability        | 1.000     | -              |
| chaos_threshold           | -1.0      | (no threshold) |

* The strongest perturbation kind is
  ``frame_id`` (AUC peaks at 0.535 at magnitude
  5.0) but no cell crosses the 0.70 separation
  threshold.
* `chaos_threshold = -1.0` is a sentinel
  indicating no magnitude was found that could
  separate the two families.

### 4. The degenerate representation locks off half the reasoning space (v3.100)

| Metric                           | Value     | Gate           |
|----------------------------------|-----------|----------------|
| dim_a / dim_b                    | 46 / 45   | -              |
| distinct_point_count_a           | 9         | -              |
| distinct_point_count_b           | 8         | -              |
| collapsed_anchor_count           | 13/19     | -              |
| compression_gain                 | 0.111     | -              |
| information_loss                 | 0.500     | <= 0.10 ✗      |
| reasoning_delta                  | 0.500     | -              |
| predictive_delta                 | 0.000     | <= 0.10 ✓      |
| failure_class_delta              | 0.000     | -              |
| downstream_verdict_set_b         | {LOGICALLY_REJECTED} (singleton) |
| downstream_intervention_set_b    | {REJECT} (singleton)             |
| downstream_failure_class_set_b   | {AUDIT_LOSS} (singleton)         |

* `compression_gain` is small (11 %) because the
  one-hot family_id only adds a single
  dimension.
* `information_loss = 0.5` reflects the
  upper-bound diversity model: representation A
  could in principle assign one downstream tuple
  per (family × current-outcome) cell that
  representation B cannot, so half of the
  representational reasoning space is locked.
* `predictive_delta = 0.0` because the current
  production downstream logic emits a single
  verdict for the entangled pair regardless of
  representation - there is no measurable AUC
  difference today.
* `failure_class_delta = 0.0` for the same
  reason.

## Why this is POTENTIAL LOSS, not USEFUL COMPRESSION

The directive's six conditions split into:

* **Pass:** gates 1 (semantic distance), 2
  (verdict overlap), 3 (separation rate), 5
  (predictive delta), 6 (replay stability).
* **Fail:** gate 4 (information loss).

Under the directive's exact stricter clause -
"Wenn getrennte Repräsentation bessere
Entscheidungen ermöglicht, gilt Degeneracy als
Informationsverlust - auch wenn aktuelle DESi-
Metriken zunächst gleich bleiben" - the
information-loss metric is computed against the
upper-bound family-aware diversity, not the
current production diversity. Under that
stricter standard, the degenerate representation
fails gate 4.

The pragmatic outcome is mixed: in the current
DESi pipeline the collapse is harmless
(predictive_delta 0, failure_class_delta 0,
verdict_overlap 1) and saves a one-hot dimension
per anchor. But the moment downstream logic
evolves to consult family-level structure (a
"break the cycle" intervention for circular
reasoning, a "verify premise" intervention for
syllogisms) the degeneracy will become a hard
ceiling: the representation cannot distinguish
inputs that the new logic would need to
distinguish.

DESi's answer to the directive's closing
question "Sind epistemische Doppelgänger
intelligente Kompression — oder verliere ich
gerade etwas, das ich noch nicht sehe?":
**Aktuell intelligente Kompression, perspektivisch
potenzieller Informationsverlust.** The collapse
is benign for today's pipeline and dangerous for
any future pipeline that would route the two
families differently.

## What the documentation must NOT claim

* That the degeneracy is currently breaking
  anything. v3.98 records perfect downstream
  equivalence and v3.99 records stable coupling
  under perturbation.
* That representation A is the "correct"
  representation. Representation A is a
  conservative upper bound used to compute
  information_loss; it is not a recommendation
  to add a family_id channel to the
  StateVector.
* That the v3.93-v3.96 entangled-family
  decision changes. The conclusion that G and E
  are true epistemic doppelgangers in DESi's
  representation still stands; v3.97-v3.100
  simply audits whether that fact is a benign
  compression or a hidden loss.
* That the v3.96 hash-seed determinism patch
  affects this audit. The patch made the
  pipeline deterministic without changing what
  it represents; the entangled pair's
  signatures are byte-identical before and
  after.
* That a new failure category is introduced.
  The directive explicitly forbids new failure
  categories in this sprint.

## Stop rules and gate signals

* v3.97 ``semantic_distance`` (0.990) and
  ``concept_divergence`` (1.000) PASS the
  distinctness criterion. Documented.
* v3.98 ``verdict_overlap`` (1.000) and seven
  more axis overlaps at 1.000 PASS the
  equivalence criterion. Documented.
* v3.99 ``separation_rate`` (0.000) and
  ``chaos_threshold`` (-1.0 sentinel) PASS the
  stability criterion. Documented.
* v3.100 ``information_loss`` (0.500) FAILS
  the loss-ceiling criterion;
  ``predictive_delta`` (0.000) PASSES.
  Documented.
* v3.97-v3.100 ``replay_stability`` (1.00)
  PASS.

## Sources

* `artifacts/v3_97/report.json`                              — semantic loss audit
* `artifacts/v3_97/semantic_loss_audit.json`                 — concept assignments per anchor
* `artifacts/v3_98/report.json`                              — downstream equivalence
* `artifacts/v3_98/downstream_equivalence.json`             — 8-axis overlaps + 19 signatures
* `artifacts/v3_99/report.json`                              — counterfactual divergence
* `artifacts/v3_99/counterfactual_divergence.json`          — 35-cell perturbation grid
* `artifacts/v3_100/report.json`                             — compression vs information loss
* `artifacts/v3_100/compression_vs_information_loss.json`   — full structural comparison
