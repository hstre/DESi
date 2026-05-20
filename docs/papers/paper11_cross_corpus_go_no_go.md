# Paper 11 — Cross-Corpus Go / No-Go Decision

**Status:** decision artifact for the Cross-Corpus
Semantic Field Validation Sprint (v3.53–v3.56). The
directive's opening "Paper 11 weiterhin pausiert" is
respected: this document records the cross-corpus
result, not the paper.

## Paper-11 v2 Gate evaluation (directive § "Paper-11 Gate")

| # | Gate                                  | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | radius_transfer_rate (v3.53)          | >= 0.75   | **1.00**  | ✓ |
| 2 | pair_transfer_rate (v3.54)            | >= 0.75   | **0.00**  | ✗ |
| 3 | anti_anchor_transfer_rate (v3.55)     | >= 0.75   | **1.00**  | ✓ |
| 4 | phase_transfer_rate (v3.56)           | >= 0.75   | **1.00**  | ✓ |
| 5 | replay_stability (all sprints)        | == 1.00   | **1.00**  | ✓ |

Four of five gates pass; gate #2 (pair resonance)
fails.

## Decision

**Paper 11: NO-GO.**

Per the directive's exact wording — "Wenn eines
scheitert: Semantic Coupling bleibt corpus-lokal.
Kein Paper." — a single failing gate is sufficient
to deny Paper 11. The v3.50 pair-resonance phenomenon
is corpus-local; it does not survive per-corpus
replay.

Paper 11 remains paused. The other three sprints
(radius, anti-anchor, phase) reproduce their
respective v3.49–v3.52 findings inside every
reference corpus and are NOT the blocker.

## Sources

* `artifacts/v3_53/report.json`                    — radius transfer
* `artifacts/v3_53/cross_corpus_radius.json`       — 4 corpora × 6 masks
* `artifacts/v3_54/report.json`                    — pair transfer
* `artifacts/v3_54/cross_corpus_resonance.json`    — per-corpus pair matrices
* `artifacts/v3_55/report.json`                    — anti-anchor transfer
* `artifacts/v3_55/cross_corpus_anti_anchor.json`  — 4 per-corpus suppression records
* `artifacts/v3_56/report.json`                    — phase transfer
* `artifacts/v3_56/cross_corpus_phase.json`        — per-corpus phase curves

## Reference corpus inventory

| Corpus | Trajectories | Plateau | Leakage |
|--------|-------------:|--------:|--------:|
| v23    | 30           | 6       | 12      |
| v314   | 60           | 3       | 30      |
| v315   | 100          | 1       | 24      |
| v316   | 100          | 1       | 24      |

All four directive-named corpora are present in the
data. No substitution was required.

## Findings the paper must encode (when the gate
re-passes)

### 1. Radius transfer holds in every corpus (v3.53)

* `radius_transfer_rate` = 1.00
* Per-corpus `corpus_radius_breaks`: `{v23: True,
  v314: True, v315: True, v316: True}`
* Per-corpus `corpus_critical_radii`: all `"4"` in the
  closed `RADII` set
* Per-corpus `artifact_likelihoods`: all 0.20 (only
  `support_only` collapses; frame masks survive
  everywhere)

The v3.44 step function is a corpus-invariant
geometric property. The transition from
no-leakage to full-leakage happens between r=2.0 and
r=4.0 in every reference corpus.

### 2. Pair resonance is a cross-corpus aggregation artifact (v3.54)

* `pair_transfer_rate` = 0.00 (FAILING gate)
* `eligible_corpora` = (v23, v314); v315 and v316
  each have only 1 plateau anchor and cannot form
  pairs
* Per-corpus `resonance_pairs_per_corpus`:
  `{v23: 0, v314: 0}`
* Per-corpus `control_pairs_per_corpus`:
  `{v23: 0, v314: 0}`
* Per-corpus `subadditivity_per_corpus`:
  `{v23: 0.30, v314: 0.25}` — non-zero (anchors do
  overlap) but uniformly so between plateau and
  control
* `triple_max_extra_per_corpus`:
  `{v23: 0, v314: 0}` — triples never add anything
  beyond the best pair union

Within each individual corpus, plateau anchors are
either coverage-equivalent (multiple anchors hit the
same leakage subset) or empty-equivalent (anchor
captures no leakage in this corpus at r=3.5). No
pair satisfies the v3.50 proper-set-independence
definition of resonance in any per-corpus analysis.

The v3.50 `resonant_pair_count = 64` was a property
of mixing v23 + v314 + v315 + v316 plateau anchors
into one 20-element manifold. The phenomenon is NOT
a per-corpus property of plateau anchors; it emerges
from the cross-corpus aggregate.

### 3. Anti-anchor suppression is universal (v3.55)

* `anti_anchor_transfer_rate` = 1.00
* Per-corpus `suppression_per_corpus`: all 1.00 (every
  leakage zeroed in every corpus)
* Per-corpus `recall_per_corpus`: all 1.00 (every
  plateau preserved in every corpus)
* Per-corpus `repulsion_per_corpus`: `{v23: 12,
  v314: 30, v315: 24, v316: 24}` (every baseline
  leakage trajectory repelled)

Five leakage anti-anchors at suppression radius 2.5
zero leakage and preserve full plateau recall in
every reference corpus independently. The v3.51
mechanism is a local, per-corpus property of the
leakage manifold — no cross-corpus mixing is needed.

### 4. Phase transition transfers in every eligible corpus (v3.56)

* `phase_transfer_rate` = 1.00
* `eligible_corpora` = (v23, v314); v315/v316 again
  ineligible (single anchor → flat curve by
  construction)
* Per-corpus `discontinuity_per_corpus`:
  `{v23: 1.00, v314: 1.00}` — discrete tipping in
  both
* Per-corpus `saturation_per_corpus`:
  `{v23: 2, v314: 2}` — same saturation k
* Per-corpus `coupling_strength_per_corpus`:
  `{v23: 0.556, v314: 0.333}` — positive
  subadditivity

Both eligible corpora exhibit discrete phase
transitions with saturation at exactly k=2 anchors —
matching the v3.52 saturation point. The discrete-
tipping behaviour is a per-corpus structural
property.

## Why this is NO-GO, not partial-GO

The directive's gate uses "Wenn EINES scheitert"
(AND across all five gates). gate #2 fails because
the v3.50 pair-resonance was a cross-corpus
aggregation effect, not a per-corpus property of the
plateau manifold. The other three field-coupling
gates (radius, anti-anchor, phase) all transfer
cleanly, but they alone are insufficient to write a
paper about "Semantic Coupling" — because the
defining v3.50 phenomenon (resonant pairs) is the
one that fails.

The honest reading: DESi sees corpus-invariant
geometric structure (radius, anti-anchor, phase) but
the higher-order pair-resonance interpretation
in v3.50 was a v3-aggregate artifact.

## What the next sprint may explore (out of scope
for this document)

1. **Per-corpus anchor enrichment.** v315 and v316
   each carry only 1 plateau anchor, making them
   ineligible for v3.54 / v3.56 pair- and phase-
   tests. A future enrichment sprint could probe
   whether the small-anchor corpora actually contain
   plateau-like trajectories that the v3.31
   classifier missed.
2. **Cross-corpus aggregate as deliberate construction.**
   The v3.50 resonance is real in the aggregate; the
   paper could be reframed as "what does mixing
   plateau anchors across corpora reveal?" rather
   than "is plateau coupling universal?".
3. **Within-corpus pair structure at smaller radii.**
   The probe radius 3.5 produced uniform
   plateau-anchor coverage per corpus. A finer
   per-corpus radius sweep might surface within-
   corpus pair structure.

## Stop rules not triggered (and one that was)

* v3.53 `radius_transfer_rate` (1.00) PASS.
* v3.54 `pair_transfer_rate` (0.00) **FAIL** —
  semantic-coupling resonance is corpus-local. The
  sprint did not halt mid-sprint (no stop rule was
  defined for v3.54); the result is documented and
  the chain continued through v3.55 / v3.56 per the
  directive's "Wenn eines scheitert: ...
  Dokumentieren, aber weitermachen."
* v3.55 `anti_anchor_transfer_rate` (1.00) PASS.
* v3.56 `phase_transfer_rate` (1.00) PASS.
* All four sprints' replay_stability = 1.00.
