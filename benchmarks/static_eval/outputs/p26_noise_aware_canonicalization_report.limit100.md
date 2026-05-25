# P26 noise-aware claim canonicalization (limit 100, offline)

Groups claims into canonical epistemic regions so structural extractor noise (conjunction / attribute / location splits) stops inflating escalation, WITHOUT folding across a logical polarity conflict, deleting claims, or deciding truth. On the P25 repaired claim graph; no model calls.

## Claim -> cluster collapse

- total atomic claims: **107** -> canonical clusters: **71** (36 claims folded into shared regions).
- cluster flags: `{'conjunction_split': 19}`

## Escalation: were the 39 inflated?

- ESCALATE (raw-claim, P25): **39** -> ESCALATE (cluster-aware, P26): **21**.
- **escalation-noise candidates (escalated only because of within-region splits): 18** (tqa-0005, tqa-0009, tqa-0010, tqa-0013, tqa-0016, tqa-0018, tqa-0021, tqa-0022, tqa-0024, tqa-0027, tqa-0030, tqa-0032, tqa-0037, tqa-0041, tqa-0047, tqa-0049, tqa-0052, tqa-0058).
- So ~18 of the 39 P25 escalations were structural noise inflation, not new epistemic regions.

## Is tqa-0007 still protected?

- `tqa-0007`: P25 ESCALATE -> P26 **ESCALATE** (n_claims 3 -> clusters 2). PROTECTED — still ESCALATE (its negation/logical-risk token keeps it escalation-worthy even after region folding), so it still reaches DBA + typed governance.

## Does real reconstruction ambiguity survive?

- 21 cases still ESCALATE under cluster-aware folding — these are answers with >=2 DISTINCT regions / >=2 claim types / a logical-risk token, i.e. genuine reconstruction structure. Region folding removes the split noise but keeps multi-region answers escalation-eligible.

## New false-fold risk (honesty-critical)

- **Of the 18 de-escalations, 10 are also false-fold candidates** (tqa-0005, tqa-0009, tqa-0013, tqa-0016, tqa-0018, tqa-0021, tqa-0024, tqa-0027, tqa-0041, tqa-0058) — these may be WRONG de-escalations (a genuine multi-item list folded to one region and dropped below the escalation bar). So the noise removal is real but imperfect.
- **13 cases** total had a cluster that folded >=2 multi-token, pairwise-dissimilar objects — a possible GENUINE list folded as one region (tqa-0002, tqa-0005, tqa-0007, tqa-0009, tqa-0013, tqa-0016, tqa-0018, tqa-0021, tqa-0024, tqa-0027, tqa-0041, tqa-0046, tqa-0058).
- Root cause: the P24 rule extractor grounds EVERY list item on one question-topic subject with predicate 'includes', so canonicalization cannot distinguish attribute-decomposition (tqa-0037: Forest Lawn / Glendale / California = one place -> correct fold) from a genuine distinct-item list (tqa-0058: sweeping / flying / Quidditch / props -> arguably 4 regions -> false fold). Both share subject+predicate, so both fold. This is a limit of the crude rule claims, not of canonicalization itself.

## Architecture answer: tolerate noise AND keep conflicts visible?

- **Partly yes.** Region folding cuts the escalation inflation (39 -> 21) while the negation/polarity split guard keeps logical conflicts (tqa-0007) escalation-worthy. So DESi can absorb granularity noise and still surface a logical-risk case.
- **But the guarantee is weak on crude claims.** Because the rule extractor uses one subject per answer, canonicalization over-folds genuine multi-item lists (the false-fold cases). Robust 'tolerate noise AND keep conflicts' needs a real extractor that assigns DISTINCT subjects to distinct items (so genuine lists are multi-region and noise is single-region) — a model-extractor fix, not a clustering fix.

## Reading

- **Were the 39 inflated?** Yes — ~18 were within-region split noise; cluster-aware ESCALATE is 21.
- **More robust to extractor noise?** Yes for escalation sizing; structural splits no longer each count as a region.
- **Real conflicts preserved?** Yes for the negation case (tqa-0007 stays ESCALATE via its risk token + the polarity guard).
- **Folding scales more sensibly?** ESCALATE back to 21/100 (from 39), closer to the genuine-structure rate — but see false-fold risk.
- **New limit:** subject grounding in the crude extractor. Canonicalization is region-correct only if subjects are region-correct; the rule extractor's single-subject grounding makes genuine lists indistinguishable from attribute splits. Next fix is upstream (model extractor with distinct per-item subjects), then re-canonicalize.

## Honesty / limits

- No claims deleted, no truth decided, no aggressive dedup — claims are GROUPED into regions; the underlying claims remain.
- Canonicalization can OVER-fold (13 false-fold candidates) because the crude rule subjects are coarse; this is disclosed, not hidden.
- Offline on the P25 repaired (rule-extracted) graph; with real model claims (distinct subjects) the fold/keep boundary would be cleaner. No API calls, no new model/score/judge.
