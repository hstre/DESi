# Cycle 3 evaluation — native-DES operation taxonomy report

## What ran

Documentation-only. No detectors added or changed. A standalone
analysis script `taxonomy.py` classifies every entry of upstream DES
`operation_history` into exactly one of five categories using:

- `parse_des_operation` (added by external-reality fix 2);
- the cycle-1 rule (`sub_role == "hypothesis_builder"` AND `target`);
- the cycle-2 rule (`sub_role == "falsifier"` AND `target`).

Output: `taxonomy_report.md` in this directory.

## Headline numbers (upstream DES, 35 operations)

| Category | Count | % |
|---|---:|---:|
| `reconstructed_EN_candidate` | 3 | 8.6% |
| `reconstructed_critique_navigation_candidate` | 3 | 8.6% |
| `plain_operator_transition` | 29 | 82.9% |
| `unsupported_extension` | 0 | 0.0% |
| `unparsed_operation` | 0 | 0.0% |
| **TOTAL** | **35** | **100.0%** |

## Coverage measurements

| Metric | Value |
|---|---:|
| coverage (reconstructed / total) | **6 / 35 = 17.1%** |
| unparsed rate | **0 / 35 = 0.0%** |
| unsupported rate | **0 / 35 = 0.0%** |
| target-creating completeness | **6 / 6 = 100.0%** |

## Interpretation

### 0% unparsed

External-reality fix 2 (the canonical `parse_des_operation`) handles
every form the upstream produces. None of the 35 strings fell to
`OPERATOR_PARSE_FAILURE`. The translator's old silent-`UNKNOWN`
fallback is fully retired on this corpus.

### 0% unsupported

Every parsed operation either lacks a sub-role (29 cases →
`plain_operator_transition`) or carries one of the two sub-roles the
reconstruction rules already cover. There is **no third sub-role
hiding in upstream DES** that DESi recognises syntactically but has
no rule for. This is a positive finding: the cycle-1 / cycle-2 pair
exhaustively covers the sub-role space the parser sees in this
trajectory.

### 100% target-creating completeness

Of the 6 operations that produce a new `Cyyy` target claim,
**all 6** land in a reconstruction category (3 EN, 3 critique-nav).
None of them slip into `unsupported_extension` or
`plain_operator_transition`. This is the strongest statement the
taxonomy supports: **every structural extension of the DES claim
graph that DESi can see is classified.**

### 17.1% coverage

Of the 35 total operations, only 6 (17.1%) extend the claim graph.
The other 29 (82.9%) are bare `Tn on Cxxx` — operations on existing
claims with no role annotation and no new target. From DESi's
perspective these are operator-level work that should NOT be labelled
as EN or critique-navigation candidates; their `plain_operator_transition`
classification is the correct null assignment.

A reader who interprets 17.1% as a "low" coverage number is reading
it wrong. The taxonomy says: 100% of the operations DESi *should*
classify as structural events ARE classified. The remaining 82.9% are
correctly NOT classified.

### Per-claim creation map

The 6 candidates trace exactly which claims were created via which role:

| Loop | Created claim | Role | Source |
|---:|---|---|---|
| 3 | C004 | hypothesis_builder | C002 |
| 4 | C005 | falsifier | C002 |
| 7 | C006 | hypothesis_builder | C003 |
| 8 | C007 | falsifier | C003 |
| 10 | C008 | hypothesis_builder | C003 |
| 11 | C009 | falsifier | C003 |

Reading: DES started from C001, did some operator-level work, then at
loop 3 forked a hypothesis off C002 (creating C004), at loop 4 spawned
a falsifier of C002 (creating C005), and similarly C003 spawned three
children (C006 hypothesis + C007 falsifier at loops 7-8; C008
hypothesis + C009 falsifier at loops 10-11). After that, no more
structural extensions — the rest of the trajectory operates on those
9 claims (C001 through C009).

This matches the upstream `des_state.json` which reports
`focus_claim_id = "C009"` and `iteration = 32`: DES extended the
claim graph 6 times across the first ~11 iterations, then spent the
remaining ~24 iterations refining the resulting 9 claims.

## Regression check

| Suite | Result |
|---|---|
| pytest | **58 / 58** (no change) |
| n=10 adversarial | spurious-hit total 13, attractor_lock 5, etc. (unchanged) |
| n=20 generalization | spurious-hit total 15, attractor_lock 4, etc. (unchanged) |
| external DES (conservative) | EN=3, CN=3, schema_mismatch=True (unchanged) |
| external DES (heuristic) | EN=3, CN=3, schema_mismatch=False (unchanged) |

No source change in `src/desi/`. No new tests. No behaviour change
anywhere. The taxonomy is a READ-ONLY report.

## What this cycle does not say

- It does NOT say the 6 reconstruction candidates are confirmed ENs
  or confirmed navigation events. They are structural candidates.
  Confirmation would require additional signal that upstream DES does
  not emit (eni_novelty, recovery, post-EN trajectory dynamics).
- It does NOT say the 29 plain_operator_transitions are uninteresting.
  They could matter — for example, the pattern `T8 on Cxxx` appearing
  4 times across the tail could be a signal of consolidation activity.
  But cycle 3 does not classify operator-level patterns; that would be
  a separate detector, deliberately out of scope here.
- It does NOT say DES could not produce a sub-role this taxonomy
  doesn't know about (e.g. `consolidator`, `merger`, `pruner`). Such
  a sub-role would land in `unsupported_extension` and signal that a
  cycle-4-style rule extension is warranted. On THIS trajectory, no
  such sub-role appears.

## Stop

One-shot taxonomy. Done.
