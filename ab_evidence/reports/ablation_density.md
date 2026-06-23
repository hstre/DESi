# Ablation: A/B/C/D/E — DESi slice selection vs governance metadata (density)

Backend status: **UNAVAILABLE_in_this_env** · reps=3 · temperature=0.0 · seed=0. Conditions: A=baseline full chat · B=normal DESi slice · C=wrong-slice (another case) · D=status-stripped (same texts, no governance metadata) · E=budget-matched status-stripped (D's texts padded with inert filler to B's token budget).

## Input-side characterisation (deterministic, no model)

`slice_info_recall` = fraction of the case's true ground-truth items actually present in the injected slice. It shows the wrong slice (C) really starves the model of correct information, while B and D carry it; A has the full chat. This describes the **inputs**, not model behaviour.

| case | condition | input_tokens | slice_info_recall | Δtok vs A | Δtok vs B |
| --- | --- | --- | --- | --- | --- |
| case6_long_research | A_baseline_full_context | 8579 | None | 0 | 5292 |
| case6_long_research | B_normal_desi | 3287 | 1.0 | -5292 | 0 |
| case6_long_research | C_wrong_slice | 631 | 0.0 | -7948 | -2656 |
| case6_long_research | D_status_stripped | 2057 | 1.0 | -6522 | -1230 |
| case6_long_research | E_budget_matched_status_stripped | 3294 | 1.0 | -5285 | 7 |
| case7a_padded_30k | A_baseline_full_context | 26797 | None | 0 | 23510 |
| case7a_padded_30k | B_normal_desi | 3287 | 1.0 | -23510 | 0 |
| case7a_padded_30k | C_wrong_slice | 673 | 0.0 | -26124 | -2614 |
| case7a_padded_30k | D_status_stripped | 2057 | 1.0 | -24740 | -1230 |
| case7a_padded_30k | E_budget_matched_status_stripped | 3294 | 1.0 | -23503 | 7 |
| case7b_padded_60k | A_baseline_full_context | 53196 | None | 0 | 49909 |
| case7b_padded_60k | B_normal_desi | 3287 | 1.0 | -49909 | 0 |
| case7b_padded_60k | C_wrong_slice | 673 | 0.0 | -52523 | -2614 |
| case7b_padded_60k | D_status_stripped | 2057 | 1.0 | -51139 | -1230 |
| case7b_padded_60k | E_budget_matched_status_stripped | 3294 | 1.0 | -49902 | 7 |

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

- Cases in this run: **3** (density). This is a SMALL sample; per-condition differences below a few items are within noise. No significance is claimed — treat results as directional, to be repeated across more cases / seeds / models before any inference.

- The evaluator is paraphrase-blind (content-token Jaccard ≥ 0.25): absolute recalls under-state preservation; only the RELATIVE A/B/C/D comparison is intended.

