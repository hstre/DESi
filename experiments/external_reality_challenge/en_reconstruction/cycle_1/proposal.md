# EN-reconstruction cycle 1 — `hypothesis_builder` produces new claim → EN candidate

## DESi self-diagnosis

DESi cannot derive `eni_novelty` numerically from upstream DES output
(no ENI computation is performed by DES). But upstream DES operations
carry STRUCTURED information that DESi has been throwing away:

- `T5[hypothesis_builder] on C003 -> C006`
- `T6[hypothesis_builder] on C003 -> C008`
- `T6[falsifier] on C002 -> C005`

The `[sub_role]` token tells us what KIND of operation DES performed.
The `-> Cyyy` tells us what new claim it produced. A
`hypothesis_builder` op that emits a fresh target_claim is **the
DES-side analog of "novelty injection"** — DES has actively created
a new claim that did not previously exist in the graph.

Paper 0 §3 / Section "ENI ≠ ENI₀" notes that ENI is a measurement on
top of DES's claim graph dynamics. DESi can't read the dynamics
directly, but it CAN read these structured operations. That gives a
proxy: **operations that DEFINITELY produced novelty have at least
some claim-on-novelty signal.**

## The ONE rule (cycle 1)

```
EN candidate at loop K  iff
    parsed_op[K].sub_role == "hypothesis_builder"
    AND parsed_op[K].target_claim is not None
```

That's it. No threshold, no recovery check, no ENI fabrication.
A candidate is an annotation: "this loop is where DES extended the
claim graph." DESi treats it as a *candidate*, not a confirmed EN.

## What needs to change

1. **`TrajectoryStep`** gains two optional fields: `operator_sub_role`
   and `operator_target`. Default `None`. Hand-authored fixtures
   keep them empty.
2. **Translator** populates them from `parse_des_operation` output.
3. **`diagnostics.py`** gets `reconstruct_en_candidates(trajectory)`
   that returns the list of `(loop_index, operator, target_claim)`
   tuples matching the cycle-1 rule.

DESi's existing detectors are NOT touched. The new function is a
candidate generator, not a classifier.

## Predictions

| Suite | Rule fires |
|---|---|
| n=10 adversarial | 0 (no fixture uses sub-role operators) |
| n=20 generalization | 0 (same) |
| external DES (conservative) | 3 (the three `T5[hypothesis_builder]` and `T6[hypothesis_builder]` ops with `-> Cyyy` targets) |

If prediction holds:
- **FP** on hand-authored suites = 0 (rule doesn't fire at all)
- **FN** vs hand-authored en_events = total existing ENs (the rule
  is sensitive to a different signal; this is by design)
- **External coverage** = 3 candidates on real DES

If FP > 0 or external coverage = 0, the rule needs revision.

## Stop condition

> "Stop after: first real EN candidate appears OR three failed
> reconstruction cycles."

If external coverage > 0 AND FP on hand-authored = 0 → stop.
First real candidate appeared.
