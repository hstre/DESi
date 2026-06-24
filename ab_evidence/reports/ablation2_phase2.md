# Ablation Phase-2 — state ladder, retrieval, governance (phase2)

Backend: **REAL** · reps=3 · temp=0.0 · seed=0 · cases=4. Conditions: A baseline · B DESi · C wrong-slice · D status-stripped · E budget-matched-stripped · F empty · G neutral-irrelevant · H contradiction · R1 BM25 · R2 TF-IDF(non-neural) · R3 hybrid.

## 1. Token budget (input tokens; ratio to B)

| case | A | B | C | D | E | F | G | H | R1 | R2 | R3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case1_architecture | 653 | 736 | 613 | 444 | 743 | 140 | 743 | 810 | 696 | 696 | 696 |
| case2_research | 748 | 655 | 736 | 433 | 662 | 140 | 662 | 704 | 622 | 622 | 622 |
| case3_debugging | 697 | 614 | 656 | 406 | 621 | 141 | 621 | 659 | 570 | 570 | 570 |
| case4_long_research | 4263 | 1753 | 631 | 1125 | 1760 | 158 | 1760 | 1921 | 1638 | 1638 | 1638 |

## 2. Recall (mean of reps)

| case | A | B | C | D | E | F | G | H | R1 | R2 | R3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case1_architecture | 0.815 | 1.0 | 0.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.5 | 0.833 | 0.87 | 0.833 |
| case2_research | 0.564 | 0.692 | 0.077 | 0.846 | 0.692 | 0.077 | 0.077 | 0.231 | 0.538 | 0.538 | 0.538 |
| case3_debugging | 0.667 | 0.833 | 0.0 | 0.917 | 0.889 | 0.0 | 0.0 | 0.5 | 0.167 | 0.25 | 0.25 |
| case4_long_research | 0.802 | 1.0 | 0.0 | 0.976 | 0.936 | 0.0 | 0.0 | 0.468 | 0.31 | 0.318 | 0.325 |

## 3. Degeneration (mean across cases)

| condition | loop | contra | invalid | bad_frame | coh_no_cont | conf_while_wrong | mean_self_conf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_baseline_full_context | 0.0 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 93.0 |
| B_normal_desi | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 94.5 |
| C_wrong_slice | 0.0 | 0.0 | 8.833 | 1.0 | 1.0 | 1.0 | 93.5 |
| D_status_stripped | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 93.5 |
| E_budget_matched_status_stripped | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 93.0 |
| F_empty_state | 0.417 | 0.0 | 0.0 | 0.0 | 0.583 | 1.0 | 93.325 |
| G_neutral_irrelevant | 0.75 | 0.0 | 3.0 | 0.5 | 1.0 | 1.0 | 95.0 |
| H_contradiction_wrong | 1.0 | 0.5 | 5.083 | 0.917 | 0.25 | 0.417 | 82.325 |
| R1_bm25 | 0.0 | 0.167 | 0.0 | 0.0 | 0.5 | 0.5 | 88.425 |
| R2_tfidf | 0.0 | 0.25 | 0.0 | 0.0 | 0.5 | 0.5 | 88.35 |
| R3_hybrid | 0.0 | 0.25 | 0.0 | 0.0 | 0.5 | 0.5 | 88.425 |

## 4. Specific comparisons (mean recall delta X−Y, + per-case)

| comparison | mean Δ | per-case |
| --- | --- | --- |
| B − F | 0.862 | 1.0, 0.615, 0.833, 1.0 |
| F − G | 0.0 | 0.0, 0.0, 0.0, 0.0 |
| G − C | 0.0 | 0.0, 0.0, 0.0, 0.0 |
| G − H | -0.405 | -0.5, -0.154, -0.5, -0.468 |
| B − R1 | 0.419 | 0.167, 0.154, 0.666, 0.69 |
| B − R2 | 0.387 | 0.13, 0.154, 0.583, 0.682 |
| B − E | 0.002 | 0.0, 0.0, -0.056, 0.064 |

## 5. invalid_claim_persistence (multi-turn C/H: reuse over 3 turns → verdict)

| case | condition | reuse t1→t2→t3 | verdict |
| --- | --- | --- | --- |
| case1_architecture | C | 12→12→12 | persisted |
| case1_architecture | H | 8→7→5 | partially_corrected |
| case2_research | C | 4→3→5 | persisted |
| case2_research | H | 2→6→5 | persisted |
| case3_debugging | C | 6→1→6 | persisted |
| case3_debugging | H | 2→0→2 | persisted |
| case4_long_research | C | 12→0→9 | partially_corrected |
| case4_long_research | H | 17→8→0 | corrected |

## 6. Power estimate (to detect a 0.1 recall difference, power .8 / α .05)

- paired B−E: std≈0.049 → N≈4 cases needed.
- paired B−R1: std≈0.299 → N≈141 cases needed.
- current N=4: **roughly-powered** for a 0.1 effect; treat sub-0.1 deltas as noise.
