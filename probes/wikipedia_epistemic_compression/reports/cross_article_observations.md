# DESi Wikipedia Epistemic-Compression Probe — cross-article observations

N = 10 frozen Featured Articles (seed 20260528). Research question: **which epistemic structures survive strong compression?** — not whether DESi compresses Wikipedia perfectly.

## By article type (means)

| type | n | compress | claims | branch | conflict | uncert | cites | recover | loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| history | 8 | 0.889 | 169.125 | 3 | 8 | 11.875 | 293.125 | 0.443 | 0.557 |
| politics | 1 | 0.94 | 370 | 8 | 9 | 27 | 1013 | 0.221 | 0.779 |
| science | 1 | 0.893 | 65 | 2 | 6 | 20 | 151 | 0.638 | 0.362 |

## Expected-vs-observed type differences

- Hypotheses were: technical→stable structure, historical→more conflict/branches, political→narrative drift, biography→many claims/few branches, science→good evidence. With a *random* (non-curated) sample these types may be unevenly represented — read the table as observation, not confirmation. Types present: history×8, politics×1, science×1.
- **Honest negative — the type classifier is unreliable.** It is a fixed keyword heuristic (no embeddings) and it MISLABELS: a film (Hellraiser: Judgment), a footballer biography (Hughie Ferguson), a music album (Kids See Ghosts) and a sheep breed (North Ronaldsay sheep) all fell into `history`, and no article was identified as `biography` or `technical` at all. So the per-type table above is NOT a sound basis for the type hypotheses; embedding-free topical typing of open-world articles failed here, and we do not tune it to fix the labels (that would be retrofitting). The hypotheses remain untested on this sample.

## Failure questions (measured, honest)

1. **Implicit context lost?** YES — the compressed state holds 0 prose tokens; all implicit cross-references and narrative connective tissue are dropped by construction. Only anchors/markers survive.
2. **Alternative narratives collapse?** PARTIALLY — branch *existence* is preserved in all 10 articles (True), but each branch collapses to a cue+anchor fingerprint; the competing content itself is gone. Existence preserved, content collapsed.
3. **Conflicts smoothed?** Existence NOT smoothed (conflict markers kept in full: True); but the conflict's resolution/nuance is lost with the prose.
4. **Uncertainties removed?** NO — uncertainty markers explicitly retained for all articles (True); however the marker is detached from its qualified claim once prose is dropped.
5. **Fact density vs epistemic stability confused?** Risk is real: 1/10 articles have high claim density but low branch count — a flat, 'stable-looking' state that merely reflects low-conflict content, not verified epistemic stability. Claim count must not be read as robustness.
6. **Topic-mixing failure?** The compressed state is a FLAT claim/marker list with no intra-article topic boundaries beyond section labels; highest frame-diversity articles (Grey Cup, Islands: Non-Places, Actions along the Mata) have their distinct sub-topics blended in the flat state. Section frames are retained but claims are not scoped to them.

## Interpretation (per the pre-registered rule)

- Mean compression **0.895**, mean anchor-recoverability **0.44** (mean loss 0.56).
- **Partial success / partial failure, reported honestly:** the *existence* of conflicts, branches and uncertainties survives strong compression in every article (success on the structure-preservation criterion). BUT the *content* of alternative narratives, the implicit context, and the conflict nuance collapse to fingerprints (failure on the narrative-preservation criterion). DESi here preserves an epistemic-structure SKELETON, not the narratives themselves.
- This is the honest boundary the experiment was meant to expose: deterministic, embedding-free extraction can keep WHERE the epistemic action is (markers + anchors) but not WHAT it says (semantics) — exactly where an open-world, semantically dense corpus like Wikipedia exceeds lexical structure analysis.

## No overclaiming

- This does NOT show that DESi 'understands' Wikipedia, replaces knowledge graphs, or builds memory. It measures one thing: deterministic epistemic-structure compression and what it preserves vs loses.

## Honest limits

- Claim/branch/conflict/uncertainty detection is FIXED lexical/structural heuristics (no embeddings, by design) — it misses paraphrastic conflicts and implicit branches and may false-positive on cue words used non-epistemically. Sentence splitting is regex-level. Anchors are proper-noun/number heuristics. The claim budget (K=25) and lexicons were set before the run and NOT tuned to results. Per-section DESi frames are often `frame_undeclared` on encyclopedic prose (the frame layer is built for claims, not narration) — reported as-is, not patched.
