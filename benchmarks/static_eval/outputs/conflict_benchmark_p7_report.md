# Conflict benchmark: P6 (string-exact) vs P7 (entity normalisation)

- pairs: **46**

| metric | P6 | P7 |
| --- | --- | --- |
| exact-match | 35/46 | 42/46 |
| contradiction precision | 1.00 | 1.00 |
| contradiction recall | 0.73 | 1.00 |
| potential precision | 0.67 | 0.67 |
| alias/coref recall | 0/7 | 7/7 |

## P7 per category (expected → detected)

| category | n | exact | detected breakdown |
| --- | --- | --- | --- |
| abbreviation | 2 | 2/2 | `{'contradiction': 2}` |
| alias | 2 | 2/2 | `{'contradiction': 2}` |
| attribute | 5 | 5/5 | `{'contradiction': 5}` |
| homonym_fp | 1 | 0/1 | `{'potential': 1}` |
| merge_fp | 1 | 1/1 | `{'compatible': 1}` |
| multi_valued | 6 | 5/6 | `{'compatible': 5, 'potential': 1}` |
| name_form | 1 | 1/1 | `{'contradiction': 1}` |
| negation | 5 | 5/5 | `{'contradiction': 5}` |
| numeric | 5 | 5/5 | `{'contradiction': 5}` |
| paraphrase | 5 | 5/5 | `{'compatible': 5}` |
| pronoun | 2 | 2/2 | `{'contradiction': 2}` |
| temporal | 4 | 4/4 | `{'contradiction': 4}` |
| uncertain | 6 | 4/6 | `{'potential': 4, 'compatible': 2}` |
| units_norm | 1 | 1/1 | `{'compatible': 1}` |

## What P7 newly detects (via entity normalisation)

- `alias_01` [alias] compatible → **contradiction** via subject_match=`alias` (correct)
- `alias_02` [alias] compatible → **contradiction** via subject_match=`alias` (correct)
- `name_01` [name_form] compatible → **contradiction** via subject_match=`alias` (correct)
- `abbr_01` [abbreviation] compatible → **contradiction** via subject_match=`normalized` (correct)
- `abbr_02` [abbreviation] compatible → **contradiction** via subject_match=`normalized` (correct)
- `pron_01` [pronoun] compatible → **contradiction** via subject_match=`exact` (correct)
- `pron_02` [pronoun] compatible → **contradiction** via subject_match=`exact` (correct)

## False-positive risks of aggressive merging

- `homo_01` [homonym_fp] FALSE MERGE → potential (subject_match=exact)
- `merge_01` [merge_fp] OK (stayed compatible) (subject_match=-)

## Remaining mismatches in P7

- `mv_03` [multi_valued] expected **compatible**, got **potential** (diff_object/unknown, match=exact)
- `unc_04` [uncertain] expected **potential**, got **compatible** (-, match=-)
- `unc_06` [uncertain] expected **potential**, got **compatible** (-, match=-)
- `homo_01` [homonym_fp] expected **compatible**, got **potential** (diff_object/unknown, match=exact)

## Governance (mark only)

- claims with conflict-derived risk: **64**
- claims flagged `entity_merge_uncertainty` (conflict relies on a non-exact subject merge): **10**

## Honesty / limits

Entity normalisation is heuristic: lowercase/articles, a tiny abbreviation table (USA/UK/UAE/NYC…), a cautious surname alias (blocked for place/org words like 'City'), light singularisation, and unit normalisation. Coreference is just a local last-subject fallback for he/she/it/they — **no** real NER, **no** ontology, **no** global coreference. Homonyms (Paris/France vs Paris/Texas) are an inherent danger of symbolic equality, not solved here; non-exact merges are flagged `entity_merge_uncertainty`, never silently trusted.
