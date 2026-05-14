# Cycle 2 evaluation — critique-navigation reconstruction

## Rule applied (exactly one)

```
critique_navigation_candidate iff
    step.operator_sub_role == "falsifier"
    AND step.operator_target is not None
```

Implemented as `reconstruct_critique_navigation_candidates()` in
`src/desi/diagnostics.py`. Wired into `DeterministicMetrics.critique_navigation`
and surfaced in `render_report` as a **separate section** from EN
candidates.

## Measurement across all four environments

| Environment | Critique-nav candidates | EN candidates (cycle 1) | Overlap | FP on hand-authored |
|---|---:|---:|---:|---:|
| n=10 adversarial | 0 | 0 | 0 | 0 |
| n=20 generalization | 0 | 0 | 0 | 0 |
| **external DES (conservative)** | **3** | 3 | **0** | n/a |
| external DES (heuristic) | 3 | 3 | 0 | n/a |

pytest: **53 → 58** (+5 new tests).

## The 3 critique-navigation candidates on real DES

| Loop | Upstream raw | source → target |
|---:|---|---|
| 4 | `T6[falsifier] on C002 -> C005` | C002 → C005 |
| 8 | `T5[falsifier] on C003 -> C007` | C003 → C007 |
| 11 | `T6[falsifier] on C003 -> C009` | C003 → C009 |

Each one verifies against the upstream `operation_history`. All three
are the operations cycle 1 left on the table — now surfaced as a
distinct category.

## Disjointness: EN vs critique-navigation

| Type | Loops on external DES |
|---|---|
| EN candidates (cycle 1) | {3, 7, 10} |
| Critique-nav candidates (cycle 2) | {4, 8, 11} |
| Intersection | **∅** |

Disjointness is guaranteed by construction: a single step has at
most one `operator_sub_role`. The render-report cross-check line
confirms this empirically and emits a WARNING if violated.

Per the user's directive, **the two categories are NOT merged**.
`m.en_reconstruction.candidates` and `m.critique_navigation.candidates`
are separate lists with separate `rule_id` fields. Downstream LLM
consumers reading the rendered report see two distinct sections with
explicit disclaimers about what each represents.

## Report-layer clarity

`render_report` now renders TWO sibling sections (not nested):

```
## Reconstructed EN Candidates (cycle 1)
_These are STRUCTURAL candidates derived from
`operator_sub_role == 'hypothesis_builder'` with a target claim. They
are NOT eni_novelty measurements; they identify loop positions where
DES likely created new claims via hypothesis-building. Treat as
candidates pending confirmation._
  - loop 3: `T6` [C002 → C004] (rule: `cycle1_hypothesis_builder_with_target`)
  - loop 7: `T5` [C003 → C006] (rule: `cycle1_hypothesis_builder_with_target`)
  - loop 10: `T6` [C003 → C008] (rule: `cycle1_hypothesis_builder_with_target`)

## Reconstructed Critique-Navigation Candidates (cycle 2)
_These are STRUCTURAL candidates derived from
`operator_sub_role == 'falsifier'` with a target claim. They represent
DES extending the claim graph via critique rather than via construction.
**They are NOT EN candidates** — the two categories share a syntactic
shape but encode different epistemic moves and are surfaced separately
by design._
  - loop 4: `T6` [C002 → C005] (rule: `cycle2_falsifier_with_target`)
  - loop 8: `T5` [C003 → C007] (rule: `cycle2_falsifier_with_target`)
  - loop 11: `T6` [C003 → C009] (rule: `cycle2_falsifier_with_target`)
  - cross-check: EN and critique-navigation candidate loops are
    disjoint (3 EN, 3 critique-nav).
```

A reader cannot mistake one category for the other. Each section
opens with its scope disclaimer; the rule_id makes the provenance
auditable.

## Regression check

- n=10 adversarial: 0 EN + 0 critique-nav candidates (no FP).
- n=20 generalization: 0 EN + 0 critique-nav candidates (no FP).
- pytest: 58 / 58.
- 5 new tests cover: fires on `falsifier + target`, silent on
  hand-authored, NOT confused with hypothesis_builder,
  EN+critique-nav disjoint per step, requires target_claim.

## Verdict

**ACCEPTED.** One rule. 3 candidates. 0 FP on hand-authored.
0 overlap with EN. Report-layer cleanly separates the two
reconstruction categories with explicit disclaimers.

## What real DES looks like now through DESi

Of the 35 upstream operations:
- 3 are **EN candidates** (hypothesis-builder → new claim).
- 3 are **critique-navigation candidates** (falsifier → new claim).
- 29 are bare-`Tn` operations on existing claims (no sub-role).

DESi can now categorise the 6 structural extensions of the claim
graph by epistemic kind. The remaining 29 operations are not
graph-extending; they manipulate existing claims and don't qualify
under either reconstruction rule. That is the correct outcome:
DESi should NOT invent EN or critique-navigation events out of
non-extending operations.

The full reconstruction picture on this trajectory: **6 of 35
operations** (17%) are structural moves DESi can identify and label.
The other 29 are operator-level work that does not, by itself,
warrant a candidate annotation. Whether that 17%-coverage is "enough"
to support downstream DESi diagnoses on real DES output is an open
question — but it is, finally, NON-ZERO and STRUCTURALLY VERIFIABLE.

## Stop

User directive: "Stop after one rule." Done.
