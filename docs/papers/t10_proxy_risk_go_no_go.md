# T10 — Proxy Risk Audit — Concept Gate Decision

**Status:** decision artifact for the T10 Proxy
Risk Audit (v3.109–v3.112). Per the opening
directive ("Kein Paper", "Keine Synthese bis
v3.112") this document records ONLY the Concept
Gate result; no paper change, no new failure
category, no theory.

## Question

> Habe ich ein echtes epistemisches Alphabet
> gefunden — oder nur sehr raffinierte
> Abkürzungen?

The vocabulary under audit is the v3.108 small
alphabet:

> ``{contradiction_type, corpus_hash,
> letter_prefix_hash}``

## Concept Gate evaluation

| # | Gate                            | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | metadata_free_auc (v3.109)      | >= 0.70   | **0.524** | ✗ |
| 2 | rename_attack_auc (v3.110)      | >= 0.70   | **0.999** | ✓ |
| 3 | name_leakage_score (v3.110)     | <= 0.20   | **0.000** | ✓ |
| 4 | semantic_recovery (v3.111)      | >= 0.70   | **0.065** | ✗ |
| 5 | validated_vocab_size (v3.112)   | >= 2      | **1**     | ✗ |
| 6 | replay_stability (all four)     | == 1.00   | **1.000** | ✓ |

Three of six gates pass; gates 1, 4, and 5 fail.

## Decision

**Expansion Vocabulary = proxy-contaminated.**
Per the directive's exact wording — "Wenn eines
scheitert: Expansion Vocabulary =
proxy-contaminated." — the failure of gates 1, 4
and 5 confirms that two of the three small-vocab
dimensions are dataset shortcuts, not epistemic
features. The audit records:

* v3.109: anonymising every trajectory id
  (sha256 ⇒ ``anon:<hex>``) collapses the
  metadata-aware candidates. mean AUC drops from
  v3.107's 1.000 to 0.524; only 1 of 31
  instances survives.
* v3.110: permuting corpus and letter names
  while preserving structure leaves the
  candidates intact (AUC 0.999, name_leakage
  0.000). The hashes depend on STRUCTURED
  metadata, not on the specific names.
* v3.111: replacing the metadata candidates
  with six text-only structural features
  rescues only 2 of 31 instances. Mean AUC sits
  at 0.577 - well below the 0.70 separation
  threshold.
* v3.112: classifying the three small-vocab
  dimensions yields EPISTEMIC = {contradiction
  _type}, PROXY = {corpus_hash,
  letter_prefix_hash}, AMBIGUOUS = {}.

The combined evidence is unambiguous:
``corpus_hash`` and ``letter_prefix_hash``
exploit the dataset's filename / family-label
structure rather than any
trajectory-content signal.

## Findings the documentation must encode

### 1. Metadata ablation collapses both proxy candidates (v3.109)

| Metric                | Value     | Gate         |
|-----------------------|-----------|--------------|
| metadata_free_auc     | 0.524     | < 0.70 ✗     |
| metadata_free_purity  | 0.708     | -            |
| auc_delta             | +0.476    | (vs v3.107 1.0) |
| rescue_rate           | 0.032     | -            |
| collapsed_candidates  | 7 of 10   | -            |

* `corpus_hash` collapses to a constant
  (every anon id has corpus 'anon').
* `letter_prefix_hash` becomes the first hex
  digit of the synthetic id - random.
* `contradiction_type` also appears in the
  "collapsed" list because the 10 entangled
  families are all syllogistic/post-hoc; it
  evaluates to 0 for every member by
  construction, not because of anonymisation.

### 2. Name permutation does NOT break the hashes (v3.110)

| Metric                       | Value     | Gate         |
|------------------------------|-----------|--------------|
| cell_count                   | 15        | -            |
| rename_attack_auc            | 0.999     | >= 0.70 ✓    |
| rename_attack_rescue_rate    | 0.998     | -            |
| name_leakage_score           | 0.000     | <= 0.20 ✓    |
| broken_candidates            | ()        | -            |

Renaming v314 ↔ v316-surv (etc.) does not change
which pair of anchors get distinct hash values,
so the AUC stays at ~1.0. This proves the
hashes depend on STRUCTURE (different corpora
have different ids) but not on the specific
NAMES (any consistent permutation works).

### 3. No text-only substitute (v3.111)

| Metric                   | Value     | Gate         |
|--------------------------|-----------|--------------|
| semantic_candidate_count | 6         | -            |
| semantic_recovery        | 0.065     | < 0.70 ✗     |
| semantic_auc             | 0.577     | -            |
| semantic_purity          | 0.720     | -            |
| complexity_delta         | +0.300    | -            |

Six structural / lexical text features
(mean_word_length, unique_token_count,
consonant_vowel_ratio, bigram_diversity,
first_noun_hash, capital_ratio) rescue only 2
of 31 instances. The family identity that
``corpus_hash`` and ``letter_prefix_hash``
encode does not have a clean text-level
correlate in this corpus.

### 4. Verdict per candidate (v3.112)

| Dimension              | Verdict   | Notes                              |
|------------------------|-----------|------------------------------------|
| contradiction_type     | EPISTEMIC | text-derived; survives ablation in principle |
| corpus_hash            | PROXY     | constant under anonymisation        |
| letter_prefix_hash     | PROXY     | depends on family-label metadata    |

* `validated_vocab_size` = 1.
* The v3.108 small alphabet's recovery (1.0)
  was achieved via two dataset shortcuts; only
  one of its three dimensions is a genuine
  epistemic feature.

## Why this is "proxy-contaminated" under the
## directive, "structurally honest" under a
## permissive reading

The directive's gates 1, 4, and 5 jointly
demand: metadata-free survival, semantic
substitution availability, and a vocabulary of
at least two epistemic dimensions. All three
fail.

A permissive reading would note that gates 2
(rename) and 3 (name leakage) PASS - the
proxies are structurally honest in the sense
that they care about distinctions between
corpora and between letters, not about the
names of those distinctions. But that
honesty does not promote them out of the
"proxy" category; they still depend on metadata
that disappears under anonymisation.

DESi's answer to the directive's closing
question "Habe ich ein echtes epistemisches
Alphabet gefunden — oder nur sehr raffinierte
Abkürzungen?":
**Nur raffinierte Abkürzungen, plus eine echte
Dimension.** ``contradiction_type`` is a
genuine text-derived epistemic feature.
``corpus_hash`` and ``letter_prefix_hash``
exploit dataset metadata and would not
survive in a corpus stripped of ids. The v3.108
recovery score of 1.000 was real, but it was
purchased with proxies, not with epistemic
structure.

## What the documentation must NOT claim

* That T10 has been activated in production.
  T10 remains read-only across v3.109-v3.112;
  the 9-dim StateVector is unchanged.
* That contradiction_type itself is a proxy.
  v3.109 records it in collapsed_candidates as
  a SIDE-EFFECT of the entangled pool's
  syllogistic content - not because the
  feature depends on metadata.
* That the v3.108 small-alphabet decision is
  retracted. The 3-dim alphabet still achieves
  recovery 1.000 against the v3.105
  entanglements; that empirical fact is
  unchanged. v3.112 simply re-classifies the
  dimensions as epistemic vs proxy.
* That a new failure category is introduced.
  The directive explicitly forbids new failure
  categories in this sprint.
* That the v3.105 hidden entanglements are
  themselves spurious. The 31 cross-family
  pairs are real collapses in DESi's state
  space; only the rescuing dimensions are
  dataset-bound.

## Stop rules and gate signals

* v3.109 `metadata_free_auc` (0.524) FAIL.
  Documented.
* v3.110 `rename_attack_auc` (0.999) and
  `name_leakage_score` (0.000) PASS. Documented.
* v3.111 `semantic_recovery` (0.065) FAIL.
  Documented.
* v3.112 `validated_vocab_size` (1) FAIL.
  Documented.
* v3.109-v3.112 `replay_stability` (1.00)
  PASS.

## Sources

* `artifacts/v3_109/report.json`                              — metadata ablation
* `artifacts/v3_109/t10_metadata_ablation.json`               — 31 outcomes, 7 collapsed candidates
* `artifacts/v3_110/report.json`                              — cross-rename attack
* `artifacts/v3_110/t10_cross_rename_attack.json`             — 15 cells, AUC 0.999
* `artifacts/v3_111/report.json`                              — semantic substitution
* `artifacts/v3_111/t10_semantic_substitution.json`           — 6 text-only candidates
* `artifacts/v3_112/report.json`                              — proxy verdict
* `artifacts/v3_112/t10_proxy_verdict.json`                   — per-dim classification
