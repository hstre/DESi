# Cycle 1 evaluation — `hypothesis_builder` + target → EN candidate

## Rule applied (exactly one)

```
candidate iff step.operator_sub_role == "hypothesis_builder"
              AND step.operator_target is not None
```

Implemented as `reconstruct_en_candidates()` in `src/desi/diagnostics.py`.
TrajectoryStep gained two optional fields (`operator_sub_role`,
`operator_target`); translator populates them from
`parse_des_operation` output.

## Measurement across all four environments

| Environment | Candidates emitted | Real ENs in input | FP (cand @ non-EN loop) | FN (real EN missed) |
|---|---:|---:|---:|---:|
| n=10 adversarial | 0 | 17 | 0 | 17 (rule doesn't try) |
| n=20 generalization | 0 | 30 | 0 | 30 (rule doesn't try) |
| **external DES (conservative)** | **3** | 0 | n/a (no GT) | n/a |
| external DES (heuristic) | 3 | 8 (synth) | 1 | 1 |

pytest: **49 / 49** (no new tests in this cycle; the next test would
be a regression assertion that hand-authored fixtures emit 0
candidates — easy to add later).

## The three candidates on real DES

| Loop | Upstream raw | source → target | Rule note |
|---:|---|---|---|
| 3 | `T6[hypothesis_builder] on C002 -> C004` | C002 → C004 | hypothesis_builder op T6 extended the claim graph |
| 7 | `T5[hypothesis_builder] on C003 -> C006` | C003 → C006 | hypothesis_builder op T5 extended the claim graph |
| 10 | `T6[hypothesis_builder] on C003 -> C008` | C003 → C008 | hypothesis_builder op T6 extended the claim graph |

Each one is verifiable: scan upstream `operation_history[3]`,
`[7]`, `[10]` — these are exactly the three `[hypothesis_builder]`
operations with a `-> Cyyy` target. Three real structural events,
three candidates. No fabrication. No ENI value is asserted — the
rule emits LOCATIONS, not measurements.

## Interpretation

### FP on hand-authored suites = 0

The rule fires only when an operator carries `hypothesis_builder`
sub-role. Hand-authored fixtures (n=10 + n=20) use bare `Tn`
operators with no sub-role. So `operator_sub_role` is None on every
step → rule never fires. **Zero false positives on the 30
hand-authored fixtures across both pre-existing suites.**

### FN on hand-authored suites = 47

Across the 30 hand-authored fixtures the rule misses 47 of the
47 pre-existing en_events. This is **by design**: the rule
addresses a different signal than the one those fixtures encode.
Hand-authored ENs come with explicit `eni_novelty` values; the
rule does not (and could not) reconstruct those numerically from
operation_history. The two signals are complementary, not
substitutes.

A reasonable framing: the rule is a **reconstruction** of ENs that
DES did not emit. On hand-authored data where ENs ARE emitted, the
rule has nothing new to contribute — DESi should still use the
explicit en_events.

### First real EN candidate appears ✓

The user's stop condition is met. On the held-out external DES
trajectory, three structurally-verifiable EN candidates were
reconstructed from operation_history alone. They correspond to
DES's three `[hypothesis_builder]` operations that created new
child claims (C004, C006, C008).

## What the rule does NOT capture (deferred, not failed)

Three observable structural events in the upstream trajectory are
NOT yet candidates under rule 1:

- `T6[falsifier] on C002 -> C005` at loop 4 (created C005 via critique)
- `T5[falsifier] on C003 -> C007` at loop 8 (created C007 via critique)
- `T6[falsifier] on C003 -> C009` at loop 11 (created C009 via critique)

Falsifier operations also extend the claim graph but represent a
different epistemic move (critique-driven creation rather than
construction-driven). A future cycle 2 could broaden rule 1 to
include `falsifier`, but per the user's "one rule per cycle" and
"stop after first real candidate" directives, **this cycle stops
here**.

## Verdict

**ACCEPTED.** First real EN candidate appeared on the held-out
external DES trajectory. Zero FP on the two hand-authored suites.
The reconstruction is structurally verifiable against the upstream
`operation_history`. DESi can now infer at least *some* meaningful
EN locations from native DES operations alone — though only the
`hypothesis_builder` kind, and only when the operation carries the
sub-role notation.

The verdict is a lower bound: DESi can extract SOME signal from
native DES output, not the FULL paper-7 ENI signal. That harder
goal would require either DES-side ENI measurement (not in DESi's
scope) or further reconstruction rules (deferred to future cycles).
