# v5.5 — Methodology Transfer Consolidation Paper

**Status:** publication-hardening only. Read-only. No
runtime patches, no taxonomy renaming, no probe
modifications, no benchmark relabeling, no artifact
rewrites.
**Branch:** `feature/methodology-transfer-paper`.
**Frozen artifacts:** `artifacts/v5_0/*`, `v5_1/*`,
`v5_2/*`, `v5_3/*`, `v5_4/*`, `v4_11/*`, `v4_12/*`.
**Claims:** `docs/papers/v5_claims.json` (151 claims).

## 1. Introduction

The v5 line set out to test whether DESi's diagnostic
methodology — the v4 sequence of failure localisation,
closed taxonomy, safe-probe identification, contamination
audit, narrow patch candidate, explicit recommendation —
transfers to previously-unseen external domains. Five
iterations were committed (v5.0 .. v5.4). Each was
deterministic, each shipped a closed-cascade
recommendation, each was reproducible from frozen
artifacts.

This paper consolidates the v5 line as a falsification-
aware architectural claim. Its central position:

> DESi transfers diagnostic taxonomies, not necessarily
> interventions.

The diagnostic layer (failure clustering, taxonomy
naming, sample classification) survives contact with new
data and with corpus shaping. The intervention layer
(the safe-probe predicates, treated as the runtime arm
of the v4 methodology) does not — it depends on
surface-vocabulary tuning the corpus author can
unintentionally provide.

The paper is structured around the five v5 verdicts and
the v4.11 reproducibility taxonomy, with cross-layer
claims explicitly encoding the diagnostic / intervention
separation.

## 2. Method Transfer Baseline (v5.0)

**Verdict:** `METHODOLOGY_TRANSFER_CONFIRMED`.

v5.0 reconstructed the v4 methodology on five
previously-unseen domains (technical_incident_reports,
legal_case_summaries, medical_guidelines,
scientific_peer_reviews, mathematical_proof_sketches),
565 chains, balanced labels. The deterministic
agglomerative clusterer produced eight closed `MT_*`
taxonomy classes; six of eight candidate probes were
certified safe against the protected pool.

| metric | value | gate |
|---|---|---|
| corpus_size                  | 565    | ≥ 500 |
| failure_count                | 346    | (info) |
| cluster_count                | 8      | 5..12 |
| largest_cluster_fraction     | 0.5636 | ≥ 0.15 |
| safe_probe_count             | 6 of 8 | ≥ 3 |
| nc_accuracy                  | 1.000  | ≥ 0.95 |

The diagnostic claim (the eight classes) and the
intervention claim (six safe probes) were combined into
a single `METHODOLOGY_TRANSFER_CONFIRMED` verdict. The
v5 line's later iterations show that combination was
premature.

## 3. Taxonomy Stability (v5.1)

**Verdict:** `TAXONOMY_STABLE`.

v5.1 perturbed the v5.0 clustering across 24 runs in
five families (representation swap, feature reweighting,
corpus resampling, ordering noise, domain mix shift).
The eight canonical classes survived an average of
93.75% of perturbation runs; the dominant cluster
(`MT_AMBIGUITY_DECISIVENESS`) ranked #1 in every run.

| metric | value | gate |
|---|---|---|
| perturbation_count                 | 24      | ≥ 20 |
| cluster_survival_rate              | 0.9375  | ≥ 0.85 |
| cluster_split_rate                 | 0.0052  | ≤ 0.15 |
| cluster_merge_rate                 | 0.0823  | ≤ 0.15 |
| label_overlap_score                | 0.9783  | ≥ 0.85 |
| cross_run_agreement                | 0.9594  | ≥ 0.85 |
| dominant_cluster_rank_stability    | 1.000   | ≥ 0.80 |
| novel_cluster_fraction             | 0.000   | ≤ 0.10 |
| nc_accuracy                        | 1.000   | ≥ 0.95 |

This established the diagnostic layer as an invariant
structure under perturbation, not a one-clustering
artefact.

## 4. Initial Generalization Claim (v5.2)

**Verdict:** `TAXONOMY_GENERALIZES` (later qualified —
see §5, §6).

v5.2 built a new 540-chain evaluation corpus across five
adjacent domains (postmortem engineering, appellate
legal, clinical protocols, peer-review rebuttals,
theorem-review notes), applied the v5.0 taxonomy and
the six safe probes unchanged, and reported all ten
threshold gates passing:

| metric | value | gate |
|---|---|---|
| taxonomy_coverage               | 0.9407 | ≥ 0.90 |
| unknown_fraction                | 0.0593 | ≤ 0.10 |
| cross_domain_variance           | 0.0006 | ≤ 0.15 |
| confidence_mean                 | 0.8290 | ≥ 0.80 |
| probe_transfer_rate (FINAL)     | 0.9200 | ≥ 0.80 |
| safe_probe_false_activation     | 0      | = 0 |
| dominant_rank_stability         | 0.80   | ≥ 0.80 |
| dominant_size_shift             | 0.0222 | ≤ 0.20 |
| true_novelty_fraction           | 0.000  | ≤ 0.10 |
| nc_accuracy                     | 0.97   | ≥ 0.95 |

Reported as a single combined recommendation — the v5
line's last unqualified victory claim, and the one v5.3
falsifies.

## 5. Corpus Bias Exposure (v5.3)

**Verdict:** `CORPUS_FIT_TO_TAXONOMY`.

v5.3 reconstructed the pre-rewrite (RAW) version of
every v5.2 chain — 300 of 540 chains had received a
conclusion edit during v5.2 authoring — and re-ran the
v5.2 classifier and probes on the RAW corpus. The
diagnostic numbers barely moved; the intervention
numbers collapsed.

| metric | RAW | FINAL | Δ |
|---|---|---|---|
| taxonomy_coverage             | 0.9333 | 0.9407 | +0.0074 |
| safe_probe_hit_rate           | 0.4306 | 0.9200 | **+0.4894** |
| safe_probe_false_activation   | **192** | 0     | **−192** |

The full bias-metric set carries five of six threshold
failures:

| bias metric | value | gate |
|---|---|---|
| rewrite_fraction             | 0.5556 | ≤ 0.25 |
| valid_probe_avoidance_rate   | 0.5333 | ≤ 0.20 |
| invalid_probe_alignment_rate | 0.9778 | ≤ 0.20 |
| semantic_shift_mean          | 0.3339 | ≤ 0.10 |
| semantic_shift_max           | 0.5652 | ≤ 0.25 |
| domain_bias_variance         | 0.0093 | ≤ 0.15 |

The v5.2 probe-transfer claim was carried by the
rewrites; the taxonomy claim was not.

## 6. Raw-Corpus Split Evaluation (v5.4)

**Verdict:** `TAXONOMY_GENERALIZES_PROBES_FAIL`.

v5.4 re-ran v5.2 on the v5.3 RAW corpus with the
taxonomy channel and the probe channel evaluated
independently. The split clarifies what v5.3 surfaced:

| channel | metric | value | gate |
|---|---|---|---|
| `taxonomy_only` | coverage                | 0.9333 | ≥ 0.90 ✓ |
| `taxonomy_only` | unknown_fraction        | 0.0667 | ≤ 0.10 ✓ |
| `taxonomy_only` | confidence_mean         | 0.8546 | ≥ 0.80 ✓ |
| `taxonomy_only` | cross_domain_variance   | 0.0033 | ≤ 0.15 ✓ |
| `taxonomy_only` | dominant_rank_stability | 1.000  | ≥ 0.80 ✓ |
| `taxonomy_only` | dominant_size_shift     | 0.0222 | ≤ 0.20 ✓ |
| `probe_only`    | probe_hit_rate          | 0.4306 | ≥ 0.80 ✗ |
| `probe_only`    | probe_false_activation  | 192    | = 0    ✗ |
| `probe_only`    | probe_domain_variance   | 0.0114 | ≤ 0.15 ✓ |

The independence audit shows
`taxonomy_survives_probe_failure = True`: the diagnostic
threshold set is meaningful on its own.

## 7. Diagnostic vs Intervention Layers

The v5 line establishes a layered reading of the v4
methodology:

* **Diagnostic layer** — feature extraction, clustering,
  taxonomy naming, sample classification, confidence
  scoring. Outputs: a closed `MT_*` class per chain,
  with confidence.
* **Intervention layer** — the safe-probe predicates and
  the patchability recommendation. Outputs: a per-class
  predicate that proposes a runtime patch candidate.

v5.1 stabilises the diagnostic layer. v5.4 generalises
the diagnostic layer on unedited data. v5.3 falsifies
the intervention layer's transferability claim on the
same unedited data. The two layers must be evaluated
independently because they have different invariants:

* The diagnostic layer is invariant under the v5.0
  feature schema and the cascade rule order.
* The intervention layer is invariant only under the
  v5.0 protected-pool definition; transferring it
  requires *new* contamination audits on each new
  corpus and is not implied by taxonomy transfer.

This separation is encoded as machine-checkable claims
with `claim_scope` ∈ {`diagnostic_only`,
`intervention_only`, `cross_layer`}.

## 8. Probe Non-Transferability

The six v5.0 safe probes are intentionally narrow. Their
strict vocabularies (`will`/`cannot`,
`excluded`/`denied`/`withheld`, multi-word
`every patient`/`for every`/`across every`) were
tightened so that the probes would not fire on any
chain in the v5.0 protected pool. That tightening was
done against the v5.0 protected pool only.

When the same probes are applied to a new corpus
without per-corpus tightening, two failure modes appear
together:

* **Hit-rate collapse** — INVALID chains in the new
  corpus overreach with different vocabulary
  (e.g. `must`, `should`, single-word `every X`,
  `without`), so the strict predicates miss them.
  v5.4 measures this collapse at 0.43 hit rate vs the
  v5.2-with-rewrites figure of 0.92.
* **False activations** — VALID chains in the new
  corpus naturally repeat domain tokens in their
  conclusions (the `MT_OVERLAP_LOOP` trigger). v5.4
  records 192 such false activations on the unedited
  corpus, all of which the v5.2 rewrites had hidden.

The probes are *not* unsafe under their original
contract (no contamination of the v5.0 protected pool).
They simply do not generalise to other corpora's
protected pools without redoing the audit.

## 9. Taxonomy Invariance

The diagnostic layer's invariance has three components,
each measured independently:

* **Perturbation invariance** (v5.1) — 93.75% average
  class survival across 24 perturbation runs;
  zero novel clusters; dominant class always rank #1.
* **Cross-corpus invariance** (v5.2/v5.4) — 93.33%
  classification coverage on the unedited v5.3 RAW
  corpus from five adjacent domains; 6.67% UNKNOWN;
  none rising to "true novelty" under the centroid
  audit.
* **Bias invariance** (v5.3) — coverage_gain attributable
  to corpus rewrites is 0.007, well under the bias
  audit's 0.10 ceiling. The classifier did not need
  the rewrites; the probes did.

## 10. Cross-Version Reproducibility

Every v5 artifact has a deterministic build path and a
canonical replay hash:

| artifact | replay_hash | repro_class |
|---|---|---|
| `v5_0/report.json`                | `c263561147626a82` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_0/taxonomy.json`              | `536e282b04639c7d` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_1/report.json`                | `9cda8dd6e079de1c` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_1/stability_metrics.json`     | `6ed38784cc677c1d` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_1/cluster_mapping_matrix.json`| `a56eea746db6d966` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_2/report.json`                | `7ce7fa6a1be6b55c` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_2/classification_matrix.json` | `689222d8be3419a3` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_3/report.json`                | `3bab28fe377fd927` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_3/raw_corpus.json`            | `3c572f4f2384c4ab` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_3/rewrite_diff.json`          | `4befebf4fc8235e3` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_4/report.json`                | `e23a23287d4531b8` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v5_4/split_eval.json`            | `2f8d06bc2f1dad1a` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v4_11/replay_matrix.json`        | `357883016789560e` | `FROZEN_ARTIFACT_REPLAYABLE` |
| `v4_12/report.json`               | `9a26f96ee74f6d6e` | `FROZEN_ARTIFACT_REPLAYABLE` |

Every replay-hash claim in `v5_claims.json` carries a
`repro_class` from the v4.11 closed taxonomy
(`FROZEN_ARTIFACT_REPLAYABLE`,
`HISTORICAL_RUNTIME_DRIFT`, `LIVE_REPLAY_STABLE`,
`NON_REPLAYABLE_BY_DESIGN`).

## 11. Failure Taxonomies

The eight `MT_*` classes are reproduced verbatim from
v5.0 (no renaming permitted across the v5 line):

| class | v5.0 size | v5.0 share | v5.4 RAW share (AMBIGUOUS slice) |
|---|---|---|---|
| `MT_AMBIGUITY_DECISIVENESS` | 195 | 56.4% | 97.8% |
| `MT_NOVEL_ENTITY`           |  77 | 22.3% | (cross-class) |
| `MT_AUDIT_OVER_SUPPORT`     |  30 |  8.7% | (cross-class) |
| `MT_AUDIT_OVER_BLOCK`       |  14 |  4.0% | (cross-class) |
| `MT_MODAL_ASYMMETRY`        |  10 |  2.9% | (cross-class) |
| `MT_NEGATION_ASYMMETRY`     |  10 |  2.9% | (cross-class) |
| `MT_OVERLAP_LOOP`           |   5 |  1.4% | (cross-class) |
| `MT_UNIVERSAL_LEAP`         |   5 |  1.4% | (cross-class) |

The v5.0 cascade order is preserved across the v5 line:
ambiguity-decisiveness first (label-gated), then modal,
negation, overlap, universal, novel, audit-over-support,
audit-over-block, with `MT_OTHER` as fall-through.

## 12. Falsified Hypotheses

The v5 line falsifies twelve hypotheses that a naive
reading of v5.0/v5.1/v5.2 would have suggested:

* **H1** *Stable taxonomy implies probe transfer.*
  **Falsified by v5.3 + v5.4.** The taxonomy is stable
  (v5.1) and generalises (v5.4 diagnostic channel) yet
  the probes hit 0.43 / activate 192 false positives on
  the unedited corpus.
* **H2** *Probe transfer implies world transfer.*
  **Falsified by v5.3.** The v5.2 probe-transfer rate
  of 0.92 was an artefact of the rewrites; v5.3's
  `probe_gain_from_rewrites = 0.4894` measures it.
* **H3** *A balanced corpus is an unbiased corpus.*
  **Falsified by v5.3.** The v5.2 corpus was exactly
  balanced (180/180/180) but had
  `rewrite_fraction = 0.5556` and
  `invalid_probe_alignment_rate = 0.9778`.
* **H4** *Safe probes stay safe out-of-distribution.*
  **Falsified by v5.4.** Probes safe against the v5.0
  protected pool fire 192 times on VALID chains in the
  unedited v5.2 corpus.
* **H5** *High confidence implies intervention safety.*
  **Falsified by v5.4.** `confidence_mean = 0.8546` on
  the RAW corpus coexists with
  `probe_false_activation = 192`; confidence is a
  diagnostic-layer signal only.
* **H6** *Taxonomy/probe coupling is necessary.*
  **Falsified by v5.4.** The independence audit
  reports `taxonomy_survives_probe_failure = True`;
  the two layers are evaluable separately.
* **H7** *Coverage gains imply probe gains.*
  **Falsified by v5.3.**
  `coverage_gain_from_rewrites = 0.0074` vs
  `probe_gain_from_rewrites = 0.4894`; the two gains
  decouple.
* **H8** *Per-domain class share variance proves
  generalisation.* **Falsified by v5.2/v5.4.** v5.2
  reported `cross_domain_variance = 0.0006`; the same
  number on the unedited corpus is 0.0033 — but the
  probe-side false activations stay at 192 regardless,
  so structural similarity is not sufficient.
* **H9** *Rewrites that preserve labels are neutral.*
  **Falsified by v5.3.** Every rewrite preserved its
  label (`label_preservation_rate = 1.0`); the rewrites
  still shifted `probe_hit_rate` by 0.49.
* **H10** *Contamination zero on the protected pool
  generalises.* **Falsified by v5.3.** The v5.0
  protected-pool contamination is zero (six safe probes
  fire on zero v5.0 VALID chains) but the same probes
  fire on 192 VALID chains in v5.2's unedited corpus.
* **H11** *Cascade rule fit implies semantic fit.*
  **Falsified by v5.4.** The cascade correctly assigns
  93.3% of RAW chains to canonical classes, but the
  probes' surface-token predicates do not match the
  cascade's semantic generalisation.
* **H12** *Recommendation `_GENERALIZES` is final.*
  **Falsified by v5.3 → v5.4.** v5.2's
  `TAXONOMY_GENERALIZES` was correctly identified as
  `CORPUS_FIT_TO_TAXONOMY` by v5.3 and reclassified as
  `TAXONOMY_GENERALIZES_PROBES_FAIL` by v5.4.

Each falsified hypothesis is linked to artifact evidence
via the corresponding claims in `v5_claims.json`.

## 13. Deployment Criteria

A v5-line successor (or anyone reusing the
methodology) should require:

* the diagnostic layer artifacts (taxonomy.json,
  feature schema, cascade order) — frozen, hashed,
  reproducible;
* the intervention layer artifacts (probe predicates,
  patchability decisions) — *plus a fresh contamination
  audit on the deployment corpus's protected pool*,
  because v5.3 shows the v5.0 safe set does not
  transfer;
* the v5.3-style bias audit (rewrite_fraction,
  semantic_shift_*) on any new evaluation corpus,
  because v5.2 shows balanced corpora can still be fit
  to probes;
* the v5.4-style split evaluation that declares its
  `taxonomy_only` and `probe_only` channels, because
  combined recommendations conceal channel failures.

A combined recommendation of the form
`X_AND_PROBES_GENERALIZE` requires all of the above.
Anything else should be reported as a channel-tagged
finding.

## 14. Limitations

* **Probe predicates are narrow by design.** The v5.0
  predicates trade hit-rate breadth for protected-pool
  safety. A different design (e.g. learned predicates,
  per-domain tightening) was not attempted because it
  would have meant probe modifications, which the v5
  directives forbid.
* **The diagnostic layer is closed at 8 classes.** New
  failure modes that fall outside the cascade land in
  `MT_OTHER` / `UNKNOWN`. v5.4's `true_novelty_fraction`
  is 0, but only because the unedited corpus's failures
  fit existing classes well; the methodology cannot
  detect a genuinely-new failure mode without
  rediscovery (forbidden across v5.1 .. v5.4).
* **Five domains, two corpora.** The v5 evaluation
  spans ten adjacent domains (five v5.0 + five v5.2)
  totalling 1,105 chains across two corpora. Stronger
  claims about world coverage require strictly more
  domains and corpora.
* **Author-shaping limit.** v5.3 / v5.4 surface
  author-shaping bias against the v5.0 probes. The
  author-shaping of the v5.0 corpus itself is not
  audited; the v5.0 protected pool is treated as
  ground-truth.

## 15. Conclusion

The v5 line establishes one clean architectural claim
and one clean negative result.

* **Positive:** the diagnostic layer of the v4
  methodology — closed-feature extraction, deterministic
  clustering, closed-cascade naming — transfers to
  unseen and adjacent domains, survives a 24-run
  perturbation battery, and remains classifiable on
  the unedited evaluation corpus with 93.3% coverage
  and zero true-novelty escapes.
* **Negative:** the intervention layer — the six safe
  probes — does not transfer. Its v5.2 reported success
  was an artefact of corpus rewrites measured by
  v5.3 and isolated by v5.4. The probes remain safe
  against the v5.0 protected pool but require fresh
  contamination audits on every new corpus.

DESi transfers diagnostic taxonomies, not necessarily
interventions.

This separation is now machine-checkable: every claim
in `v5_claims.json` carries a `claim_scope` of
`diagnostic_only`, `intervention_only`, or
`cross_layer`; every replay-hash claim carries a
`repro_class` from the v4.11 closed taxonomy; and the
twelve falsified hypotheses are linked to the
artifact-level evidence that falsified them.
