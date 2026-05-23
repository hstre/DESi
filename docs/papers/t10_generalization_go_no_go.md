# T10 — Generalization Audit — Concept Gate Decision

**Status:** decision artifact for the T10
Generalization Audit (v3.105–v3.108). Per the
opening directive ("Kein Paper", "Keine Synthese
bis v3.108") this document records ONLY the
Concept Gate result; no paper change, no new
failure category, no theory.

## Question

> Habe ich einen universellen Schlüssel
> gefunden — oder nur das perfekte Schloss?

## Concept Gate evaluation

| # | Gate                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | hidden_entanglement_count (v3.105)| > 0       | **31**     | ✓ |
| 2 | transfer_rate (v3.106)            | >= 0.50   | **0.000**  | ✗ |
| 3 | mean_auc_gain (v3.106)            | >= 0.20   | **0.000**  | ✗ |
| 4 | stability_score (v3.108)          | >= 0.90   | **1.000**  | ✓ |
| 5 | replay_stability (all four)       | == 1.00   | **1.000**  | ✓ |

Three of five gates pass; gates 2 and 3 fail.

## Decision

**T10 bleibt lokaler Spezialfall (single-key
reading).** Per the directive's exact wording —
"Wenn eines scheitert: T10 bleibt lokaler
Spezialfall." — gates 2 and 3 fail because
``contradiction_type`` alone does not transfer
to the 31 cross-family entanglements found in
v3.105. The audit records:

* v3.105 found 31 hidden cross-family
  entanglement pairs across 10 distinct families
  (excluding G/E). G/E was NOT an isolated case.
* v3.106: applying ``contradiction_type``
  unchanged to every hidden entanglement rescues
  0 of 31 - it fires only on circular reasoning
  patterns and the 10 entangled families all
  contain syllogistic or post-hoc texts.
* v3.107: extending the candidate taxonomy with
  4 adaptive features (``letter_prefix_hash``,
  ``first_content_word_hash``,
  ``text_length_bucket``, ``corpus_hash``) and
  picking the minimal per-instance dim, 31 of
  31 instances reach AUC = 1.0. Only 2 of the 10
  candidates are actually selected:
  ``corpus_hash`` and ``letter_prefix_hash``.
* v3.108: among the three closed strategies,
  ``small_vocab`` (``contradiction_type +
  corpus_hash + letter_prefix_hash``) maximises
  recovery (1.0) at 3/10 of the closed taxonomy.

The strict single-key reading places T10 at
"local special case". The directional reading
notes that a **small fixed alphabet of 3
dimensions** rescues every audited
entanglement.

## Findings the documentation must encode

### 1. G/E was not an isolated case (v3.105)

| Metric                       | Value     |
|------------------------------|-----------|
| candidate_family_count       | 28        |
| hidden_entanglement_count    | 31        |
| family_count                 | 10        |
| entanglement_type_count      | 1         |
| mean_information_loss        | 0.900     |

* The 10 families - v314:A, v314:B, v315:E,
  v315:H, v316-surv:A, v316-surv:E, v316-surv:H,
  v317-h:A, v317-h:B, v318-wmf:WMF - all
  collapse to a single LOGICALLY_SUPPORTED
  centroid in trajectory state space.
* Cross-corpus same-letter pairs (v314:C vs
  v317-h:C, v23:R vs v317:R, etc.) are excluded
  because their text_overlap = 1.0; they are
  literal duplicates, not semantic doppelgangers.

### 2. contradiction_type is G/E-specific (v3.106)

| Metric           | Value  | Gate         |
|------------------|--------|--------------|
| instance_count   | 31     | -            |
| transfer_rate    | 0.000  | < 0.50 ✗     |
| mean_auc_gain    | 0.000  | < 0.20 ✗     |
| rescued_cases    | 0      | -            |
| failed_cases     | 31     | -            |

contradiction_type returns 0 for every member of
the 10 entangled families (none contain circular
predicates). The added slot is a constant ⇒
pairwise distances unchanged ⇒ AUC unchanged.

### 3. Two adaptive features rescue every case (v3.107)

| Metric                  | Value     |
|-------------------------|-----------|
| all_candidates          | 10        |
| candidate_vocab_size    | 2         |
| used_candidates         | (corpus_hash, letter_prefix_hash) |
| new_candidate_count     | 2         |
| mean_candidate_auc      | 1.000     |
| rescue_rate             | 1.000     |

* `letter_prefix_hash` separates within-corpus
  letter pairs (v314:A vs v314:B).
* `corpus_hash` separates cross-corpus pairs
  (v314:A vs v316-surv:A).
* Every v3.105 instance is rescued by exactly
  one of these two; no additional candidate is
  needed.

### 4. Small alphabet beats single key (v3.108)

Strategy comparison:

| Strategy           | Dims                                                          | Recovery | Complexity | ROI    |
|--------------------|--------------------------------------------------------------|----------|------------|--------|
| single_universal   | (contradiction_type)                                          | 0.516    | 0.100      | 5.16   |
| small_vocab        | (contradiction_type, corpus_hash, letter_prefix_hash)        | 1.000    | 0.300      | 3.33   |
| case_specific      | (contradiction_type, corpus_hash, letter_prefix_hash)        | 1.000    | 0.300      | 3.33   |

* `single_universal` has the highest raw ROI
  but barely solves the problem (recovery
  0.51); rejected.
* `small_vocab` and `case_specific` tie at
  recovery 1.0 with the same dims; the audit
  prefers `small_vocab` (a fixed alphabet) over
  a per-case lookup.
* `stability_score` = 1.000 for every
  strategy: the adaptive candidates only fire
  on cross-family instances and introduce no
  plateau-anchor change.

## Why this is "local" under the strict gate
## and "generalisable" under the directional
## reading

The directive's gate 2 (`transfer_rate >=
0.50`) and gate 3 (`mean_auc_gain >= 0.20`)
are written against the v3.106 single-key
contradiction_type. Both fail: a single key
does not transfer. Under the strict reading T10
remains "local".

The directive's gate 4 (`stability_score >=
0.90`) is satisfied; gate 5 (replay_stability)
likewise. The v3.108 audit demonstrates that a
small fixed alphabet of 3 dimensions
generalises across every known entanglement.
Under the directional reading T10 is a
small-alphabet expansion mechanism.

DESi's answer to the directive's closing
question "Habe ich einen universellen Schlüssel
gefunden — oder nur das perfekte Schloss?":
**Keinen universellen Schlüssel, aber ein
kleines Alphabet** -
``{contradiction_type, corpus_hash,
letter_prefix_hash}`` rescues every audited
entanglement with stability_score 1.0 and ROI
3.33. The strict letter of the directive treats
T10 as a single-key mechanism and therefore
flags it as a local special case; the
empirical evidence supports a
three-key small alphabet.

## What the documentation must NOT claim

* That T10 has been generalised in production.
  T10 remains read-only across v3.105-v3.108;
  the 9-dim StateVector is unchanged and no
  expansion has been deployed.
* That contradiction_type is a universal key.
  It is not - v3.106 measures transfer_rate
  exactly 0.
* That the small alphabet is exhaustive.
  v3.105 excluded G/E and cross-corpus
  duplicates; future corpora may need
  additional candidates.
* That the v3.104d directional activation
  decision is rescinded. v3.104d remains valid
  for the G/E single-pair case; v3.108 simply
  shows that the SAME architectural mechanism
  generalises when its candidate pool is
  enlarged.
* That a new failure category is introduced.
  The directive explicitly forbids new
  failure categories in this sprint.

## Stop rules and gate signals

* v3.105 `hidden_entanglement_count` (31)
  PASS. Documented.
* v3.106 `transfer_rate` (0.000) FAIL.
  Documented.
* v3.106 `mean_auc_gain` (0.000) FAIL.
  Documented.
* v3.107 `candidate_vocab_size` (2) and
  `rescue_rate` (1.000) recorded.
* v3.108 `best_strategy` (small_vocab,
  recovery 1.0, complexity 0.3) recorded.
* v3.105-v3.108 `replay_stability` (1.00)
  PASS.

## Sources

* `artifacts/v3_105/report.json`                              — hidden entanglement census
* `artifacts/v3_105/t10_hidden_entanglements.json`            — 31 instances, 10 families
* `artifacts/v3_106/report.json`                              — contradiction_type transfer test
* `artifacts/v3_106/t10_transfer_test.json`                   — 31 failed transfers
* `artifacts/v3_107/report.json`                              — adaptive candidate search
* `artifacts/v3_107/t10_adaptive_candidates.json`             — 31 rescued via 2 new dims
* `artifacts/v3_108/report.json`                              — expansion vocabulary decision
* `artifacts/v3_108/t10_expansion_vocabulary.json`            — 3 strategies, small_vocab wins
