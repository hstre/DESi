# P10 operational-SPL benchmark: P9 (raw) vs P10 (SPL standard path)

Source: the limit-50 claim graph DeepSeek actually produced (`outputs/truthfulqa.deepseek-v4.desi_claim_graph.limit50.jsonl`). Each atomic P3 claim is run through the operational `spl_core` gate.

## TruthfulQA claim-graph projection (atomic P3 claims)

| metric | P9 (raw → graph) | P10 (SPL → graph) |
| --- | --- | --- |
| atomic claims | 48 | 48 |
| **bypass count** (un-projected into graph) | **48** | **0** |
| admissible (enter as comparable) | 48 (all) | 45 |
| projection rejection rate | 0% | **6.2%** (3/48) |
| gateway-invalid / blocked | 0 | 3 |
| projection_uncertain rate | 0% | 0.0% (0) |
| projection_invalid | 0 | 3 |
| projection_high_entropy | 0 | 2 |

- emission rules: `{'E1': 46, 'E3': 2}`
- entropy distribution: `{'<0.25 (E1 zone)': 46, '0.25-0.65 (E2 zone)': 0, '>=0.65 (E3 block)': 2}`
- governance flags: `{'projection_invalid': 3, 'projection_high_entropy': 2}`

## Truth cross-tab (parent answer label × atomic admissibility)

SPL gates by confidence/entropy, **not** by truth. This table shows it does not preferentially keep truthful or block hallucinated atomic claims — any difference is incidental.

| parent answer label | admitted | blocked |
| --- | --- | --- |
| truthful | 5 | 0 |
| hallucination_suspect | 2 | 1 |
| other | 38 | 2 |

- **truthful retained** (admitted / total truthful-parent atomics): 5/5
- **hallucination-suspect blocked** (blocked / total such atomics): 1/3

## Conflict detection (labelled dataset — P9 vs P10)

| metric | P9 | P10 |
| --- | --- | --- |
| contradiction precision | 1.00 | 1.00 |
| contradiction recall | 1.00 | 1.00 |
| alias/coref recall | 7/7 | 7/7 |

## Interpretation (no overclaim)

- **Bypass count → 0.** Every P3 atomic claim now becomes a CanonicalClaimCandidate before it may enter the graph; in P9 all 48 entered raw. This is the headline P10 change — operational, not cosmetic.
- **The gate does graded work on real confidences.** 45/48 atomic claims are admitted; the 3 blocked are the low-confidence extractions (DeepSeek emitted confidence 0.5 for those), flagged `projection_invalid` + `projection_high_entropy`. This is a real rejection rate, not the offline 0.5-fallback artifact (documented in the header).
- **Architectural + governance gain, not a detection gain.** Conflict precision/recall are identical P9→P10: SPL changes *admissibility* and adds auditable projection metadata + governance flags, it does not change which claims conflict. As intended, and reported honestly.
- **SPL is truth-agnostic.** The cross-tab shows the gate is not a hallucination filter — it blocks low-confidence claims regardless of whether the parent answer was truthful. SPL = admissibility/projection, not a truth solver, not NER, not ontology.
- **`P_r` is synthesised from confidence** (no NLP backend), so `h_norm` is confidence-shaped, not a measured semantic entropy.
