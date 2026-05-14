# Cycle 4 evaluation — downstream-effect validation

## Headline result

```
6 reconstructed candidates → 5 productive + 1 terminal_anchor + 0 dormant
```

Every claim created by a cycle-1 or cycle-2 reconstruction candidate
becomes something DES continues to work on for the rest of the
trajectory. **None are dormant.** This is the strongest downstream
validation the current rules support: the structural signals DESi
picks up (hypothesis_builder + target / falsifier + target) are
**predictive of downstream activity**, not noise.

## Per-candidate effect (native-DES fields only)

| Claim | Created @ | Via | First focus | Touches | Survives | Final focus | Class |
|---|---:|---|---:|---:|:---:|:---:|---|
| C004 | 3 | `T6[hypothesis_builder]` | 13 | 4 | ✓ | ✗ | `productive` |
| C005 | 4 | `T6[falsifier]` | 17 | 4 | ✓ | ✗ | `productive` |
| C006 | 7 | `T5[hypothesis_builder]` | 21 | 3 | ✓ | ✗ | `productive` |
| C007 | 8 | `T5[falsifier]` | 24 | 4 | ✓ | ✗ | `productive` |
| C008 | 10 | `T6[hypothesis_builder]` | 28 | 3 | ✓ | ✗ | `productive` |
| C009 | 11 | `T6[falsifier]` | 31 | 4 | ✓ | ✓ | `terminal_anchor` |

Methodology recap:
- **Touch** = post-creation operation where claim appears as source OR target.
- **First focus** = smallest loop > creation where source_claim equals this claim.
- **Survives** = present in upstream `claims` dict at final state.
- **Terminal focus** = equal to upstream `focus_claim_id`.
- **Threshold** PRODUCTIVE_MIN_TOUCHES = 3.

## Observations

### O1 — Every candidate is consequential.

0 dormant out of 6. The reconstruction rules don't fire on noise. On
this trajectory, every claim DES created via the two recognised
sub-roles became something DES kept working on for at least 3 more
operations, and survives to the final graph.

This is the strongest cross-rule validation result we have so far:
the structural signals identified by cycles 1 + 2 correlate with
real downstream DES effort. Causally, of course, the candidates
ARE the events that introduced the claims DES then worked on; the
finding is that DES did not introduce claims via these operations
and then immediately drop them. The claim-introduction events
predict at least ~3 loops of follow-up work each.

### O2 — Long latency between creation and first focus.

| Claim | Created loop | First focus | Gap |
|---|---:|---:|---:|
| C004 | 3 | 13 | 10 |
| C005 | 4 | 17 | 13 |
| C006 | 7 | 21 | 14 |
| C007 | 8 | 24 | 16 |
| C008 | 10 | 28 | 18 |
| C009 | 11 | 31 | 20 |

DES creates claims early (loops 3-11) and consolidates each in
turn during a later phase (loops 13-34). Mean creation-to-focus gap
is ~15 loops. This is informative: if DESi ever measures
"time-to-attention" on real DES output, the realistic range is
double-digit loops, not single-digit. The hand-authored suites
typically have ENs at loop ≤ 5 and recovery at loop ≤ 7; real DES
operates on a different time-scale.

### O3 — Terminal anchor came from a falsifier, not a hypothesis_builder.

C009, the upstream `focus_claim_id` at the final state, was created
via `T6[falsifier]` — the critique-navigation category, not the EN
category. The trajectory ended on a critique-derived claim, not on
a builder-derived claim. Both reconstruction rules are necessary if
DESi wants to see what DES converged on.

This is also a defence of cycle 2's "do NOT merge into EN" directive:
critique-navigation candidates are not weaker than EN candidates in
this dataset — one of them became the final focus. Merging them
would have erased that distinction.

### O4 — Pairing pattern (hypothesis + falsifier on same source).

The 6 candidates come in three pairs, each pair operating on the
same source claim:

| Pair | Source claim | Hypothesis @ | Falsifier @ |
|---|---|---:|---:|
| 1 | C002 | 3 (→C004) | 4 (→C005) |
| 2 | C003 | 7 (→C006) | 8 (→C007) |
| 3 | C003 | 10 (→C008) | 11 (→C009) |

DES emits builder + falsifier on the SAME parent in adjacent loops.
This is a pattern, not a coincidence: each new claim is born with
both a hypothesis and a critique. The trajectory then consolidates
them one at a time.

If DESi ever wants a higher-order reconstruction rule, this pairing
would be the natural cycle-5 candidate: "DES extends a parent claim
in a paired hypothesis/falsifier move". But per the operating
discipline of this loop, that's a future cycle, not this one.

## What this cycle does NOT claim

- It does NOT claim 100% prediction. The sample is one trajectory.
  Generalising "reconstruction candidates are always productive"
  from n=1 would be the same kind of overgeneralisation the
  generalization-loop's final report warned about. The honest
  statement is: on this one upstream DES dump, 6/6 candidates
  were productive or terminal. Replication on more dumps is needed.
- It does NOT claim that productivity is *caused* by being a
  reconstruction candidate. Causally it's the other way: DES
  created these claims, and DES kept working on them. The
  finding is that the reconstruction RULES correctly identify
  *which* operations create such productive nodes.
- It does NOT invent any ENI score. The "touch count" and
  "survives" flags are native DES facts (operation_history,
  claims dict).

## Regression check

| | |
|---|---|
| pytest | **58 / 58** unchanged |
| n=10 adversarial | unchanged |
| n=20 generalization | unchanged |
| external DES (conservative + heuristic) | unchanged |
| Source under `src/desi/` | not touched |

## Stop

One-shot analyser. Done.
