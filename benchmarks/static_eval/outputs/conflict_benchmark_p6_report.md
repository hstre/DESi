# Conflict benchmark: P5 (no predicate typing) vs P6 (predicate typing)

- pairs: **36**

| metric | P5 | P6 |
| --- | --- | --- |
| exact-match | 25/36 | 33/36 |
| contradiction precision | 1.00 | 1.00 |
| contradiction recall | 0.89 | 1.00 |
| potential precision | 0.36 | 0.80 |
| potential recall | 0.67 | 0.67 |
| multi-valued FP rate | 6/6 | 1/6 |
| temporal correct | 2/4 | 4/4 |

## P6 per category (expected → detected)

| category | n | exact | detected breakdown |
| --- | --- | --- | --- |
| negation | 5 | 5/5 | `{'contradiction': 5}` |
| numeric | 5 | 5/5 | `{'contradiction': 5}` |
| temporal | 4 | 4/4 | `{'contradiction': 4}` |
| attribute | 5 | 5/5 | `{'contradiction': 5}` |
| multi_valued | 6 | 5/6 | `{'compatible': 5, 'potential': 1}` |
| paraphrase | 5 | 5/5 | `{'compatible': 5}` |
| uncertain | 6 | 4/6 | `{'potential': 4, 'compatible': 2}` |

## What P6 fixed

- `tmp_03` [temporal] compatible → **contradiction** (now correct; rule temporal_order)
- `tmp_04` [temporal] compatible → **contradiction** (now correct; rule temporal_order)
- `mv_01` [multi_valued] potential → **compatible** (now correct; rule -)
- `mv_02` [multi_valued] potential → **compatible** (now correct; rule -)
- `mv_04` [multi_valued] potential → **compatible** (now correct; rule -)
- `mv_05` [multi_valued] potential → **compatible** (now correct; rule -)
- `mv_06` [multi_valued] potential → **compatible** (now correct; rule -)
- `par_01` [paraphrase] potential → **compatible** (now correct; rule -)

## Remaining mismatches in P6

- `mv_03` [multi_valued] expected **compatible**, got **potential** (diff_object/unknown)
- `unc_04` [uncertain] expected **potential**, got **compatible** (-)
- `unc_06` [uncertain] expected **potential**, got **compatible** (-)

## Governance (mark only)

- claims with conflict-derived risk: **48**
- REJECTED-vs-CONFIRMED flagged: **8 claims**

## Honesty / limits

Predicate typing is keyword-based (no ontology). Multi-valued is inferred from predicate keywords (`has`, `contains`, `described as`, …); a contradiction on a multi-valued predicate would be missed. Temporal handles before/after with a shared reference only. Unit normalisation covers a few cases (celsius, percent). Still heuristic, same-subject only, no world model; labels are a human reading.
