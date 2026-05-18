# T10 — Representational Expansion Trigger — Concept Gate Decision

**Status:** decision artifact for the T10
Activation Sprint (v3.101–v3.104). Per the
opening directive ("Kein Paper", "Keine Synthese
bis v3.104") this document records ONLY the
Concept Gate result; no paper change, no new
failure category, no theory.

## The rule under audit

**T10 — Representational Expansion Trigger.**

> If semantically distinct claim families
> collapse into one operational state, and this
> collapse induces measurable latent
> information loss, DESi may propose exactly
> one additional state dimension — but only if
> historical trajectory geometry remains
> stable.

T10 was specified for the first time in this
sprint. Earlier "T10" usage (`src/desi/
frame_invariance/cases.py:98`) was a
thermodynamic frame-invariance test case, not an
architectural rule. The provenance audit
classified that earlier usage as
``T10_RETROSPECTIVE_INTERPRETATION``.

## Concept Gate evaluation

| # | Gate                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | candidate_auc (v3.101)            | >= 0.70   | **1.000** | ✓ |
| 2 | injected_purity (v3.102)          | >= 0.70   | **1.000** | ✓ |
| 3 | injected_auc (v3.102)             | >= 0.70   | **1.000** | ✓ |
| 4 | gate_flip_count (v3.103)          | == 0      | **0**     | ✓ |
| 5 | historical_auc_delta (v3.103)     | <= 0.05   | **0.494** | ✗ |
| 6 | replay_stability (all four)       | == 1.00   | **1.000** | ✓ |

Five of six gates pass; gate 5 fails because the
counterfactual AUC jump on the entangled pair
(v3.96 ``resolved_auc`` 0.506 → 1.000) is much
larger than 0.05.

## Decision

**Representational Degeneracy = echte
Architekturgrenze (strict reading).** Per the
directive's exact wording — "Wenn eines
scheitert: Representational Degeneracy = echte
Architekturgrenze. Wenn alle bestehen: T10 =
empirisch aktivierter Expansion Trigger." — the
literal failure of gate 5 keeps T10 in the
"proposed but not activated" status.

The mitigating context is intentionally
documented but does NOT override the gate
verdict:

* gate_flip_count = 0 (no historical PASS
  becomes a FAIL under T10).
* The 0.494 ``historical_auc_delta`` is
  concentrated in exactly the three rescue-
  target sprints (v3.94, v3.96 ×2, v3.100)
  that T10 was designed to address; every
  delta is in the beneficial direction.
* Five plateau-anchor sprints (Mozart,
  missing_claim, redundancy_classes,
  doppelgaenger, minimal_features) are
  byte-stable because the +1 dim is a constant
  0 on plateau anchors.
* v3.104 architecture_roi = 27.6.

The strict reading flags T10 as not yet
activatable; the operational reading would
accept it. The directive's letter takes
precedence: **T10 stays in proposed-only
status.**

## Findings the documentation must encode

### 1. The minimal missing dimension is the contradiction marker (v3.101)

Six candidate dimensions enumerated; per-
candidate AUC on the entangled pair:

| Candidate                  | AUC    | Purity | Margin   |
|----------------------------|--------|--------|----------|
| contradiction_type         | 1.000  | 1.000  | +1.930   |
| reasoning_pattern_id       | 0.890  | 0.526  | -0.020   |
| semantic_operator_family   | 0.890  | 0.526  | -0.020   |
| inference_template         | 0.589  | 0.526  | -22.36   |
| claim_structure_hash       | 0.499  | 0.526  | -33.54   |
| premise_dependency         | 0.491  | 0.526  | -0.306   |

* `contradiction_type` is binary:
  1.0 for every G_v316susp anchor (circular
  reasoning pattern), 0.0 for every E_v317h
  anchor (syllogistic pattern).
* Three candidates clear the 0.70 AUC
  threshold but only `contradiction_type` is
  fully separating (purity = 1.0). It is the
  dominant candidate; the next-best AUC is
  0.11 lower.

### 2. One added dimension restores family-pure clustering (v3.102)

Append `contradiction_type` as a single 46th
slot to the entangled pair's residual vectors:

| Metric                       | Value     | Gate         |
|------------------------------|-----------|--------------|
| baseline_dim / injected_dim  | 45 / 46   | (+1 only)    |
| injected_cluster_count       | 2         | (was 1)      |
| injected_cluster_sizes       | (10, 9)   | exact family split |
| injected_purity              | 1.000     | >= 0.70 ✓    |
| injected_auc                 | 1.000     | >= 0.70 ✓    |
| geometry_delta               | 0.463     | (mean pairwise shift) |
| cluster_delta                | +1        | -            |

A single binary slot rescues the entangled
pair's family geometry.

### 3. No historical PASS becomes a FAIL (v3.103)

12 historical gates evaluated under the +1 dim
counterfactual:

| Sprint family               | Flips |
|-----------------------------|-------|
| Plateau-invariant (5)       | 0 unchanged |
| Novel/Frame (3)             | 0 unchanged |
| Entangled rescue (3)        | 3 beneficial |
| Representational rescue (1) | 1 beneficial |
| **Adverse flips**           | **0** |
| **Beneficial flips**        | **4** |

* `gate_flip_count` (adverse) = 0 ✓
* `replay_hash_breakage` = 0 (artifacts on
  disk are frozen).
* `failure_class_delta` = 0.
* `compatibility_score` = 1.000.
* `historical_auc_delta` = 0.494 (driven
  entirely by v3.96 `resolved_auc` flipping
  from 0.506 to 1.000 - the desired effect of
  T10).

### 4. Recovery dwarfs complexity cost (v3.104)

| Metric                | Value     | Notes                   |
|-----------------------|-----------|-------------------------|
| base_state_dim_count  | 9         | DESi's closed enum      |
| state_dim_cost        | 0.100     | 1/(N+1)                 |
| tail_vector_cost      | 0.022     | 1/augmented_dim         |
| compression_delta     | 0.111     | loss of v3.100 compression_gain |
| overfitting_risk      | 0.000     | binary feature, no unique-anchor values |
| recovery_gain         | 1.942     | sum of beneficial deltas (v3.94, v3.96 ×2, v3.100) |
| complexity_cost       | 0.070     | mean of three cost components |
| architecture_roi      | **27.59** | recovery_gain / complexity_cost |

* The +1 dim costs ~0.07 in complexity and
  delivers ~1.94 in recovery - a 27x ROI.
* `overfitting_risk` is 0 because
  `contradiction_type` is binary; the 19
  entangled-pair anchors split into exactly
  two 9-/10-member buckets, so no anchor has a
  unique value to memorise.

## Why this is "Architekturgrenze" under the
## strict letter, "Expansion Trigger" under the
## operational reading

The directive's gate 5 (`historical_auc_delta
<= 0.05`) is written to prevent T10 from
silently moving previously-passing AUCs. In
practice the 0.494 delta is concentrated in
exactly the entangled-pair sprints T10 was
designed to rescue, all in the beneficial
direction. The plateau-anchor sprints
(Mozart, etc.) are byte-stable.

Two readings:

* **Strict (directive letter):** gate 5 fails →
  T10 is not yet activatable; representational
  degeneracy remains a real architectural
  limit.
* **Operational (spirit of the audit):**
  beneficial AUC gains on the rescue targets
  do not count as "drift" because they are the
  desired outcome, and 0 adverse flips means
  no historical work is harmed.

This document records the strict reading. Any
follow-up that would relax gate 5 to "max
ADVERSE AUC delta <= 0.05" would require its
own directive.

DESi's answer to the directive's closing
question "Fehlt mir nur eine Dimension — oder
stoße ich gerade an eine echte epistemische
Architekturgrenze?":
**Eine Dimension reicht messbar, aber unter dem
strengen Directive-Gate bleibt T10 vorgeschlagen,
nicht aktiviert.** The minimal information that
DESi lacks for G/E is the binary
``contradiction_type`` marker. Adding it
mechanically resolves every G/E-derived gate
failure with zero adverse historical flips.
Whether to activate T10 in production now
depends on whether the directive's gate-5
threshold is taken as literal or operational.

## What the documentation must NOT claim

* That T10 has been activated in production.
  T10 is read-only across v3.101–v3.104; the
  9-dim StateVector is unchanged.
* That T10 invalidates the v3.93–v3.96
  decision. v3.96 correctly identified the
  pair as entangled in the 9-dim
  representation; T10's audit shows that a
  10-dim representation would resolve the
  entanglement.
* That T10 invalidates the v3.97–v3.100
  decision. The v3.100 information_loss
  metric was computed against the 9-dim
  representation; under the 10-dim
  counterfactual it would drop to 0 - which is
  exactly what T10's recovery measures.
* That the v2.8 replay hashes (1f4d9dfe44cb16e1,
  d83d81ab8417c022) change. T10 does not
  affect the rule_patch_protocol pipeline;
  v2.8 hashes are unaffected.
* That a new failure category is introduced.
  The directive explicitly forbids new
  failure categories in this sprint.

## Stop rules and gate signals

* v3.101 `candidate_auc` (1.000) PASS.
  Documented.
* v3.102 `injected_purity` (1.000) and
  `injected_auc` (1.000) PASS. Documented.
* v3.103 `gate_flip_count` (0) PASS;
  `historical_auc_delta` (0.494) FAIL under
  strict reading. Documented.
* v3.104 `architecture_roi` (27.59) recorded;
  not a Concept Gate condition but informs
  the decision.
* v3.101–v3.104 `replay_stability` (1.00)
  PASS.

## Sources

* `artifacts/v3_101/report.json`                              — candidate dimension search
* `artifacts/v3_101/t10_dimension_search.json`                — 6 candidates, AUC per candidate
* `artifacts/v3_102/report.json`                              — single-dimension injection
* `artifacts/v3_102/t10_single_dimension_injection.json`      — purity / auc / geometry deltas
* `artifacts/v3_103/report.json`                              — historical compatibility
* `artifacts/v3_103/t10_historical_compatibility.json`        — 12 gates, adverse + beneficial flips
* `artifacts/v3_104/report.json`                              — recovery vs complexity
* `artifacts/v3_104/t10_recovery_vs_complexity.json`          — ROI = 27.59
