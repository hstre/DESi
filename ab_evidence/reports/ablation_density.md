# Ablation: A/B/C/D/E — DESi slice selection vs governance metadata (density)

Backend status: **REAL** · reps=3 · temperature=0.0 · seed=0. Conditions: A=baseline full chat · B=normal DESi slice · C=wrong-slice (another case) · D=status-stripped (same texts, no governance metadata) · E=budget-matched status-stripped (D's texts padded with inert filler to B's token budget).

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

## Accuracy + degeneration (backend=REAL, mean over 3 reps @ temp 0.0)

| case | condition | recall | ΔR vs A | ΔR vs B | loop_rate | contra | invalid | bad_frame | coh_no_cont |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case6_long_research | A_baseline_full_context | 0.796 | 0.0 | 0.078 | 0.0 | 2.0 | 0.0 | 0.0 | 0.0 |
| case6_long_research | B_normal_desi | 0.718 | -0.078 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case6_long_research | C_wrong_slice | 0.024 | -0.772 | -0.694 | 0.0 | 0.0 | 12.0 | 1.0 | 1.0 |
| case6_long_research | D_status_stripped | 0.49 | -0.306 | -0.228 | 0.667 | 0.0 | 0.0 | 0.0 | 0.0 |
| case6_long_research | E_budget_matched_status_stripped | 0.616 | -0.18 | -0.102 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case7a_padded_30k | A_baseline_full_context | 0.428 | 0.0 | -0.325 | 0.0 | 0.667 | 0.0 | 0.0 | 0.0 |
| case7a_padded_30k | B_normal_desi | 0.753 | 0.325 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case7a_padded_30k | C_wrong_slice | 0.024 | -0.404 | -0.729 | 0.0 | 0.0 | 10.0 | 1.0 | 1.0 |
| case7a_padded_30k | D_status_stripped | 0.471 | 0.043 | -0.282 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case7a_padded_30k | E_budget_matched_status_stripped | 0.612 | 0.184 | -0.141 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case7b_padded_60k | A_baseline_full_context | 0.427 | 0.0 | -0.275 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| case7b_padded_60k | B_normal_desi | 0.702 | 0.275 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case7b_padded_60k | C_wrong_slice | 0.024 | -0.403 | -0.678 | 0.0 | 0.0 | 10.0 | 1.0 | 1.0 |
| case7b_padded_60k | D_status_stripped | 0.494 | 0.067 | -0.208 | 0.667 | 0.0 | 0.0 | 0.0 | 0.0 |
| case7b_padded_60k | E_budget_matched_status_stripped | 0.612 | 0.185 | -0.09 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

### B-centred accuracy deltas (recall(B) − recall(X); positive = B better)

| case | B−A | B−C | B−D | B−E |
| --- | --- | --- | --- | --- |
| case6_long_research | -0.078 | 0.694 | 0.228 | 0.102 |
| case7a_padded_30k | 0.325 | 0.729 | 0.282 | 0.141 |
| case7b_padded_60k | 0.275 | 0.678 | 0.208 | 0.09 |

### Degeneration RATES per condition (mean across cases)

| condition | loop_trap_rate | bad_framing_rate | coh_no_cont_rate | mean_contra_persist | mean_invalid_reuse |
| --- | --- | --- | --- | --- | --- |
| A_baseline_full_context | 0.0 | 0.0 | 0.0 | 1.222 | 0.0 |
| B_normal_desi | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| C_wrong_slice | 0.0 | 1.0 | 1.0 | 0.0 | 10.667 |
| D_status_stripped | 0.778 | 0.0 | 0.0 | 0.0 | 0.0 |
| E_budget_matched_status_stripped | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

_Read conservatively: C≈B ⇒ selection not load-bearing; C collapses ⇒ selection load-bearing; D/E≈B ⇒ metadata likely decorative; **B>E** on conflict / contradiction / degeneration (E controls for tokens) ⇒ governance metadata has evidence; B beats A only at high density ⇒ mainly long-context robustness._

## Statistical health

- Cases in this run: **3** (density). This is a SMALL sample; per-condition differences below a few items are within noise. No significance is claimed — treat results as directional, to be repeated across more cases / seeds / models before any inference.

- The evaluator is paraphrase-blind (content-token Jaccard ≥ 0.25): absolute recalls under-state preservation; only the RELATIVE A/B/C/D comparison is intended.

