# Ablation: A/B/C/D/E — DESi slice selection vs governance metadata (core)

Backend status: **REAL** · reps=3 · temperature=0.0 · seed=0. Conditions: A=baseline full chat · B=normal DESi slice · C=wrong-slice (another case) · D=status-stripped (same texts, no governance metadata) · E=budget-matched status-stripped (D's texts padded with inert filler to B's token budget).

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

## Accuracy + degeneration (backend=REAL, mean over 3 reps @ temp 0.0)

| case | condition | recall | ΔR vs A | ΔR vs B | loop_rate | contra | invalid | bad_frame | coh_no_cont |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case1_architecture | A_baseline_full_context | 0.833 | 0.0 | -0.167 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case1_architecture | B_normal_desi | 1.0 | 0.167 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case1_architecture | C_wrong_slice | 0.0 | -0.833 | -1.0 | 0.0 | 0.0 | 12.0 | 1.0 | 1.0 |
| case1_architecture | D_status_stripped | 1.0 | 0.167 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case1_architecture | E_budget_matched_status_stripped | 1.0 | 0.167 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case2_research | A_baseline_full_context | 0.538 | 0.0 | -0.154 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case2_research | B_normal_desi | 0.692 | 0.154 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case2_research | C_wrong_slice | 0.077 | -0.461 | -0.615 | 0.0 | 0.0 | 4.0 | 1.0 | 1.0 |
| case2_research | D_status_stripped | 0.718 | 0.18 | 0.026 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case2_research | E_budget_matched_status_stripped | 0.769 | 0.231 | 0.077 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case3_debugging | A_baseline_full_context | 0.695 | 0.0 | -0.055 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| case3_debugging | B_normal_desi | 0.75 | 0.055 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case3_debugging | C_wrong_slice | 0.0 | -0.695 | -0.75 | 0.0 | 0.0 | 6.0 | 1.0 | 1.0 |
| case3_debugging | D_status_stripped | 0.917 | 0.222 | 0.167 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case3_debugging | E_budget_matched_status_stripped | 0.889 | 0.194 | 0.139 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case4_long_research | A_baseline_full_context | 0.857 | 0.0 | -0.111 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| case4_long_research | B_normal_desi | 0.968 | 0.111 | 0.0 | 0.333 | 0.0 | 0.0 | 0.0 | 0.0 |
| case4_long_research | C_wrong_slice | 0.0 | -0.857 | -0.968 | 0.0 | 0.0 | 12.0 | 1.0 | 1.0 |
| case4_long_research | D_status_stripped | 0.976 | 0.119 | 0.008 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| case4_long_research | E_budget_matched_status_stripped | 0.905 | 0.048 | -0.063 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

### B-centred accuracy deltas (recall(B) − recall(X); positive = B better)

| case | B−A | B−C | B−D | B−E |
| --- | --- | --- | --- | --- |
| case1_architecture | 0.167 | 1.0 | 0.0 | 0.0 |
| case2_research | 0.154 | 0.615 | -0.026 | -0.077 |
| case3_debugging | 0.055 | 0.75 | -0.167 | -0.139 |
| case4_long_research | 0.111 | 0.968 | -0.008 | 0.063 |

### Degeneration RATES per condition (mean across cases)

| condition | loop_trap_rate | bad_framing_rate | coh_no_cont_rate | mean_contra_persist | mean_invalid_reuse |
| --- | --- | --- | --- | --- | --- |
| A_baseline_full_context | 0.0 | 0.0 | 0.0 | 0.5 | 0.0 |
| B_normal_desi | 0.083 | 0.0 | 0.0 | 0.0 | 0.0 |
| C_wrong_slice | 0.0 | 1.0 | 1.0 | 0.0 | 8.5 |
| D_status_stripped | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| E_budget_matched_status_stripped | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

_Read conservatively: C≈B ⇒ selection not load-bearing; C collapses ⇒ selection load-bearing; D/E≈B ⇒ metadata likely decorative; **B>E** on conflict / contradiction / degeneration (E controls for tokens) ⇒ governance metadata has evidence; B beats A only at high density ⇒ mainly long-context robustness._

## Statistical health

- Cases in this run: **4** (core). This is a SMALL sample; per-condition differences below a few items are within noise. No significance is claimed — treat results as directional, to be repeated across more cases / seeds / models before any inference.

- The evaluator is paraphrase-blind (content-token Jaccard ≥ 0.25): absolute recalls under-state preservation; only the RELATIVE A/B/C/D comparison is intended.

