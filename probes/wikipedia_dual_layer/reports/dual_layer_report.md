# DESi Wikipedia Dual-Layer Retrieval Probe — report

Two layers over the SAME frozen 10 Featured Articles (seed 20260528, same cache, no new picks): a COLD narrative layer (full prose, archived) and an ACTIVE DESi state layer (compact epistemic map; each claim / conflict / branch / uncertainty unit carries a narrative anchor = section + char offsets + a short lexical locator). Question: can the compact active layer reliably NAVIGATE back to the relevant prose? No embeddings, no retrieval engine — deterministic anchors + replayable offsets only. No DESi-core change.

- Replay hash `0228dda1a8b717b5…`, stable across two builds: **True**.

## Single-layer (replace prose) vs dual-layer (navigate prose)

| article | type | compress | single-layer recover | dual anchor_precision | dual anchor_recover | cold_access |
| --- | --- | --- | --- | --- | --- | --- |
| Actions along the Matani | history | 0.9366 | 0.265 | 0.9 | 0.169 | 0.812 |
| Canada | politics | 0.932 | 0.221 | 0.899 | 0.167 | 0.815 |
| Curlew sandpiper | science | 0.8642 | 0.638 | 0.961 | 0.645 | 0.329 |
| Grey Cup | history | 0.9222 | 0.346 | 0.885 | 0.186 | 0.789 |
| Hellraiser: Judgment | history | 0.9068 | 0.438 | 0.936 | 0.244 | 0.739 |
| Henry I of England | history | 0.8725 | 0.392 | 0.957 | 0.293 | 0.694 |
| Hughie Ferguson | history | 0.93 | 0.337 | 0.943 | 0.174 | 0.816 |
| Islands: Non-Places | history | 0.775 | 0.791 | 0.969 | 0.816 | 0.158 |
| Kids See Ghosts (album) | history | 0.9272 | 0.288 | 0.636 | 0.121 | 0.809 |
| North Ronaldsay sheep | history | 0.8254 | 0.684 | 0.912 | 0.525 | 0.424 |

- Means: compression **0.889**, anchor_precision **0.9** (offset integrity 1.0), anchor_recoverability **0.334**, cold_access_rate **0.638**.
- Single-layer mean recoverability was ~0.44 (entity-anchor coverage, prose gone). The dual layer changes the question: the prose is NOT gone (it is in cold), and the metric is whether the compact map points back correctly.

## Per-article dual-layer detail

| article | raw_tok | state_tok | anchors | branch_surv | conflict_surv | uncert_surv | n_units (active) | cold_access |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Actions along the Matani | 4699 | 298 | 30 | 1.0 | 1.0 | 0.75 | 160 (30) | 0.812 |
| Canada | 10662 | 725 | 69 | 0.875 | 0.889 | 0.929 | 372 (69) | 0.815 |
| Curlew sandpiper | 3933 | 534 | 51 | 1.0 | 0.833 | 0.95 | 76 (51) | 0.329 |
| Grey Cup | 7059 | 549 | 52 | 1.0 | 0.9 | 0.8 | 247 (52) | 0.789 |
| Hellraiser: Judgment | 5279 | 492 | 47 | 1.0 | 0.889 | 1.0 | 180 (47) | 0.739 |
| Henry I of England | 9788 | 1248 | 116 | 0.846 | 0.957 | 1.0 | 379 (116) | 0.694 |
| Hughie Ferguson | 5160 | 361 | 35 | 1.0 | 1.0 | 1.0 | 190 (35) | 0.816 |
| Islands: Non-Places | 1449 | 326 | 32 | 1.0 | 1.0 | 1.0 | 38 (32) | 0.158 |
| Kids See Ghosts (album) | 4669 | 340 | 33 | 1.0 | 1.0 | 0.833 | 173 (33) | 0.809 |
| North Ronaldsay sheep | 2027 | 354 | 34 | 1.0 | 1.0 | 1.0 | 59 (34) | 0.424 |

## Cold-storage dependency

- `cold_access_rate` = epistemic units with NO active anchor (claims beyond the 25-claim budget) ÷ total units — i.e. units that force a brute cold SCAN rather than a targeted anchored jump. Mean **0.638**.
- ALL marker units (branch / conflict / uncertainty) are kept active and anchored, so they are navigable by a targeted jump; reading their CONTENT always touches cold (that is the dual-layer design: prose archived, not active).

## New research questions (measured)

1. **Navigate with little active memory?** Active state is ~0.889 smaller than prose, yet anchors resolve correctly 0.9 of the time (offset integrity 1.0); navigation works for the units the map holds.
2. **Conflicts addressable?** conflict_survival mean 0.947 — kept active and resolvable back to the source span (addressability ≠ nuance; nuance is in cold).
3. **Alternative narratives reconstructable?** Only as POINTERS — branch_survival 0.972: the anchor returns to the branch sentence, but the competing content must be READ from cold (not reconstructed from the active map).
4. **Branches led back correctly?** Via offsets, integrity 1.0; via the compact locator, precision 0.9 (collisions on near-duplicate sentences are the failure mode — see failures report).
5. **Implicit context still lost?** From ACTIVE memory yes (no prose held); but it is recoverable by following the anchor into cold — the dual layer converts 'lost' into 'archived + addressable'.
6. **Which operations require cold?** Structural/navigational (count, locate, list entities, jump-to-source) run on active; any CONTENT read (what it says, the argument, the resolution) requires cold. Cold-scan fallback rate 0.638.

## Interpretation (per the rule)

- Success here is NOT 'DESi replaces Wikipedia'. It is: **the compact active layer can function as an epistemic navigation index over archived prose.** On this evidence it does for the units it holds (precision 0.9, offset integrity 1.0), with a 0.638 cold-scan fallback for claims beyond budget. The prose stays archived in cold; DESi manages only the active epistemic state and the pointers back.

## No overclaiming

- Measures epistemic-navigation over archived prose only. NOT understanding, NOT knowledge-graph replacement, NOT memory. Anchors are lexical/offset, not semantic.

## Core invariance
- Peripheral; imports `desi.core.replay_kernel` + the previous probe READ-ONLY; adds only new files; DESi core byte-identical.
