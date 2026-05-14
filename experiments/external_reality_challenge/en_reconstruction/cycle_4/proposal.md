# Cycle 4 — downstream-effect validation of reconstruction candidates

## Stance

Standalone analyser. **No new detectors in `src/desi/`.** No ENI score
fabrication. Uses **only native DES fields** from `des_state.json`:

- `operation_history` (parsed via `parse_des_operation`)
- `claims` (the final claim dict — used for survival check)
- `focus_claim_id` (final focus — used for terminal-anchor check)

## What this measures

For each of the 6 created claims `C004..C009` (the targets of the 6
reconstruction candidates from cycles 1 + 2):

1. **first_focus_after_creation** — earliest loop after creation
   where `source_claim == Cxxx` (DES makes this claim the operand of
   a subsequent operation).
2. **touch_count_after_creation** — number of operations after the
   creation loop where the claim appears as source OR target.
3. **survives_in_final_claims** — boolean: is the claim_id present in
   the upstream `claims` dict at the final state.
4. **is_terminal_focus** — boolean: is the claim_id == upstream
   `focus_claim_id` at the final state.

## Classification

Each candidate is assigned to exactly one of three categories:

```
terminal_anchor   iff is_terminal_focus
                  (regardless of touch count)

productive        iff NOT terminal_anchor
                  AND touch_count_after_creation >= 3
                  AND survives_in_final_claims

dormant           iff NOT terminal_anchor
                  AND (touch_count_after_creation < 3
                       OR NOT survives_in_final_claims)
```

The threshold of 3 touches is the smallest count that distinguishes
"DES kept working on this claim" from "DES touched it once or twice
and moved on". It's a parameter of the analysis, not a DESi-side
constant — recorded explicitly in the report.

## What this cycle does NOT do

- **No ENI scores invented.** The candidates from cycles 1 + 2 are
  structural locations; this cycle adds downstream-effect labels,
  not numerical novelty scores.
- **No new DESi detector.** This is a documentation + analysis cycle.
- **No source change in `src/desi/`.**

## Goal

Move from structural reconstruction (cycles 1 + 2 said "DES extended
the graph here") to downstream-effect validation (cycle 4 says "and
DES kept working on what it created"). If most candidates are
`dormant`, the reconstruction rule is picking up structural-but-
inconsequential events. If most are `productive` or `terminal_anchor`,
the rule is picking up actually-consequential ones.

## Predictions (rough, from inspection of taxonomy report)

Pre-running:
- All 6 created claims appear as `source_claim` in several subsequent
  operations (visible in cycle-3's per-operation table).
- All 9 claims (C001-C009) are present in upstream `claims` dict
  (per `upstream_claim_count: 9` in the translator provenance block).
- `focus_claim_id` is `C009`.

So the most likely classification is:
- C009: `terminal_anchor`
- C004, C005, C006, C007, C008: `productive` (each touched 3+ times)
- Dormants: 0 expected.

If predictions hold, the reconstruction rules pick up
actually-consequential extensions. If any are dormant, that's a
signal the rules may be over-permissive.

## Stop condition

Single-pass analysis. Stop after emitting the report.
