# Cycle 2 — `falsifier + target` → critique-navigation candidate

## Self-diagnosis (from cycle 1's deferred list)

EN-reconstruction cycle 1 left 3 verifiable structural extensions on
the table:

- loop 4: `T6[falsifier] on C002 -> C005`
- loop 8: `T5[falsifier] on C003 -> C007`
- loop 11: `T6[falsifier] on C003 -> C009`

These DO extend the claim graph (each produces a new `Cyyy` target),
but the operator's epistemic *role* is critique, not construction.
Cycle 1's rule deliberately excluded them.

The user's directive for this cycle: classify them as a **separate**
candidate kind — "structural navigation" — and do **not** automatically
merge them with EN candidates. The two categories may correlate, but
they encode different epistemic moves and downstream consumers should
be able to tell them apart.

## The ONE rule

```
critique_navigation_candidate at loop K  iff
    step[K].operator_sub_role == "falsifier"
    AND step[K].operator_target is not None
```

Same shape as cycle 1, different sub-role.

## Implementation outline

- New `CritiqueNavigationCandidate` + `CritiqueNavigationReport`
  dataclasses in `src/desi/diagnostics.py`.
- New `reconstruct_critique_navigation_candidates(trajectory)` function.
- New `critique_navigation: CritiqueNavigationReport` field on
  `DeterministicMetrics`; wired via `compute_all`.
- `report_writer.py` gets a SEPARATE section
  "Reconstructed Critique-Navigation Candidates" (not under EN).
  Clear visual separation from the EN-reconstruction block.

DESi's existing EN-reconstruction is NOT modified. The two reports
are independent.

## Predictions

| Suite | Critique-nav candidates | EN candidates | Overlap |
|---|---:|---:|---:|
| n=10 adversarial | 0 (no sub-roles) | 0 | 0 |
| n=20 generalization | 0 (no sub-roles) | 0 | 0 |
| **external DES (conservative)** | **3** (loops 4, 8, 11) | 3 (loops 3, 7, 10) | **0** (disjoint loops) |
| external DES (heuristic) | 3 (same loops) | 3 (same loops) | 0 |

If overlap is 0 on real DES, the two reports describe DISJOINT
structural events. That's the diagnostic point: hypothesis-building
and falsification are two different DES moves, both worth surfacing,
neither should be conflated with the other.

## Stop condition

> "Stop after one rule."

If the rule fires AND FP = 0 on hand-authored suites AND the report
clearly separates critique-navigation from EN → stop.
