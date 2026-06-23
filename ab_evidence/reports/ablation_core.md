# Ablation: A/B/C/D/E — DESi slice selection vs governance metadata (core)

Backend status: **UNAVAILABLE_in_this_env** · reps=3 · temperature=0.0 · seed=0. Conditions: A=baseline full chat · B=normal DESi slice · C=wrong-slice (another case) · D=status-stripped (same texts, no governance metadata) · E=budget-matched status-stripped (D's texts padded with inert filler to B's token budget).

## Input-side characterisation (deterministic, no model)

`slice_info_recall` = fraction of the case's true ground-truth items actually present in the injected slice. It shows the wrong slice (C) really starves the model of correct information, while B and D carry it; A has the full chat. This describes the **inputs**, not model behaviour.

| case | condition | input_tokens | slice_info_recall | Δtok vs A | Δtok vs B |
| --- | --- | --- | --- | --- | --- |
| case1_architecture | A_baseline_full_context | 653 | None | 0 | -83 |
| case1_architecture | B_normal_desi | 736 | 1.0 | 83 | 0 |
| case1_architecture | C_wrong_slice | 613 | 0.0 | -40 | -123 |
| case1_architecture | D_status_stripped | 444 | 1.0 | -209 | -292 |
| case1_architecture | E_budget_matched_status_stripped | 743 | 1.0 | 90 | 7 |
| case2_research | A_baseline_full_context | 748 | None | 0 | 93 |
| case2_research | B_normal_desi | 655 | 1.0 | -93 | 0 |
| case2_research | C_wrong_slice | 736 | 0.0 | -12 | 81 |
| case2_research | D_status_stripped | 433 | 1.0 | -315 | -222 |
| case2_research | E_budget_matched_status_stripped | 662 | 1.0 | -86 | 7 |
| case3_debugging | A_baseline_full_context | 697 | None | 0 | 83 |
| case3_debugging | B_normal_desi | 614 | 1.0 | -83 | 0 |
| case3_debugging | C_wrong_slice | 656 | 0.0 | -41 | 42 |
| case3_debugging | D_status_stripped | 406 | 1.0 | -291 | -208 |
| case3_debugging | E_budget_matched_status_stripped | 621 | 1.0 | -76 | 7 |
| case4_long_research | A_baseline_full_context | 4263 | None | 0 | 2510 |
| case4_long_research | B_normal_desi | 1753 | 1.0 | -2510 | 0 |
| case4_long_research | C_wrong_slice | 631 | 0.0 | -3632 | -1122 |
| case4_long_research | D_status_stripped | 1125 | 1.0 | -3138 | -628 |
| case4_long_research | E_budget_matched_status_stripped | 1760 | 1.0 | -2503 | 7 |

## Model-dependent metrics: UNAVAILABLE_in_this_env

No `ANTHROPIC_API_KEY` / `OPENROUTER_API_KEY` is set, so accuracy and degeneration are **not** measured and **not** simulated. The conditions, the frozen evaluator and the degeneration metrics are wired and unit-tested; one command + a key reproduces the full table:

```bash
export OPENROUTER_API_KEY=...
python ab_evidence/ablation_run.py
```

### What the deterministic inputs already tell us

- C (wrong-slice) carries `slice_info_recall ≈ 0`: the model is given a structurally valid but content-irrelevant slice. If a real run shows C ≈ B on accuracy, the DESi gain is mostly generic structured-context formatting, not correct slice selection. If C collapses, correct selection matters.

- D (status-stripped) carries the same `slice_info_recall` as B at a similar budget: identical information, no governance typing. If D ≈ B, DESi is mostly selection; if B > D on conflict/decision typing or degeneration, the metadata is doing work.


## Statistical health

- Cases in this run: **4** (core). This is a SMALL sample; per-condition differences below a few items are within noise. No significance is claimed — treat results as directional, to be repeated across more cases / seeds / models before any inference.

- The evaluator is paraphrase-blind (content-token Jaccard ≥ 0.25): absolute recalls under-state preservation; only the RELATIVE A/B/C/D comparison is intended.

