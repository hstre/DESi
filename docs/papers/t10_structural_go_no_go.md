# T10 — Deep Epistemic Feature Discovery — Concept Gate Decision

**Status:** decision artifact for the Deep
Epistemic Feature Discovery sprint
(v3.113–v3.116). Per the opening directive
("Kein Paper", "Keine Synthese bis v3.116") this
document records ONLY the Concept Gate result;
no paper change, no new failure category, no
theory.

## Question

> Kann ich dieselbe Rettung durch echte Struktur
> erreichen — oder waren die Abkürzungen
> unvermeidbar?

## Concept Gate evaluation

| # | Gate                            | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | top_candidate_auc (v3.113)      | >= 0.70   | **0.500** | ✗ |
| 2 | structural_recovery (v3.114)    | >= 0.70   | **0.000** | ✗ |
| 3 | proxy_dependence (v3.114)       | == 0      | **0**     | ✓ |
| 4 | minimal_vocab_size (v3.115)     | <= 3      | **1**     | ✓ |
| 5 | vocab_recovery (v3.115)         | >= 0.90   | **0.000** | ✗ |
| 6 | replay_stability (all four)     | == 1.00   | **1.000** | ✓ |

Three of six gates pass; gates 1, 2, and 5 fail.

## Decision

**T10 bleibt lokaler Spezialfall.** Per the
directive's exact wording — "Wenn eines
scheitert: T10 bleibt lokaler Spezialfall." —
the failure of gates 1, 2, and 5 confirms that
pure structural features cannot replicate the
proxy alphabet's recovery on this corpus. The
audit records:

* v3.113: 12 closed structural candidates
  (inference_depth, premise_fanout, etc.) all
  evaluate to the SAME value across every
  member of the entangled pool. Variance is
  literally zero; AUC sits at chance for every
  candidate.
* v3.114: injecting the top structural
  candidate as a +1 dim adds a constant slot to
  every vector ⇒ pairwise distances unchanged ⇒
  rescue rate 0.
* v3.115: exhaustively searching 298 subsets of
  the 12 structural candidates (sizes 1..3)
  finds no combination that rescues a single
  instance. Constants combine to constants.
* v3.116: comparing canonical_9d (recovery 0,
  proxy 0), proxy_alphabet (recovery 1, proxy
  0.67), and structural_alphabet (recovery 0,
  proxy 0), the only strategy with any recovery
  is the proxy_alphabet - which wins ROI by
  default.

DESi's state-vector representation genuinely
does NOT encode the family identity for these 10
entangled families. The proxies were
unavoidable because the structural information
is not there.

## Findings the documentation must encode

### 1. Every structural candidate is constant on the entangled pool (v3.113)

| Metric                    | Value     | Gate         |
|---------------------------|-----------|--------------|
| candidate_count           | 12        | -            |
| signal_candidate_count    | 0         | -            |
| signal_candidates         | ()        | -            |
| top_candidate             | support_propagation_length | - |
| top_candidate_auc         | 0.500     | < 0.70 ✗     |
| top_candidate_margin      | 0.000     | -            |

All 138 anchors share byte-identical state
sequences (frame=[0,0,5,5,5],
branch=[0,2,2,2,2], support=[0,0,0,0,4],
conf=[0,0,0.25,0.25,1],
novel=[0,2,5,0.25,4]). Every structural feature
derived from this sequence is therefore
constant across the pool.

### 2. A single structural candidate rescues nothing (v3.114)

| Metric                | Value     | Gate         |
|-----------------------|-----------|--------------|
| selected_candidate    | support_propagation_length | - |
| instance_count        | 31        | -            |
| structural_recovery   | 0.000     | < 0.70 ✗     |
| structural_auc        | 0.500     | < 0.70 ✗     |
| structural_purity     | 0.667     | < 0.70 ✗     |
| proxy_dependence      | 0         | == 0 ✓       |

The candidate is honest - zero proxy dependence
- but its constant +1 slot leaves pairwise
distances unchanged.

### 3. No subset of structural candidates works (v3.115)

| Metric                | Value     | Gate         |
|-----------------------|-----------|--------------|
| subset_count          | 298       | (sizes 1..3) |
| best_subset           | (support_propagation_length,) | - |
| minimal_vocab_size    | 1         | <= 3 ✓       |
| vocab_recovery        | 0.000     | < 0.90 ✗     |
| mean_auc              | 0.500     | -            |
| complexity_cost       | 0.083     | -            |

Exhaustively searching every 1-, 2-, and 3-dim
subset confirms: constants combine to constants.

### 4. Proxy alphabet wins by default (v3.116)

| Strategy           | Dims                                                          | Recovery | Complexity | Proxy | ROI    |
|--------------------|---------------------------------------------------------------|----------|------------|-------|--------|
| canonical_9d       | ()                                                            | 0.000    | 0.000      | 0.000 | 0.000  |
| proxy_alphabet     | (contradiction_type, corpus_hash, letter_prefix_hash)         | 1.000    | 0.250      | 0.667 | 1.079  |
| structural_alphabet| (support_propagation_length,)                                 | 0.000    | 0.083      | 0.000 | 0.000  |

* canonical_9d and structural_alphabet tie at
  ROI 0 (no recovery).
* proxy_alphabet wins ROI 1.08 because it is
  the only strategy with any recovery - even
  though 2 of its 3 dims are proxies.
* The selection criterion penalises proxy
  contamination via the denominator; the
  proxy_alphabet still wins because the other
  strategies have a zero numerator.

## Why pure structure cannot replace the proxies

The 10 entangled families collapse onto a
single point in trajectory state space:
they share frame_id sequences, branch_cost
sequences, support_state sequences, confidence
sequences, and novelty sequences. No
structural-temporal feature derived from these
sequences can distinguish them, because every
such feature evaluates to the same value on
every anchor.

The family identity ONLY exists in the
trajectory metadata (corpus prefix, letter
prefix) and in the raw text. The text-derived
candidates (v3.111) recover at 0.065; the
metadata-derived candidates (v3.107) recover
at 1.0 but with proxy contamination
(v3.112). Pure structure recovers at 0.

DESi's answer to the directive's closing
question "Kann ich dieselbe Rettung durch
echte Struktur erreichen — oder waren die
Abkürzungen unvermeidbar?":
**Die Abkürzungen waren unvermeidbar.** The
information that distinguishes the 10
entangled families is not in DESi's state-
vector representation. It is in the metadata,
which the proxy alphabet exploits and which no
structural feature can recover.

The v3.116 PROXY_RETAINED verdict is honest:
the only strategy with any recovery uses
proxies; the only strategies without proxies
have no recovery; canonical_9d (no addition)
matches the structural_alphabet baseline.

## What the documentation must NOT claim

* That T10 has been activated in production.
  T10 remains read-only across v3.113-v3.116;
  the 9-dim StateVector is unchanged.
* That structural features are universally
  useless. They are useless ON THIS PARTICULAR
  10-family collapse because every member
  shares an identical trajectory. In a different
  corpus where families have distinct
  trajectories, structural features would have
  variance.
* That the v3.108 small-vocab decision is
  retracted. The 3-dim alphabet still achieves
  recovery 1.000 against the v3.105
  entanglements; v3.116 simply demonstrates
  that no structural alternative exists in this
  corpus.
* That the proxy alphabet is recommended for
  deployment. v3.116's PROXY_RETAINED verdict
  is descriptive (it wins by default), not
  prescriptive. The v3.112 proxy-contamination
  classification still applies.
* That a new failure category is introduced.
  The directive explicitly forbids new failure
  categories in this sprint.

## Stop rules and gate signals

* v3.113 `top_candidate_auc` (0.500) FAIL.
  Documented.
* v3.114 `structural_recovery` (0.000) FAIL;
  `proxy_dependence` (0) PASS. Documented.
* v3.115 `vocab_recovery` (0.000) FAIL;
  `minimal_vocab_size` (1) PASS. Documented.
* v3.116 verdict PROXY_RETAINED records that
  no proxy-free alternative exists.
* v3.113-v3.116 `replay_stability` (1.00)
  PASS.

## Sources

* `artifacts/v3_113/report.json`                              — structural topology census
* `artifacts/v3_113/t10_structural_topology.json`             — 12 candidates, all zero-variance
* `artifacts/v3_114/report.json`                              — single structural recovery
* `artifacts/v3_114/t10_single_structural_recovery.json`      — 31 instances, 0 rescued
* `artifacts/v3_115/report.json`                              — minimal structural alphabet
* `artifacts/v3_115/t10_structural_vocab.json`                — 298 subsets, all chance
* `artifacts/v3_116/report.json`                              — final redeployment
* `artifacts/v3_116/t10_structural_redeployment.json`         — 3 strategies, proxy wins by default
