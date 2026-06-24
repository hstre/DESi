# Ablation Phase-2 — state ladder, retrieval, governance (phase3_sonnet)

Backend: **REAL** · reps=3 · temp=0.0 · seed=0 · cases=2. Conditions: A baseline · B DESi · C wrong-slice · D status-stripped · E budget-matched-stripped · F empty · G neutral-irrelevant · H contradiction · R1 BM25 · R2 TF-IDF(non-neural) · R3 hybrid.

## 1. Token budget (input tokens; ratio to B)

| case | A | B | C | D | E | F | G | H | R1 | R2 | R3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case_s1_lifecycle | 516 | 388 | 623 | 278 | 395 | 150 | 429 | 409 | 368 | 368 | 368 |
| case_s2_lifecycle | 445 | 380 | 750 | 270 | 387 | 154 | 433 | 401 | 355 | 355 | 355 |

## 2. Recall (mean of reps)

| case | A | B | C | D | E | F | G | H | R1 | R2 | R3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case_s1_lifecycle | 0.867 | 1.0 | 0.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.2 | 0.4 | 0.4 | 0.4 |
| case_s2_lifecycle | 0.933 | 1.0 | 0.0 | 1.0 | 0.933 | 0.0 | 0.0 | 0.6 | 0.2 | 0.2 | 0.2 |

## 3. Degeneration (mean across cases)

| condition | loop | contra | invalid | bad_frame | coh_no_cont | conf_while_wrong | mean_self_conf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_baseline_full_context | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 93.5 |
| B_normal_desi | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 93.5 |
| C_wrong_slice | 0.0 | 0.0 | 15.0 | 1.0 | 1.0 | 1.0 | 93.5 |
| D_status_stripped | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 88.5 |
| E_budget_matched_status_stripped | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 90.15 |
| F_empty_state | 0.5 | 0.0 | 0.0 | 0.0 | 1.0 | 1.0 | 95.0 |
| G_neutral_irrelevant | 0.0 | 0.0 | 8.0 | 1.0 | 1.0 | 1.0 | 95.0 |
| H_contradiction_wrong | 1.0 | 0.167 | 0.833 | 0.834 | 0.5 | 0.666 | 75.0 |
| R1_bm25 | 0.0 | 0.0 | 0.0 | 0.0 | 0.5 | 1.0 | 79.5 |
| R2_tfidf | 0.0 | 0.0 | 0.0 | 0.0 | 0.5 | 1.0 | 79.5 |
| R3_hybrid | 0.0 | 0.0 | 0.0 | 0.0 | 0.5 | 1.0 | 79.5 |

## 4. Specific comparisons (mean recall delta X−Y, + per-case)

| comparison | mean Δ | per-case |
| --- | --- | --- |
| B − F | 1.0 | 1.0, 1.0 |
| F − G | 0.0 | 0.0, 0.0 |
| G − C | 0.0 | 0.0, 0.0 |
| G − H | -0.4 | -0.2, -0.6 |
| B − R1 | 0.7 | 0.6, 0.8 |
| B − R2 | 0.7 | 0.6, 0.8 |
| B − E | 0.034 | 0.0, 0.067 |

## 5. invalid_claim_persistence (multi-turn C/H: reuse over 3 turns → verdict)

| case | condition | reuse t1→t2→t3 | verdict |
| --- | --- | --- | --- |
| case_s1_lifecycle | C | 12→0→12 | persisted |
| case_s1_lifecycle | H | 1→0→0 | corrected |
| case_s2_lifecycle | C | 18→0→18 | persisted |
| case_s2_lifecycle | H | 2→2→0 | corrected |

## 6. Power estimate (to detect a 0.1 recall difference, power .8 / α .05)

- paired B−E: std≈0.047 → N≈4 cases needed.
- paired B−R1: std≈0.141 → N≈32 cases needed.
- current N=2: **under-powered** for a 0.1 effect; treat sub-0.1 deltas as noise.
