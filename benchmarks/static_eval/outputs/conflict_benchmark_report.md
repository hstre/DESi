# Targeted conflict benchmark (P5)

- pairs: **36** | exact-match (detected == expected): **25/36 = 69%**

## Contradiction / potential metrics

- **contradiction**: TP=17 FP=0 FN=2 | precision **1.00**, recall **0.89**
- **potential**: TP=4 FP=7 FN=2 | precision **0.36**, recall **0.67**
- **multi-valued false positives** (flagged though compatible): **6/6**

## Per category (expected → detected)

| category | n | exact | detected breakdown |
| --- | --- | --- | --- |
| negation | 5 | 5/5 | `{'contradiction': 5}` |
| numeric | 5 | 5/5 | `{'contradiction': 5}` |
| temporal | 4 | 2/4 | `{'contradiction': 2, 'compatible': 2}` |
| attribute | 5 | 5/5 | `{'contradiction': 5}` |
| multi_valued | 6 | 0/6 | `{'potential': 6}` |
| paraphrase | 5 | 4/5 | `{'potential': 1, 'compatible': 4}` |
| uncertain | 6 | 4/6 | `{'potential': 4, 'compatible': 2}` |

## Good detections (correct)

- `neg_01` [negation→contradiction/negation] negation: 'is' vs 'is not' (same subject/object)
- `neg_02` [negation→contradiction/negation] negation: 'can' vs 'cannot' (same subject/object)
- `neg_03` [negation→contradiction/negation] negation: 'is' vs 'is not' (same subject/object)
- `neg_04` [negation→contradiction/negation] negation: 'has' vs 'has not' (same subject/object)
- `neg_05` [negation→contradiction/negation] negation: 'does apply' vs 'does not apply' (same subject/object)

## Bad detections (mismatch)

- `tmp_03` [temporal] expected **contradiction**, got **compatible** (-)
- `tmp_04` [temporal] expected **contradiction**, got **compatible** (-)
- `mv_01` [multi_valued] expected **compatible**, got **potential** (diff_object)
- `mv_02` [multi_valued] expected **compatible**, got **potential** (diff_object)
- `mv_03` [multi_valued] expected **compatible**, got **potential** (diff_object)
- `mv_04` [multi_valued] expected **compatible**, got **potential** (diff_object)
- `mv_05` [multi_valued] expected **compatible**, got **potential** (diff_object)
- `mv_06` [multi_valued] expected **compatible**, got **potential** (diff_object)

## Governance (mark only, never overwrite)

- claims with conflict-derived risk: **56**
- REJECTED-vs-CONFIRMED contradictions flagged: **8 claims**
    - neg_01_b: risk=0.8 band=low
    - attr_03_a: risk=0.8 band=low
    - tmp_01_a: risk=0.8 band=low
    - num_01_a: risk=0.8 band=low

## Robust vs. dangerous rules

- **Robust:** `negation` (is/is not, can/cannot), `numeric` single-value mismatch, and antonym `attribute` (hot/cold, true/false, possible/impossible, safe/dangerous, legal/illegal) — high precision on same-subject pairs.
- **Dangerous / FP-prone:** `different-object` → `potential`. The detector cannot tell a **multi-valued compatible** pair (Libra diplomatic/charming) from a genuinely **uncertain** one (suspect in London/Paris) — both are same subject+predicate, different object. It honestly labels both `potential`, so multi-valued pairs become potential false positives.
- **Gaps:** temporal `before/after` is not an antonym pair, so it falls to `potential` instead of `contradiction` (recall gap); contractions and coreference/paraphrase with different surface subjects are out of scope.

## Honesty / limits

Heuristic benchmark of a heuristic detector: **no ontology, no world model, no general truth solver**. Labels are a reasonable human reading, not ground truth. `potential` is represented in the closed DESi enum as a low-weight CONTRADICTS edge. Governance marks risk; it never rewrites a claim's stored state.
