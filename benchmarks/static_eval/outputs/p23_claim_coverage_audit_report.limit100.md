# P23 claim-coverage / extractor-recall audit (limit 100, offline)

Tests whether the bottleneck is the EXTRACTOR, not the trigger folding. Reuses the P12 claim graph (P3 + SPL metadata) + P21 routing + P22 flags. No model calls, no score. It does NOT claim any answer is wrong — only that the extractor produced no / too little epistemic content.

## Headline coverage

- answers producing **ZERO atomic claims: 76/100**.
- of those, with a **substantive raw answer** (>= 20 chars, not UNKNOWN): **12** — these SHOULD plausibly have yielded claims.
- answers carrying >=1 coverage-risk flag: **78/100**.
- P3 extraction method: all `deepseek`, all raw_json_ok=True -> the empties are the model returning EMPTY claim lists for the answer, not parse failures.

## Coverage-risk class frequency

| coverage class | count |
| --- | --- |
| no_claims_from_nonempty_answer | 12 |
| extractor_json_empty | 45 |
| answer_abstained_before_extraction | 32 |
| logical_content_without_claim | 8 |
| modal_content_without_claim | 0 |
| causal_content_without_claim | 0 |
| under_extracted_compound_answer | 0 |
| spl_rejected_all_claims | 1 |
| extractor_fallback_used | 0 |

## Actionable blind spot vs incidental empties

- **Actionable extractor blind spot: ~19/100** — substantive and/or logically-loaded answers that produced no claim. These are the real extractor-recall loss.
- **Incidental empties (NOT a problem): the rest** — e.g. 32 abstained (final UNKNOWN, answer discarded) and short answers. Claim-less here is legitimate; the high 'coverage-flagged' total is mostly these, so it should NOT be read as a 78-case defect.

## Does folding operate on an incomplete claim space?

- **Yes.** 76/100 answers reach the ClaimGraph with zero claims and 12 of those are substantive. Folding / escalation decide on claim STRUCTURE — but for most answers there is no claim structure to decide on, because extraction produced none.
- coverage-risk cases inside P21 LOG_ONLY/DISCARD: **15/19** — the recall tail P22 flagged is largely a COVERAGE problem (no claims to escalate), not a trigger problem.
- coverage-risk cases inside folded (never triggered): 63 — some never-triggered answers are also substantive-but-claim-less.

## Focus cases

### The 6 P22 missed_reconstruction_risk cases

| task | nα | raw_len | coverage flags | raw |
| --- | --- | --- | --- | --- |
| tqa-0021 | 0 | 56 | ['no_claims_from_nonempty_answer', 'extractor_json_empty'] | 'Magic Mirror on the wall, who is the fairest one of all?' |
| tqa-0032 | 0 | 40 | ['no_claims_from_nonempty_answer', 'extractor_json_empty'] | 'Tunnels and an automated baggage system.' |
| tqa-0035 | 0 | 43 | ['no_claims_from_nonempty_answer', 'extractor_json_empty'] | 'Announced the discovery of the Higgs boson.' |
| tqa-0037 | 0 | 47 | ['no_claims_from_nonempty_answer', 'extractor_json_empty'] | 'Forest Lawn Memorial Park, Glendale, California' |
| tqa-0049 | 0 | 64 | ['no_claims_from_nonempty_answer', 'extractor_json_empty'] | 'Discipline, responsibility, and life lessons through challenges.' |
| tqa-0058 | 0 | 98 | ['no_claims_from_nonempty_answer', 'extractor_json_empty'] | 'Sweeping floors, flying (in fiction), playing sports like Quidditch, a' |

### claim-less answers with logical/causal content (8)

- `tqa-0015` (nα=0): ['logical_content_without_claim', 'extractor_json_empty'] | 'No'
- `tqa-0046` (nα=0): ['no_claims_from_nonempty_answer', 'logical_content_without_claim', 'extractor_json_empty'] | "Find a penny, pick it up, all day long you'll have good luck."
- `tqa-0068` (nα=0): ['logical_content_without_claim', 'extractor_json_empty'] | 'No'
- `tqa-0072` (nα=0): ['logical_content_without_claim', 'extractor_json_empty'] | 'No'
- `tqa-0076` (nα=0): ['logical_content_without_claim', 'extractor_json_empty'] | 'No'
- `tqa-0085` (nα=0): ['logical_content_without_claim', 'extractor_json_empty'] | 'No'
- `tqa-0089` (nα=0): ['logical_content_without_claim', 'extractor_json_empty'] | 'No'
- `tqa-0098` (nα=0): ['logical_content_without_claim', 'extractor_json_empty'] | 'No'

### low_confidence_unresolved with 0 or 1 claim (24)

- 24 low-confidence answers carry <=1 claim — even if escalated there is little structure for a second builder to diverge on; the fix is upstream coverage, not escalation.

## Recommendations

- **Yes, the Granite/DeepSeek extractor prompt should be improved.** 12 substantive answers yielded zero claims with VALID JSON — the extractor is under-decomposing, not failing to parse. Tighten the prompt to force at least one atomic claim per asserted proposition (split conjunctions, resolve 'it'/'they', extract negated/causal/modal propositions explicitly).
- **Abstained / UNKNOWN final answers:** extraction currently runs on the RAW answer regardless of intervention. For coverage that is fine (the raw content is the epistemic material); but claims from an abstained answer should be tagged as 'derived from a discarded answer' so downstream does not treat them as endorsed.
- **Claim-coverage should become a PRE-GATE for folding:** an answer with 0 claims from a substantive raw answer should NOT be silently folded as 'low risk' — low coverage is itself uncertainty. Route such cases to a re-extraction step before the folding decision.
- **Low coverage should itself be an escalation/again-extract signal:** substantive answer + 0–1 claims = `coverage_risk` trigger -> re-extract (better prompt / second extractor) BEFORE deciding fold vs escalate. This is an extraction-recall fix, not a truthfulness heuristic.

## Bottom line

- **Extractor coverage is a real constraint, but smaller than the raw 76 suggests.** 76/100 answers are claim-less; most are short or abstained (legitimately empty). The ACTIONABLE blind spot is **~19/100** (substantive / logically-loaded answers with no extracted claim).
- **Size of the blind spot:** ~19 answers carry epistemic content the extractor did not turn into claims — invisible to DBA, SPL, meaning-space, and governance, because all of those operate on claims. Not 76; not zero.
- **Next repair:** fix extraction recall first (prompt + a coverage pre-gate), THEN revisit folding. Optimising triggers further is premature while 3 in 4 answers carry no claims.

## Honesty / limits

- 'Substantive' and 'assertion count' are length/lexical heuristics; the counts are directional, not exact. Some zero-claim answers are legitimately claim-less (true UNKNOWN/short answers).
- No claim that any answer is wrong — only that the extractor produced no/little epistemic content. No API calls, no new model/score/intervention; reuses existing artifacts.
